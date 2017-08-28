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
from plur.types.arrayname import ArrayName
from plur.types.columns import withcolumns, hascolumns
from plur.thirdparty.meta.decompiler.instructions import make_function
from plur.thirdparty.meta import dump_python_source

##################################################################### entry point

def run(arrays, fcn, paramtypes={}, environment={}, numba=None, debug=False, debugmap={}, *otherargs):
    if isinstance(paramtypes, Type):
        types = [paramtypes]
    elif isinstance(paramtypes, dict):
        types = paramtypes.values()
    else:
        types = paramtypes

    rewrittenfcn, arrayparams = toplur(fcn, paramtypes=paramtypes, environment=environment, numba=numba, debug=debug, debugmap=debugmap)

    # add missing arrays to the set, if possible
    fillin(arrays, types, filter=arrayparams, numba=numba)

    args = tuple(arrays[n] for n in arrayparams) + otherargs
    return rewrittenfcn(*args)

def toplur(fcn, paramtypes={}, environment={}, numba=None, debug=False, debugmap={}):
    if isinstance(paramtypes, Type):
        paramtypes = [paramtypes]

    code, arrayparams, enclosedfcns, encloseddata = rewrite(fcn, paramtypes, environment)
    fcnname = code.name
    filename = fcn.__code__.co_filename

    if debug:
        print("BEFORE:\n{0}\nAFTER:\n{1}".format(
            dump_python_source(fcn2syntaxtree(fcn)), dump_python_source(code)))
        for x, y in zip(code.args.args, arrayparams):
            print("{0} -->\t{1}{2}".format(x.id if isinstance(x, ast.Name) else x.arg, y, "" if y not in debugmap else " ({0})".format(debugmap[y])))

    if numba is not None and numba is not False:
        if numba is True:
            numba = {}
        environment = dict(environment)
        environment["__numba_args"] = numba
        code = [generate(None, "import numba"),
                code,
                generate(None, "toname = numba.njit(**__numba_args)(fromname)",
                         fromname=ast.Name(fcnname, ast.Load()),
                         toname=ast.Name(fcnname, ast.Store()))]

    rewrittenfcn = compilefcn(code, fcnname, filename, environment=environment)
    return rewrittenfcn, arrayparams

##################################################################### technical interface

def fillin(arrays, types, filter=None, numba=None):
    def recurse(tpe):
        # P
        if isinstance(tpe, Primitive):
            if filter is None or tpe.column not in arrays:
                raise ValueError("required array \"{0}\" not found in arrays".format(tpe.column))

        # L
        elif isinstance(tpe, List):
            if filter is None or tpe.column in filter or tpe.column2 in filter:
                beginname = tpe.column
                endname = tpe.column2
                if beginname not in arrays or endname not in arrays:
                    offsetname = beginname[:-len(ArrayName.LIST_BEGIN)] + ArrayName.LIST_OFFSET
                    if offsetname not in arrays:
                        sizename = beginname[:-len(ArrayName.LIST_BEGIN)] + ArrayName.LIST_SIZE
                        if sizename not in arrays:
                            raise ValueError("required array \"{0}\"\n            or \"{1}\"\n            or \"{2}\" and \"{3}\" not found in arrays".format(offsetname, sizename, beginname, endname))

                        # if you have a size array, make an offset array as a new copy (one element larger)
                        sizearray = arrays[sizename]
                        offsetarray = numpy.empty(len(sizearray) + 1, dtype=numpy.int64)
                        offsetarray[0] = 0
                        numpy.cumsum(sizearray, out=offsetarray[1:])
                        arrays[offsetname] = offsetarray

                # if you have an offset array, make begin and end with views (virtually no cost)
                arrays[beginname] = arrays[offsetname][:-1]
                arrays[endname] = arrays[offsetname][1:]

            recurse(tpe.of)

        # U
        elif isinstance(tpe, Union):
            if filter is None or tpe.column in filter or tpe.column2 in filter:
                tagname = tpe.column
                offsetname = tpe.column2
                if tagname not in arrays:
                    raise ValueError("required array \"{0}\" not found in arrays".format(tagname))
                if offsetname not in arrays:
                    raise NotImplementedError("FIXME!")
                for t in tpe.of:
                    recurse(t)

        # R
        elif isinstance(tpe, Record):
            for fn, ft in tpe.of:
                recurse(ft)

        else:
            assert False, "unexpected type object: {0}".format(tpe)
                        
    for tpe in types:
        recurse(tpe)

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
    environment = dict([("len", len)] + list(environment.items()))

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

    zeros = toreplace
    def recurse(node, symboltypes=symbols, unionop=unionop):
        if isinstance(node, ast.AST):
            if isinstance(node, ast.Name):
                veto.add(node.id)

            handlername = "do_" + node.__class__.__name__
            if handlername in globals():
                return globals()[handlername](node, symboltypes, environment, enclosedfcns, encloseddata, zeros, recurse, colname, unionop)

            else:
                for fieldname in node._fields:
                    if isinstance(getattr(node, fieldname), ast.AST):
                        setattr(node, fieldname, recurse(getattr(node, fieldname)))

                    elif isinstance(getattr(node, fieldname), list):
                        setattr(node, fieldname, [recurse(x) for x in getattr(node, fieldname)])

                return node

        elif isinstance(node, list):
            return [recurse(x, symboltypes=symbols, unionop=unionop) for x in node]

        else:
            return node

    code = recurse(syntaxtree)

    newparams = [numbered for named, numbered in columns.items()]
    newparams.sort(key=lambda x: int(x[6:]))

    code.args.args = [ln(ast.Name(x, ast.Param())) if py2 else ln(ast.arg(x, None)) for x in newparams] + code.args.args

    arrayparams = [[named for named, numbered in columns.items() if numbered == x][0] for x in newparams]
    return code, arrayparams, enclosedfcns, encloseddata

##################################################################### utility functions

def ln(x):
    if not hasattr(x, "lineno"):
        x.lineno = -1
    if not hasattr(x, "col_offset"):
        x.col_offset = -1
    return x

def asteq(x, y):
    if isinstance(x, list) and isinstance(y, list) and len(x) == len(y):
        return all(asteq(xi, yi) for xi, yi in zip(x, y))

    elif isinstance(x, ast.AST) and isinstance(y, ast.AST):
        return x.__class__ == y.__class__ and all(asteq(getattr(x, n), getattr(y, n)) for n in x._fields)

    else:
        return x == y
    
def fcn2syntaxtree(fcn):
    out = make_function(fcn.__code__)
    if isinstance(out, ast.Lambda):
        if py2:
            return ln(ast.FunctionDef("lambda", out.args, [out.body], []))
        else:
            return ln(ast.FunctionDef("lambda", out.args, [out.body], [], None))
    else:
        return out

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

        if plurtype is not None:
            out.plurtype = plurtype

    else:
        out = recurse(parsed.body)
    
    return out

def node2array(node, tpe, colname, unionop):
    # P
    if isinstance(tpe, Primitive):
        return generate(None, "array[at]", array=ast.Name(colname(tpe.column), ast.Load()), at=node)

    # L
    elif isinstance(tpe, List):
        if isinstance(node, ast.Num) and node.n == 0:
            return generate(tpe, "0")
        else:
            return generate(tpe, "array[at]", array=ast.Name(colname(tpe.column), ast.Load()), at=node)

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
def do_Assign(node, symboltypes, environment, enclosedfcns, encloseddata, zeros, recurse, colname, unionop):
    if isinstance(node.value, ast.Name) and isinstance(node.value.ctx, ast.Load) and node.value.id in symboltypes:
        node.value.plurtype = symboltypes[node.value.id]
    else:
        node.value = recurse(node.value)

    def unassign(lhs):
        if isinstance(lhs, ast.Name):
            assert isinstance(lhs.ctx, ast.Store)
            if lhs.id in symboltypes:
                del symboltypes[lhs.id]

        elif isinstance(lhs, (ast.List, ast.Tuple)):
            assert isinstance(lhs.ctx, ast.Store)
            for target in lhs.elts:
                unassign(target)

    for x in node.targets:
        unassign(x)

    def assign(lhs, rhs):
        if isinstance(lhs, ast.Name):
            if hasattr(rhs, "plurtype"):
                symboltypes[lhs.id] = rhs.plurtype

        elif isinstance(lhs, (ast.List, ast.Tuple)):
            if hasattr(rhs, "plurtype"):
                raise TypeError("cannot unpack-and-assign a PLUR type")
            elif isinstance(rhs, ast.Tuple):
                for target, value in zip(lhs.elts, rhs.elts):
                    assign(target, value)

    for x in node.targets:
        assign(x, node.value)

    return node

# Attribute ("value", "attr", "ctx")
def do_Attribute(node, symboltypes, environment, enclosedfcns, encloseddata, zeros, recurse, colname, unionop):
    def fieldtype(tpe):
        for fn, ft in tpe.of:
            if fn == node.attr:
                return ft
        raise TypeError("record has no field named \"{0}\"".format(node.attr))
    
    def subunionop(tpe, node):
        assert isinstance(tpe, Record)
        return unionop(fieldtype(tpe), node)

    node.value = recurse(node.value, unionop=subunionop)

    if hasattr(node.value, "plurtype") and isinstance(node.value.plurtype, Record):
        return node2array(node.value, fieldtype(node.value.plurtype), colname, unionop)

    elif hasattr(node.value, "plurtype") and isinstance(node.value.plurtype, Union):
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
def do_Call(node, symboltypes, environment, enclosedfcns, encloseddata, zeros, recurse, colname, unionop):
    node.func = recurse(node.func)

    def descend(node, unionop):
        node.args = recurse(node.args, unionop=unionop)
        node.keywords = recurse(node.keywords)
        node.starargs = recurse(node.starargs)
        node.kwargs = recurse(node.kwargs)
        return node

    # if this is a function we know
    if isinstance(node.func, ast.Name) and node.func.id in environment:
        # len
        if environment[node.func.id] == len:
            if len(node.args) != 1:
                raise TypeError("len() takes exactly one argument ({0} given)".format(len(node.args)))

            def subunionop(tpe, node):
                if isinstance(tpe, List):
                    return generate(tpe, "end[at] - begin[at]",
                                    begin=ast.Name(colname(tpe.column), ast.Load()),
                                    end=ast.Name(colname(tpe.column2), ast.Load()),
                                    at=node)
                else:
                    return unionop(tpe, node)

            descend(node, subunionop)
            
            if hasattr(node.args[0], "plurtype") and isinstance(node.args[0].plurtype, List):
                tpe = node.args[0].plurtype

                if isinstance(node.args[0], ast.Num):
                    assert node.args[0].n == 0
                    return generate(tpe, "end[0]", end=ast.Name(colname(tpe.column2), ast.Load()))

                else:
                    assert isinstance(node.args[0], ast.Subscript)
                    assert isinstance(node.args[0].value, ast.Name) and node.args[0].value.id == colname(tpe.column)
                    assert isinstance(node.args[0].slice, ast.Index)
                    assert isinstance(node.args[0].ctx, ast.Load)

                    return generate(tpe, "end[i] - current",
                                    end=ast.Name(colname(tpe.column2), ast.Load()),
                                    i=node.args[0].slice.value,
                                    current=node.args[0])

            elif hasattr(node.args[0], "plurtype") and isinstance(node.args[0].plurtype, Union):
                return node.args[0]

            else:
                node

        # ...others?
        else:
            if any(hasattr(x, "plurtype") and isinstance(x.plurtype, Type) for x in node.args):
                raise TypeError("can't call {0} on plur types".format(dump_python_source(node.func).strip()))
            else:
                return descend(node, unionop)

    # not a function that we know
    else:
        if any(hasattr(x, "plurtype") and isinstance(x.plurtype, Type) for x in node.args):
            raise TypeError("can't call {0} on plur types".format(dump_python_source(node.func).strip()))
        else:
            return descend(node, unionop)

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
def do_For(node, symboltypes, environment, enclosedfcns, encloseddata, zeros, recurse, colname, unionop):
    node.iter = recurse(node.iter)
    node.target = recurse(node.target)

    if hasattr(node.iter, "plurtype") and isinstance(node.iter.plurtype, List) and isinstance(node.target, ast.Name) and isinstance(node.target.ctx, ast.Store):
        tpe = node.iter.plurtype

        if isinstance(node.iter, ast.Num):
            assert node.iter.n == 0
            node.iter = generate(tpe, "range(end[0])",
                                 end=ast.Name(colname(tpe.column2), ast.Load()))

        else:
            assert isinstance(node.iter, ast.Subscript)
            assert isinstance(node.iter.value, ast.Name) and node.iter.value.id == colname(tpe.column)
            assert isinstance(node.iter.slice, ast.Index)
            assert isinstance(node.iter.ctx, ast.Load)

            node.iter = generate(tpe, "range(current, end[i])",
                                 end=ast.Name(colname(tpe.column2), ast.Load()),
                                 i=node.iter.slice.value,
                                 current=node.iter)

        symboltypes[node.target.id] = tpe.of

    node.body = recurse(node.body)
    node.orelse = recurse(node.orelse)

    return node

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
def do_Name(node, symboltypes, environment, enclosedfcns, encloseddata, zeros, recurse, colname, unionop):
    if isinstance(node.ctx, ast.Load):
        if node.id in symboltypes:
            tpe = symboltypes[node.id]

            if node.id in zeros:
                node = generate(tpe, "0")

            return node2array(node, tpe, colname, unionop)

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
def do_Subscript(node, symboltypes, environment, enclosedfcns, encloseddata, zeros, recurse, colname, unionop):
    node.slice = recurse(node.slice)

    if isinstance(node.slice, ast.Index) and isinstance(node.ctx, ast.Load):
        index = node.slice.value
    else:
        index = None

    def subunionop(tpe, node):
        assert isinstance(tpe, List)

        if isinstance(node, ast.Num) and node.n == 0:
            offsetat = ln(ast.Num(0))
        else:
            offsetat = generate(None, "offset[at]", at=node, offset=ast.Name(colname(tpe.column), ast.Load()))

        if index is None:
            raise NotImplementedError

        if isinstance(offsetat, ast.Num) and offsetat.n == 0:
            offsetatplusi = index
        else:
            offsetatplusi = generate(None, "offsetat + i", offsetat=offsetat, i=index)

        return unionop(tpe.of, offsetatplusi)

    node.value = recurse(node.value, unionop=subunionop)

    if hasattr(node.value, "plurtype") and isinstance(node.value.plurtype, List):
        if not isinstance(node.slice, ast.Index) or not isinstance(node.ctx, ast.Load):
            raise NotImplementedError

        if isinstance(node.value, ast.Num) and node.value == 0:
            atplusi = index
        else:
            atplusi = generate(None, "at + i", at=node.value, i=index)

        return node2array(atplusi,
                          node.value.plurtype.of,
                          colname,
                          unionop)

    elif hasattr(node.value, "plurtype") and isinstance(node.value.plurtype, Union):
        return node.value

    else:
        return node

# Suite ("body",)

# TryExcept ("body", "handlers", "orelse")         # Py2 only
# TryFinally ("body", "finalbody")                 # Py2 only
# Try ("body", "handlers", "orelse", "finalbody")  # Py3 only

# Tuple ("elts", "ctx")
def do_Tuple(node, symboltypes, environment, enclosedfcns, encloseddata, zeros, recurse, colname, unionop):
    elts = []
    for x in node.elts:
        if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Load) and x.id in symboltypes:
            x.plurtype = symboltypes[x.id]
            elts.append(x)
        else:
            elts.append(recurse(x))

    node.elts = elts
    return node

# UAdd ()

# UnaryOp ("op", "operand")

# USub ()

# While ("test", "body", "orelse")

# withitem ("context_expr", "optional_vars")      # Py3 only
# With ("context_expr", "optional_vars", "body")  # Py2
# With ("items", "body")                          # Py3

# Yield ("value",)

