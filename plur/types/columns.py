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

import numpy

from plur.util import *
from plur.types.type import Type
from plur.types.primitive import Primitive # P
from plur.types.list import List           # L
from plur.types.union import Union         # U
from plur.types.record import Record       # R

from plur.types.primitive import withrepr
from plur.types.arrayname import ArrayName

def withcolumns(tpe, prefix, delimiter="-"):
    return columns2type(type2columns(tpe, prefix, delimiter=delimiter), prefix, delimiter="-")

def hascolumns(tpe):
    return hasattr(tpe, "column") and all(hascolumns(t) for t in tpe.children)

def type2columns(tpe, prefix, delimiter="-", offsettype=numpy.dtype(numpy.int64)):
    def recurse(name, tpe):
        if tpe.rtname is not None:
            raise NotImplementedError

        # P
        if isinstance(tpe, Primitive):
            return [(name.str(), tpe.of)]

        # L
        elif isinstance(tpe, List):
            return [(name.toListOffset().str(), offsettype)] + recurse(name.toListData(), tpe.of)

        # U
        elif isinstance(tpe, Union):
            if len(tpe.of) < 2**8:
                uniontype = numpy.dtype(numpy.uint8)
            elif len(tpe.of) < 2**16:
                uniontype = numpy.dtype(numpy.uint16)
            elif len(tpe.of) < 2**32:
                uniontype = numpy.dtype(numpy.uint32)
            elif len(tpe.of) < 2**64:
                uniontype = numpy.dtype(numpy.uint64)
            else:
                assert False, "union has way too many type possibilities ({0})".format(len(tpe.of))

            out = [(name.toUnionTag().str(), uniontype), (name.toUnionOffset().str(), offsettype)]
            for i, x in enumerate(tpe.of):
                out.extend(recurse(name.toUnionData(i), x))
            return out

        # R
        elif isinstance(tpe, Record):
            out = []
            for fn, ft in tpe.of:
                out.extend(recurse(name.toRecord(fn), ft))
            return out
            
        else:
            assert False, "unexpected type object: {0}".format(tpe)

    return dict(recurse(ArrayName(prefix, delimiter=delimiter), tpe))

def arrays2type(arrays, prefix, delimiter="-"):
    return columns2type(dict((n, a.dtype) for n, a in arrays.items()), prefix)

def columns2type(cols, prefix, delimiter="-"):
    def recurse(cols, name):
        # P
        if all(n.isPrimitive for n, d in cols) and len(cols) == 1:
            (n, d), = cols
            out = withrepr(Primitive(d), copy=True)
            out.column = name.str()
            return out

        # L
        elif all(n.isListOffset or n.isListData for n, d in cols):
            assert sum(1 for n, d in cols if n.isListOffset) == 1
            out = List(recurse([(n.drop(), d) for n, d in cols if n.isListData], name.toListData()))
            out.column = name.toListOffset().str()
            return out

        # U
        elif all(n.isUnionTag or n.isUnionOffset or n.isUnionData for n, d in cols):
            assert sum(1 for n, d in cols if n.isUnionTag) == 1
            assert sum(1 for n, d in cols if n.isUnionOffset) == 1

            possibilities = {}
            for n, d in cols:
                if n.isUnionData:
                    if n.tagnum not in possibilities:
                        possibilities[n.tagnum] = []
                    possibilities[n.tagnum].append((n.drop(), d))

            assert list(possibilities.keys()) == list(range(len(possibilities)))

            for tagnum, cols in possibilities.items():
                possibilities[tagnum] = recurse(cols, name.toUnionData(tagnum))

            out = Union(*(tpe for tagnum, tpe in sorted(possibilities.items())))
            out.column = name.toUnionTag().str()
            out.column2 = name.toUnionOffset().str()
            return out

        # R
        elif all(n.isRecord for n, d in cols):
            fields = {}
            for n, d in cols:
                if n.fieldname not in fields:
                    fields[n.fieldname] = []
                fields[n.fieldname].append((n.drop(), d))

            for fieldname, cols in fields.items():
                fields[fieldname] = recurse(cols, name.toRecord(fieldname))

            out = Record.frompairs(fields.items())
            out.column = None
            return out

        else:
            raise TypeDefinitionError("unexpected set of columns: {0}".format(", ".join(n.str(prefix="") for n, d in cols)))
        
    parsed = [(ArrayName.parse(n, prefix, delimiter=delimiter), d) for n, d in cols.items()]
    return recurse([(n, d) for n, d in parsed if n is not None], ArrayName(prefix, delimiter=delimiter))
