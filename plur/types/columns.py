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
from plur.types.primitive import Primitive # P
from plur.types.list import List           # L
from plur.types.union import Union         # U
from plur.types.record import Record       # R
from plur.types.primitive import withrepr
from plur.types.arrayname import ArrayName

def type2columns(tpe, prefix, delimiter="-", indextype=numpy.dtype(numpy.uint64)):
    def recurse(name, tpe):
        if tpe.rtname is not None:
            raise NotImplementedError

        # P
        if isinstance(tpe, Primitive):
            return [(name.str(), tpe.of)]

        # L
        elif isinstance(tpe, List):
            return [(name.toListOffset().str(), indextype)] + recurse(name.toListData(), tpe.of)

        # U
        elif isinstance(tpe, Union):
            out = [(name.toUnionTag().str(), indextype), (name.toUnionOffset().str(), indextype)]
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

def columns2type(cols, prefix, delimiter="-"):
    def recurse(cols):
        # P
        if all(n.isPrimitive for n, d in cols) and len(cols) == 1:
            (n, d), = cols
            return withrepr(Primitive(d))

        # L
        elif all(n.isListOffset or n.isListData for n, d in cols):
            assert sum(1 for n, d in cols if n.isListOffset) == 1
            return List(recurse([(n.drop(), d) for n, d in cols if n.isListData]))

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
                possibilities[tagnum] = recurse(cols)

            return Union(*(tpe for tagnum, tpe in sorted(possibilities.items())))

        # R
        elif all(n.isRecord for n, d in cols):
            fields = {}
            for n, d in cols:
                if n.fieldname not in fields:
                    fields[n.fieldname] = []
                fields[n.fieldname].append((n.drop(), d))

            for fieldname, cols in fields.items():
                fields[fieldname] = recurse(cols)

            return Record.frompairs(fields.items())

        else:
            raise TypeDefinitionError("unexpected set of columns: {0}".format(", ".join(n.str(prefix="") for n, d in cols)))
        
    parsed = [(ArrayName.parse(n, prefix, delimiter=delimiter), d) for n, d in cols.items()]
    return recurse([(n, d) for n, d in parsed if n is not None])
