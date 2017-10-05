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
import re
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
    def __init__(self, transformed, paramtypes, env, symnames):
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
    def search(node):
        if isinstance(node, ast.AST):
            if isinstance(node, ast.Name):
                symbolsused.add(node.id)

            if isinstance(node, ast.Call):
                try:
                    obj = eval(compile(ast.Expression(node.func), "", "eval"), env)
                except Exception as err:
                    raise err.__class__("code to compile calls the expression below, but it is not defined in the environment (env):\n\n    {0}".format(dump_python_source(node.func).strip()))
                else:
                    externalfcns[node.func] = tofunction(obj)
                    search(externalfcns[node.func])

            for x in node._fields:
                search(getattr(node, x))

        elif isinstance(node, list):
            for x in node:
                search(x)
                
    search(function)

    # symbol name generator
    def sym(key):
        if key not in sym.names:
            prefix = sym.bad.sub("", key)
            if len(prefix) == 0 or prefix[0] in sym.numberchars:
                prefix = "_" + prefix

            trial = prefix
            while trial in symbolsused:
                trial = "{0}_{1}".format(prefix, sym.number)
                sym.number += 1

            sym.names[key] = trial
            if key != trial:
                sym.remapped.append((key, trial))

        return sym.names[key]

    sym.bad = re.compile(r"[^a-zA-Z0-9_]*")
    sym.numberchars = [chr(x) for x in range(ord("0"), ord("9") + 1)]
    sym.number = 0
    sym.names = {}
    sym.remapped = []

    env = env.copy()
    env[sym("nonnegotiable")] = nonnegotiable
    env[sym("indexget")] = indexget
    env[sym("maybe_indexget")] = maybe_indexget
    env[sym("listget")] = listget
    env[sym("listsize")] = listsize
    env[sym("maybe_listsize")] = maybe_listsize

    # do the code transformation
    transformed = transform(function, paramtypes, externalfcns, sym)

    if debug:
        print("")
        print("Before transformation:\n----------------------\n{0}\n\nAfter transformation:\n---------------------\n{1}".format(dump_python_source(function).strip(), dump_python_source(transformed).strip()))
        if len(sym.remapped) > 0:
            print("\nRemapped symbol names:\n----------------------")
            formatter = "    {0:%ds} --> {1}" % max([len(name) for name, value in sym.remapped] + [0])
            for name, value in sym.remapped:
                print(formatter.format(name, value))
        print("")

    return Compiled(transformed, paramtypes, env, sym.names)

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

class Parameter(object):
    def __init__(self, originalname, default):
        self.originalname = originalname
        self.default = default
        self.type = None

    def args(self):
        if py2:
            return [ast.Name(self.originalname, ast.Param())]
        else:
            return [ast.arg(self.originalname, None)]

    def defaults(self):
        return [self.default]

class TransformedParameter(Parameter):
    def __init__(self, originalname, type):
        self.originalname = originalname
        self.type = type
        self.transformed = []

    def args(self):
        if py2:
            return [ast.Name(x, ast.Param()) for x in self.transformed]
        else:
            return [ast.arg(x, None) for x in self.transformed]

    def defaults(self):
        return []

class Parameters(object):
    def __init__(self, order):
        self.order = order
        self.lookup = dict((x.originalname, x) for x in self.order)

    def args(self):
        if py2:
            return ast.arguments(sum((x.args() for x in self.order), []), None, None, sum((x.defaults() for x in self.order), []))
        else:
            return ast.arguments(sum((x.args() for x in self.order), []), None, [], [], None, sum((x.defaults() for x in self.order), []))

def transform(function, paramtypes, externalfcns, sym):
    # check for too much dynamism
    if function.args.vararg is not None:
        raise TypeError("function {0} has *args, which are not allowed in compiled functions".format(repr(function.name)))
    if function.args.kwarg is not None:
        raise TypeError("function {0} has **kwds, which are not allowed in compiled functions".format(repr(function.name)))

    # identify which parameters will be transformed (probably from a single parameter to multiple)
    defaults = [None] * (len(function.args.args) - len(function.args.defaults)) + function.args.defaults
    parameters = []
    for index, (param, default) in enumerate(zip(function.args.args, defaults)):
        if py2:
            assert isinstance(param, ast.Name) and isinstance(param.ctx, ast.Param)
            paramname = param.id
        else:
            assert isinstance(param, ast.arg)
            paramname = param.arg

        if index in paramtypes and paramname in paramtypes:
            raise ValueError("parameter at index {0} and parameter named {1} are the same parameter in paramtypes".format(index, repr(paramname)))

        if index in paramtypes:
            paramtype = paramtypes[index]
        elif paramname in paramtypes:
            paramtype = paramtypes[paramname]
        else:
            paramtype = None

        if paramtype is None:
            parameters.append(Parameter(paramname, default))
        else:
            if default is not None:
                raise ValueError("parameter {0} is an argument defined in paramtypes, which is not allowed to have default parameters")
            parameters.append(TransformedParameter(paramname, Type(paramtype)))

    parameters = Parameters(parameters)

    everything = globals()

    def recurse(node):
        if isinstance(node, ast.AST):
            handlername = "do_" + node.__class__.__name__
            if handlername in everything:
                return everything[handlername](node, parameters, externalfcns, sym)
            else:
                for x in node._fields:
                    setattr(node, x, recurse(getattr(node, x)))
                return node

        elif isinstance(node, list):
            return [recurse(x) for x in node]

        else:
            return node

    transformed = recurse(function)
    transformed.args = parameters.args()

    return transformed

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
def do_Subscript(node, parameters, externalfcns, sym):
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
