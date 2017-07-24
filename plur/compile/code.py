#!/usr/bin/env python

# Copyright 2017 DIANA-HEP
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import ast
from types import MethodType

from plur.types import *
from plur.thirdparty.meta.decompiler.instructions import make_function

##################################################################### utility functions

def fcn2syntaxtree(fcn):
    def __eq__(self, other):
        if self.__class__ == other.__class__:
            return all(getattr(self, n) == getattr(other, n) for n in self._fields)
        else:
            return False

    def totuple(x):
        if isinstance(x, list):
            return tuple(x)
        else:
            return x

    def __hash__(self):
        return hash((self.__class__,) + tuple(totuple(getattr(self, n)) for n in self._fields))

    def addmethods(x):
        if isinstance(x, ast.AST):
            x.plurtype = None
            x.__eq__ = MethodType(__eq__, x)
            x.__hash__ = MethodType(__hash__, x)
            for fieldname in x._fields:
                addmethods(getattr(x, fieldname))

        elif isinstance(x, list):
            return map(addmethods, x)

        return x

    return addmethods(make_function(fcn.__code__))

def generate(plurtype, format, **subs):
    def recurse(x):
        if isinstance(x, ast.Name) and x.id in subs:
            if not hasattr(subs[x.id], "lineno"):
                subs[x.id].lineno = 1
            if not hasattr(subs[x.id], "col_offset"):
                subs[x.id].col_offset = 0
            return subs[x.id]

        elif isinstance(x, ast.AST):
            for fieldname in x._fields:
                setattr(x, fieldname, recurse(getattr(x, fieldname)))
            return x

        else:
            return x

    out = recurse(ast.parse(format).body[0].value)
    out.plurtype = plurtype
    return out

##################################################################### entry point

def rewrite(fcn, paramtypes, environment={}):
    if callable(fcn) and hasattr(fcn, "__code__"):
        syntaxtree = fcn2syntaxtree(fcn)
    else:
        raise TypeError("propagate takes a Python function as its first argument")

    if isinstance(paramtypes, dict):
        symbols = dict(paramtypes)
    else:
        try:
            iter(paramtypes)
        except TypeError:
            raise TypeError("propagate takes a dict of name -> type or iterable of parameter types as its second argument")
        else:
            symbols = dict((n.id if isinstance(n, ast.Name) else n.arg, t) for n, t in zip(syntaxtree.args.args, paramtypes))

    if hasattr(fcn, "__annotations__"):
        for n, t in fcn.__annotations__:
            if n != "return" and n not in symbols:
                symbols[n] = t

    if not isinstance(environment, dict):
        raise TypeError("propagate takes a Python dict (e.g. vars()) as its third argument")

    ####### ensure that the types have the column information we're going to propagate

    def checktype(tpe):
        # P
        if isinstance(tpe, Primitive):
            if not hasattr(tpe, "data"):
                raise TypeError("type is missing column information (hint: create with columns2type)")
        # L
        elif isinstance(tpe, List):
            if not hasattr(tpe, "offset"):
                raise TypeError("type is missing column information (hint: create with columns2type)")
            checktype(tpe.of)
        # U
        elif isinstance(tpe, Union):
            if not hasattr(tpe, "tag") or not hasattr(tpe, "offset"):
                raise TypeError("type is missing column information (hint: create with columns2type)")
            for t in tpe.of:
                checktype(t)
        # R
        elif isinstance(tpe, Record):
            for fn, ft in tpe.of:
                checktype(ft)

    for t in symbols.values():
        checktype(t)

    ####### actually transform the code

    veto = set()
    number = [0]
    def rename():
        name = "array_{0}".format(number[0])
        number[0] += 1
        if name in veto:
            return rename()
        else:
            return name

    enclosedfcns = {}
    encloseddata = {}
    columns = {}

    def recurse(node, symboltypes=symbols):
        if isinstance(node, ast.Name):
            veto.add(node.id)

        handlername = "do_" + node.__class__.__name__
        if handlername in globals():
            return globals()[handlername](node, symboltypes, environment, enclosedfcns, encloseddata, columns, recurse, rename)

        else:
            for fieldname in node._fields:
                if isinstance(getattr(node, fieldname), ast.AST):
                    setattr(node, fieldname, recurse(getattr(node, fieldname)))

                elif isinstance(getattr(node, fieldname), list):
                    setattr(node, fieldname, [recurse(x) for x in getattr(node, fieldname)])

            return node

    return recurse(syntaxtree), enclosedfcns, encloseddata, columns

##################################################################### specialized rules for each Python AST type

# Add ()

# alias ("name", "asname")

# And ()

# arg ("arg", "annotation") # Py3 only

# arguments ("args", "vararg", "kwarg", "defaults")                               # Py2
# arguments ("args", "vararg", "kwonlyargs", "kw_defaults", "kwarg", "defaults")  # Py3

# Assert ("test", "msg")

# Assign ("targets", "value")

# Attribute ("value", "attr", "ctx")

# AugAssign ("target", "op", "value")

# AugLoad ()

# AugStore ()

# BinOp ("left", "op", "right")

# BitAnd ()

# BitOr ()

# BitXor ()

# BoolOp ("op", "values")

# Break ()

# Bytes ("s",)  # Py3 only

# Call ("func", "args", "keywords", "starargs", "kwargs")

# ClassDef ("name", "bases", "body", "decorator_list")                                   # Py2
# ClassDef ("name", "bases", "keywords", "starargs", "kwargs", "body", "decorator_list") # Py3

# Compare ("left", "ops", "comparators")

# comprehension ("target", "iter", "ifs")

# Continue ()

# Del ()

# Delete ("targets",)

# DictComp ("key", "value", "generators")

# Dict ("keys", "values")

# Div ()

# Ellipsis ()

# Eq ()

# ExceptHandler ("type", "name", "body")

# Exec ("body", "globals", "locals") # Py2 only

# Expression ("body",)

# Expr ("value",)

# ExtSlice ("dims",)

# FloorDiv ()

# For ("target", "iter", "body", "orelse")

# FunctionDef ("name", "args", "body", "decorator_list")             # Py2
# FunctionDef ("name", "args", "body", "decorator_list", "returns")  # Py3

# GeneratorExp ("elt", "generators")

# Global ("names",)

# Gt ()

# GtE ()

# IfExp ("test", "body", "orelse")

# If ("test", "body", "orelse")

# ImportFrom ("module", "names", "level")

# Import ("names",)

# In ()

# Index ("value",)

# Interactive ("body",)

# Invert ()

# Is ()

# IsNot ()

# keyword ("arg", "value")

# Lambda ("args", "body")

# ListComp ("elt", "generators")

# List ("elts", "ctx")

# Load ()

# LShift ()

# Lt ()

# LtE ()

# Mod ()

# Module ("body",)

# Mult ()

# NameConstant ("value",)  # Py3 only

# Name ("id", "ctx")
def do_Name(node, symboltypes, environment, enclosedfcns, encloseddata, columns, recurse, rename):
    if isinstance(node.ctx, ast.Load):
        if node.id in symboltypes:
            node.plurtype = symboltypes[node.id]

    elif isinstance(node.ctx, ast.Store):
        raise NotImplementedError

    return node

# Nonlocal ("names",)  # Py3 only

# Not ()

# NotEq ()

# NotIn ()

# Num ("n",)

# Or ()

# Param ()

# Pass ()

# Pow ()

# Print ("dest", "values", "nl")  # Py2 only

# Raise ("type", "inst", "tback")  # Py2
# Raise ("exc", "cause")           # Py3

# Repr ("value",)  # Py2 only

# Return ("value",)

# RShift ()

# SetComp ("elt", "generators")

# Set ("elts",)

# Slice ("lower", "upper", "step")

# Starred ("value", "ctx")  # Py3 only

# Store ()

# Str ("s",)

# Sub ()

# Subscript ("value", "slice", "ctx")
def do_Subscript(node, symboltypes, environment, enclosedfcns, encloseddata, columns, recurse, rename):
    node.value = recurse(node.value)
    node.slice = recurse(node.slice)

    if isinstance(node.value.plurtype, List):
        if isinstance(node.slice, ast.Slice):
            raise NotImplementedError("slice of a list")

        if not isinstance(node.ctx, ast.Load):
            raise NotImplementedError("list dereference in {0} context".format(node.ctx))

        if isinstance(node.value.plurtype.of, Primitive):
            data = rename()
            columns[data] = node.value.plurtype.of.data

            offset = rename()
            columns[offset] = node.value.plurtype.offset

            return generate(node.value.plurtype.of,
                            "data[i] if at == 0 else data[offset[at - 1] + i]",
                            at = recurse(node.value),
                            i = recurse(node.slice),
                            data = ast.Name(data, ast.Load()),
                            offset = ast.Name(offset, ast.Load()))

        else:
            raise NotImplementedError

    else:
        return node

# Suite ("body",)

# TryExcept ("body", "handlers", "orelse")         # Py2 only
# TryFinally ("body", "finalbody")                 # Py2 only
# Try ("body", "handlers", "orelse", "finalbody")  # Py3 only

# Tuple ("elts", "ctx")

# UAdd ()

# UnaryOp ("op", "operand")

# USub ()

# While ("test", "body", "orelse")

# withitem ("context_expr", "optional_vars")      # Py3 only
# With ("context_expr", "optional_vars", "body")  # Py2
# With ("items", "body")                          # Py3

# Yield ("value",)

