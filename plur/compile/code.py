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

from plur.util import *
from plur.types import *
from plur.types.columns import withcolumns, hascolumns
from plur.thirdparty.meta.decompiler.instructions import make_function
from plur.thirdparty.meta import dump_python_source

##################################################################### entry point

def local(fcn, paramtypes={}, environment={}, numba=None, debug=False):
    code, arrayparams, enclosedfcns, encloseddata = rewrite(fcn, paramtypes, environment)
    fcnname = code.name
    filename = fcn.__code__.co_filename

    if debug:
        print("BEFORE:\n{0}\nAFTER:\n{1}".format(
            dump_python_source(fcn2syntaxtree(fcn)), dump_python_source(code)))
        for x in arrayparams:
            print("{0}\t{1}".format(x, arrays[x]))
            print("")

    if numba is not None:
        environment = dict(environment)
        environment["numbaparams"] = numba
        code = [generate(None, "import numba"),
                code,
                generate(None, "out = numba.njit(**numbaparams)(name)",
                         name=ast.Name(fcnname, ast.Load()))]

    rewrittenfcn = compilefcn(code, fcnname, filename, environment=environment)

    out = lambda arrayargs, *otherargs: rewrittenfcn(*(tuple(arrayargs) + otherargs))
    out.__name__ = fcnname

    return out, arrayparams

def compilefcn(code, fcnname, filename, environment={}):
    if not isinstance(code, list):
        code = [code]
    compiled = compile(ln(ast.Module(code)), filename, "exec")
    out = dict(environment)
    exec(compiled, out)    # exec can't be called in the same function with nested functions
    return out[fcnname]

def callfcn(arrays, rewrittenfcn, arrayargs, *otherargs):
    return rewrittenfcn(*(tuple(arrays[x] for x in arrayargs) + otherargs))

def rewrite(fcn, paramtypes={}, environment={}):
    ####### normalize and check inputs

    if callable(fcn) and hasattr(fcn, "__code__"):
        syntaxtree = fcn2syntaxtree(fcn)
    else:
        raise TypeError("fcn must be a Python function")

    if isinstance(paramtypes, dict):
        symbols = dict(paramtypes)
    else:
        try:
            iter(paramtypes)
        except TypeError:
            raise TypeError("paramtypes must be a dict of name -> type or an iterable of types for each fcn parameter")
        else:
            symbols = dict((n.id if isinstance(n, ast.Name) else n.arg, t) for n, t in zip(syntaxtree.args.args, paramtypes))

    if hasattr(fcn, "__annotations__"):
        for n, t in fcn.__annotations__:
            if n != "return" and n not in symbols:
                symbols[n] = t

    parameters = [n.id if isinstance(n, ast.Name) else n.arg for n in syntaxtree.args.args]
    toreplace = list(symbols.keys())

    if not all(x in parameters for x in toreplace):
        raise TypeError("all paramtypes ({0}) must be arguments of fcn ({1})".format(", ".join(toreplace), ", ".join(parameters)))

    len_defaults = len(() if fcn.__defaults__ is None else fcn.__defaults__)
    newargs = []
    for i, (n, arg) in enumerate(zip(parameters, syntaxtree.args.args)):
        if n in toreplace and i + len_defaults >= len(parameters):
            raise TypeError("paramtypes ({0}) must not have default values".format(", ".join(toreplace)))

        if n not in toreplace:
            newargs.append(arg)

    syntaxtree.args.args = newargs

    if not isinstance(environment, dict):
        raise TypeError("environment must be a Python dict (e.g. vars())")

    for t in symbols.values():
        if not hascolumns(t):
            raise TypeError("type is missing column information (e.g. create with plur.types.columns.columns2type or pass through plur.types.columns.withcolumns)")

    ####### actually do the rewriting

    columns = {}
    veto = set()
    number = [0]
    def colname(c):
        assert c is not None
                
        if c in columns:
            return columns[c]

        else:
            name = "array_{0}".format(number[0])
            number[0] += 1
            if name in veto:
                return colname(c)
            else:
                columns[c] = name
                return name

    enclosedfcns = {}
    encloseddata = {}

    def unionop(tpe, node):
        return generate(tpe, "array[at]", array=ast.Name(colname(tpe.column), ast.Load()), at=node)

    def recurse(node, symboltypes=symbols, unionop=unionop):
        if isinstance(node, ast.Name):
            veto.add(node.id)

        handlername = "do_" + node.__class__.__name__
        if handlername in globals():
            return globals()[handlername](node, symboltypes, environment, enclosedfcns, encloseddata, recurse, colname, unionop)

        else:
            for fieldname in node._fields:
                if isinstance(getattr(node, fieldname), ast.AST):
                    setattr(node, fieldname, recurse(getattr(node, fieldname)))

                elif isinstance(getattr(node, fieldname), list):
                    setattr(node, fieldname, [recurse(x) for x in getattr(node, fieldname)])

            return node

    code = recurse(syntaxtree)

    newparams = [numbered for named, numbered in columns.items()]
    newparams.sort(key=lambda x: int(x[6:]))

    code.args.args = [ln(ast.Name(x, ast.Param())) if py2 else ln(ast.arg(x, None)) for x in newparams] + code.args.args

    code.body = [generate(None, "name = 0", name=ast.Name(x, ast.Store())) for x in toreplace] + code.body

    arrayparams = [[named for named, numbered in columns.items() if numbered == x][0] for x in newparams]
    return code, arrayparams, enclosedfcns, encloseddata

##################################################################### utility functions

def ln(x):
    if not hasattr(x, "lineno"):
        x.lineno = -1
    if not hasattr(x, "col_offset"):
        x.col_offset = -1
    return x

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
            ln(x)
            x.plurtype = None
            x.__eq__ = MethodType(__eq__, x)
            x.__hash__ = MethodType(__hash__, x)
            for fieldname in x._fields:
                addmethods(getattr(x, fieldname))

        elif isinstance(x, list):
            return [addmethods(y) for y in x]

        return x

    out = make_function(fcn.__code__)
    if isinstance(out, ast.Lambda):
        if py2:
            out = ast.FunctionDef("lambda", out.args, [out.body], [])
        else:
            out = ast.FunctionDef("lambda", out.args, [out.body], [], None)

    return addmethods(out)

def generate(plurtype, format, **subs):
    def recurse(x):
        if isinstance(x, ast.Name) and x.id in subs:
            return ln(subs[x.id])

        elif isinstance(x, ast.AST):
            for fieldname in x._fields:
                setattr(x, fieldname, recurse(getattr(x, fieldname)))
            return x

        elif isinstance(x, list):
            return [recurse(y) for y in x]

        else:
            return x

    parsed = ast.parse(format)
    if len(parsed.body) == 1:
        if isinstance(parsed.body[0], ast.Expr):
            out = recurse(parsed.body[0].value)
        else:
            out = recurse(parsed.body[0])
        out.plurtype = plurtype
    else:
        out = recurse(parsed.body)
    
    return out

def node2array(node, tpe, colname, unionop):
    # P
    if isinstance(tpe, Primitive):
        return generate(tpe, "array[at]", array=ast.Name(colname(tpe.column), ast.Load()), at=node)

    # L
    elif isinstance(tpe, List):
        return generate(tpe, "0 if at == 0 else array[at - 1]", array=ast.Name(colname(tpe.column), ast.Load()), at=node)

    # U
    elif isinstance(tpe, Union):
        tag = ast.Name(colname(tpe.column), ast.Load())
        offsetat = generate(None, "offset[at]",
                            offset=ast.Name(colname(tpe.column2), ast.Load()),
                            at=node)
        def recurse(i):
            if i == len(tpe.of) - 1:
                return unionop(tpe.of[i], offsetat)
            else:
                return generate(None, "consequent if tag[at] == i else alternate",
                                tag=tag,
                                consequent=unionop(tpe.of[i], offsetat),
                                at=node,
                                i=ast.Num(i),
                                alternate=recurse(i + 1))
        out = recurse(0)
        out.plurtype = tpe
        return out

    # R
    elif isinstance(tpe, Record):
        node.plurtype = tpe
        return node
    else:
        assert False, "unexpected type object {0}".format(tpe)

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
def do_Attribute(node, symboltypes, environment, enclosedfcns, encloseddata, recurse, colname, unionop):
    def fieldtype(tpe):
        for fn, ft in tpe.of:
            if fn == node.attr:
                return ft
        raise TypeError("record has no field named \"{0}\"".format(node.attr))
    
    def subunionop(tpe, node):
        assert isinstance(tpe, Record)
        return unionop(fieldtype(tpe), node)

    node.value = recurse(node.value, unionop=subunionop)

    if isinstance(node.value.plurtype, Record):
        return node2array(node.value, fieldtype(node.value.plurtype), colname, unionop)

    elif isinstance(node.value.plurtype, Union):
        return node.value

    else:
        return node

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
def do_Name(node, symboltypes, environment, enclosedfcns, encloseddata, recurse, colname, unionop):
    if isinstance(node.ctx, ast.Load):
        if node.id in symboltypes:
            return node2array(node, symboltypes[node.id], colname, unionop)

    elif isinstance(node.ctx, ast.Store):
        if node.id in symboltypes:
            raise TypeError("{0} is read-only".format(node.id))

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
def do_Subscript(node, symboltypes, environment, enclosedfcns, encloseddata, recurse, colname, unionop):
    node.slice = recurse(node.slice)

    if isinstance(node.slice, ast.Slice):
        raise NotImplementedError
    elif isinstance(node.slice, ast.Index):
        if isinstance(node.ctx, ast.Load):
            index = node.slice.value
        else:
            raise NotImplementedError
    else:
        raise NotImplementedError

    def subunionop(tpe, node):
        assert isinstance(tpe, List)
        return unionop(tpe.of,
                       generate(None, "(0 if at == 0 else offset[at - 1]) + i",
                                at=node,
                                offset=ast.Name(colname(tpe.column), ast.Load()),
                                i=index))

    node.value = recurse(node.value, unionop=subunionop)

    if isinstance(node.value.plurtype, List):
        return node2array(generate(None, "at + i", at=node.value, i=index),
                          node.value.plurtype.of,
                          colname,
                          unionop)

    elif isinstance(node.value.plurtype, Union):
        return node.value

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

