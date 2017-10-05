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
import sys

import numpy
import numba
from numba.types import *

from arrowed.thirdparty.meta.decompiler.instructions import make_function
from arrowed.thirdparty.meta import dump_python_source

from arrowed.oam import *

py2 = (sys.version_info[0] <= 2)

################################################################ interface

class Compiled(object):
    def __init__(self, transformed, paramtypes, symnames):
        pass   # this would be a good place to put the exec

    @property
    def projection(self):
        pass

    def __call__(self, resolved, *args):
        pass

def compile(function, paramtypes, env={}, numbaargs={"nopython": True, "nogil": True}, debug=False):
    # turn the 'function' argument into the syntax tree of a function
    if isinstance(function, (unicode, str) if py2 else (str, bytes)):
        function = withequality(ast.parse(function).body[0])
        if isinstance(function, ast.Expr) and isinstance(function.value, ast.Lambda):
            if py2:
                return withequality(ast.FunctionDef("lambda", function.value.args, [function.value.body], []))
            else:
                return withequality(ast.FunctionDef("lambda", function.value.args, [function.value.body], [], None))

        if not isinstance(function, ast.FunctionDef):
            raise TypeError("string to compile must declare exactly one function")

    else:
        function = tofunction(function)

    # get a list of all symbols used by the function and any other functions it references
    symbolsused = set()
    externalfcns = {}
    def search(syntaxtree):
        if isinstance(syntaxtree, ast.AST):
            if isinstance(syntaxtree, ast.Name):
                symbolsused.add(syntaxtree.id)

            if isinstance(syntaxtree, ast.Call):
                try:
                    obj = eval(compile(ast.Expression(syntaxtree.func), "", "eval"), env)
                except Exception as err:
                    raise err.__class__("code to compile calls the expression below, but it is not defined in the environment (env):\n\n    {0}".format(dump_python_source(syntaxtree.func).strip()))
                else:
                    externalfcns[syntaxtree.func] = tofunction(obj)
                    search(externalfcns[syntaxtree.func])

            for x in syntaxtree._fields:
                search(getattr(syntaxtree, x))

        elif isinstance(syntaxtree, list):
            for x in syntaxtree:
                search(x)
                
    search(function)

    # symbol name generator
    def sym(key):
        if key not in sym.names:
            while True:
                trial = "_{0}".format(sym.number)
                sym.number += 1
                if trial not in symbolsused:
                    break
            sym.names[key] = trial
        return sym.names[key]

    sym.number = 0
    sym.names = {}

    # do the code transformation
    transformed = transform(function, paramtypes, externalfcns, sym)

    if debug:
        print("")
        print("Before transformation:\n----------------------\n{0}\n\nAfter transformation:\n---------------------\n{1}\n\nNew symbols:\n------------\n".format(dump_python_source(function).strip(), dump_python_source(transformed).strip()))
        for number in range(sym.number):
            name = "_{0}".format(number)
            if name in sym.names:
                print("{0} -->\t{1}".format(name, sym.names[name]))
        print("")

    return Compiled(transformed, paramtypes, sym.names)

################################################################ functions inserted into code

@numba.njit(int64(numba.optional(int64)))
def nonnegotiable(index):
    if index is None:
        raise TypeError("None found where object required")
    return index

@numba.njit(int64(int64[:], int64))
def indexget(start, index):
    return start[index]

@numba.njit(numba.optional(int64)(int64[:], int64[:], int64))
def maybe_indexget(startdata, startmask, index):
    if startmask[index]:
        return None
    else:
        return startdata[index]

@numba.njit(int64(int64[:], int64[:], int64, int64))
def listget(start, end, outerindex, index):
    offset = start[outerindex]
    size = end[outerindex] - offset
    if index < 0:
        index = size + index
    if index < 0 or index >= size:
        raise IndexError("index out of range")
    return offset + index

@numba.njit(int64(int64[:], int64[:], int64))
def listsize(start, end, index):
    return end[index] - start[index]

@numba.njit(numba.optional(int64)(int64[:], int64[:], int64[:], int64))
def maybe_listsize(startdata, startmask, enddata, index):
    if startmask[index]:
        return None
    else:
        return enddata[index] - startdata[index]

################################################################ for generating ASTs

# mix-in for defining equality on ASTs
class WithEquality(object):
    def __eq__(self, other):
        if isinstance(other, ast.AST):
            assert isinstance(other, WithEquality)
        return self.__class__ == other.__class__ and all(getattr(self, x) == getattr(other, x) for x in self._fields)

    def __hash__(self):
        hashable = lambda x: tuple(x) if isinstance(x, list) else x
        return hash((self.__class__, tuple(hashable(getattr(self, x)) for x in self._fields)))

def withequality(obj):
    if isinstance(obj, ast.AST):
        if not isinstance(obj, WithEquality):
            if obj.__class__.__name__ not in withequality.classes:
                withequality.classes[obj.__class__.__name__] = type(obj.__class__.__name__, (obj.__class__, WithEquality), {})
            out = withequality.classes[obj.__class__.__name__]()

            for x in obj._fields:
                setattr(out, x, getattr(obj, x))

            out.lineno = getattr(obj, "lineno", 1)
            out.col_offset = getattr(obj, "col_offset", 0)
            out.type = getattr(obj, "type", None)
            obj = out

        for x in obj._fields:
            setattr(obj, x, withequality(getattr(obj, x)))
        return obj

    elif isinstance(obj, list):
        return [withequality(x) for x in obj]

    else:
        return obj

withequality.classes = {}

def compose(pyast, lineno=None, type=None, **replacements):
    if lineno is None:
        lineno, col_offset = 1, 0
    else:
        lineno, col_offset = lineno.lineno, lineno.col_offset

    def recurse(x):
        if isinstance(x, ast.AST):
            if isinstance(x, ast.Name) and x.id in replacements:
                x = replacements[x.id]

            if isinstance(x, ast.Attribute) and x.attr in replacements:
                x.attr = replacements[x.attr]

            if isinstance(x, ast.FunctionDef) and x.name in replacements:
                x.name = replacements[x.name]

            for f in x._fields:
                setattr(x, f, recurse(getattr(x, f)))

            x.lineno, x.col_offset = lineno, col_offset
            x.type = type
            return x

        elif isinstance(x, list):
            return [recurse(xi) for xi in x]

        else:
            return x

    return recurse(pyast)

def toexpr(string, lineno=None, type=None, **replacements):
    return compose(withequality(ast.parse(string).body[0].value), lineno=lineno, type=type, **replacements)

def tostmt(string, lineno=None, type=None, **replacements):
    return compose(withequality(ast.parse(string).body[0]), lineno=lineno, type=type, **replacements)

def tostmts(string, lineno=None, type=None, **replacements):
    return compose(withequality(ast.parse(string).body), lineno=lineno, type=type, **replacements)

def toname(string, lineno=None, type=None, ctx=ast.Load()):
    out = withequality(ast.Name(string, ctx))
    if lineno is None:
        out.lineno, out.col_offset = 1, 0
    else:
        out.lineno, out.col_offset = lineno.lineno, lineno.col_offset
    out.type = type
    return out

def toliteral(obj, lineno=None, type=None):
    if isinstance(obj, str):
        out = withequality(ast.Str(obj))
    elif isinstance(obj, (int, float)):
        out = withequality(ast.Num(obj))
    else:
        raise AssertionError
    if lineno is None:
        out.lineno, out.col_offset = 1, 0
    else:
        out.lineno, out.col_offset = lineno.lineno, lineno.col_offset
    out.type = type
    return out

def tofunction(obj, lineno=None, type=None):
    if not hasattr(obj, "__code__"):
        raise TypeError("attempting to compile {0}, but it is not a Python function (something with a __code__ attribute); no class constructors or C extensions allowed".format(repr(obj)))
    out = make_function(obj.__code__)
    if isinstance(out, ast.Lambda):
        if py2:
            return withequality(ast.FunctionDef("lambda", out.args, [out.body], []))
        else:
            return withequality(ast.FunctionDef("lambda", out.args, [out.body], [], None))
    if lineno is not None:
        out.lineno, out.col_offset = lineno.lineno, lineno.col_offset
    out.type = type
    return out

################################################################ description of a symbol's type

class Possibility(object):
    def __init__(self, oam, conditions=None):
        self.oam = oam
        self.conditions = conditions

class Type(object):
    def __init__(self, possibilities, enclosinglist=None):
        if not isinstance(possibilities, (list, tuple)):
            possibilities = [possibilities]
        possibilities = [x if isinstance(x, Possibility) else Possibility(x) for x in possibilities]
        self.possibilities = possibilities
        self.enclosinglist = enclosinglist

unknown = Type([])

################################################################ the main transformation function

def transform(function, paramtypes, externalfcns, sym):
    return function

################################################################ specialized rules for each Python AST type

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
