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

import math
import numbers
from functools import reduce
from collections import namedtuple

import numpy

from plur.util import *
from plur.types import *
from plur.types.type import Type
from plur.types.columns import type2columns
from plur.types.arrayname import ArrayName
from plur.generate.fillmemory import FillableColumnInMemory

def infertype(obj):
    class Intermediate(Type):
        def resolve(self):
            raise NotImplementedError

    class Unknown(Intermediate):
        def resolve(self):
            raise TypeDefinitionError("could not resolve a type (e.g. all lists at a given level are empty)")

    class Boolean(Intermediate):
        def resolve(self):
            return boolean

    class Number(Intermediate):
        def __init__(self, min, max, whole, real):
            self.min = min
            self.max = max
            self.whole = whole
            self.real = real
            Intermediate.__init__(self)

        def resolve(self):
            if self.whole:
                if self.min >= 0:
                    if self.max <= numpy.iinfo(numpy.uint8).max:
                        return uint8
                    elif self.max <= numpy.iinfo(numpy.uint16).max:
                        return uint16
                    elif self.max <= numpy.iinfo(numpy.uint32).max:
                        return uint32
                    elif self.max <= numpy.iinfo(numpy.uint64).max:
                        return uint64

                else:
                    if numpy.iinfo(numpy.int8).min <= self.min and self.max <= numpy.iinfo(numpy.int8).max:
                        return int8
                    elif numpy.iinfo(numpy.int16).min <= self.min and self.max <= numpy.iinfo(numpy.int16).max:
                        return int16
                    elif numpy.iinfo(numpy.int32).min <= self.min and self.max <= numpy.iinfo(numpy.int32).max:
                        return int32
                    elif numpy.iinfo(numpy.int64).min <= self.min and self.max <= numpy.iinfo(numpy.int64).max:
                        return int64
                    else:
                        return float64

            elif self.real:
                return float64

            else:
                return complex128

    class IntermediateList(List, Intermediate):
        def __init__(self, of):
            List.__init__(self, of)
            Intermediate.__init__(self)

        def resolve(self):
            return List(self.of)

    class IntermediateRecord(Record, Intermediate):
        def __init__(self, named):
            Record.__init__(self, **named)
            Intermediate.__init__(self)

        def resolve(self):
            return Record.frompairs(self.of)

    def unify(types):
        if len(types) == 0 or all(isinstance(x, Unknown) for x in types):
            return Unknown()

        elif all(isinstance(x, (Unknown, Boolean)) for x in types):
            return Boolean()

        elif all(isinstance(x, (Unknown, Number)) for x in types):
            return Number(min(x.min for x in types if isinstance(x, Number)),
                          max(x.max for x in types if isinstance(x, Number)),
                          all(x.whole for x in types if isinstance(x, Number)),
                          all(x.real for x in types if isinstance(x, Number)))

        elif all(isinstance(x, (Unknown, IntermediateList)) for x in types):
            return IntermediateList(unify([x.of for x in types if isinstance(x, IntermediateList)]))

        elif all(isinstance(x, (Unknown, IntermediateRecord)) for x in types):
            fields = {}
            for n in reduce(lambda x, y: x.union(y), (set(x.of) for x in types if isinstance(x, IntermediateRecord)), set()):
                fields[n] = unify([x.of.get(n, Unknown()) for x in types if isinstance(x, IntermediateRecord)])
            return IntermediateRecord(fields)

        else:
            raise TypeDefinitionError("unable to find a common type among the following:\n    {0}".format("\n    ".join(map(repr, types))))

    def buildintermediate(obj):
        if obj is False or obj is True:
            return Boolean()

        elif isinstance(obj, numbers.Integral):
            return Number(int(obj), int(obj), True, True)

        elif isinstance(obj, numbers.Real):
            return Number(float(obj), float(obj), False, True)

        elif isinstance(obj, numbers.Complex):
            return Number(float("-inf"), float("inf"), False, False)
        
        elif isinstance(obj, dict):
            return IntermediateRecord(dict((n, buildintermediate(v)) for n, v in obj.items()))

        elif isinstance(obj, tuple) and hasattr(obj, "_fields"):
            return IntermediateRecord(dict((n, buildintermediate(getattr(obj, n))) for n in obj._fields))

        else:
            try:
                iter(obj)
            except TypeError:
                return IntermediateRecord(dict((n, buildintermediate(getattr(obj, n))) for n in dir(obj) if not n.startswith("_")))
            else:
                return IntermediateList(unify([buildintermediate(x) for x in obj]))

    return buildintermediate(obj).resolve()

def convert(prefix, obj, tpe=None, fillable=FillableColumnInMemory, delimiter="-", indextype=numpy.dtype(numpy.uint64), **fillableOptions):
    if tpe is None:
        tpe = infertype(obj)

    dtypes = type2columns(tpe, prefix, delimiter=delimiter, indextype=indextype)
    fillables = dict((ArrayName.parse(n, prefix, delimiter=delimiter), fillable(n, d, **fillableOptions)) for n, d in dtypes.items())

    last_list_offset = {}
    last_union_offset = {}

    def recurse(obj, tpe, name):
        if isinstance(tpe, Primitive):
            fillables[name].fill(obj)

        elif isinstance(tpe, List):
            nameoffset = name.toListOffset()
            namedata = name.toListData()

            if nameoffset not in last_list_offset:
                last_list_offset[nameoffset] = 0
            last_list_offset[nameoffset] += len(obj)

            fillables[nameoffset].fill(last_list_offset[nameoffset])
            
            for x in obj:
                recurse(x, tpe.of, namedata)

        elif isinstance(tpe, Union):
            t = infertype(obj)   # can be expensive!
            tag = None
            for i, possibility in enumerate(tpe.of):
                if t.issubtype(possibility):
                    tag = i
                    break
            assert tag is not None

            nametag = name.toUnionTag()
            nameoffset = name.toUnionOffset()
            namedata = name.toUnionData(tag)

            if namedata not in last_union_offset:
                last_union_offset[namedata] = 0
            last_union_offset[namedata] += 1

            fillables[nametag].fill(tag)
            fillables[nameoffset].fill(last_union_offset[namedata])

            recurse(obj, tpe.of[tag], namedata)

        elif isinstance(tpe, Record):
            if isinstance(obj, dict):
                for fn, ft in tpe.of:
                    recurse(obj[fn], ft, name.toRecord(fn))

            else:
                for fn, ft in tpe.of:
                    recurse(getattr(obj, fn), ft, name.toRecord(fn))

        else:
            assert False, "unexpected type object: {0}".format(tpe)

    recurse(obj, tpe, ArrayName(prefix, delimiter=delimiter))

    return dict((n.str(), f.finalize()) for n, f in fillables.items())
