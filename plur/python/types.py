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

import numbers
# from functools import reduce

import numpy

from plur.util import *
from plur.types import *

def infertype(obj):
    class Intermediate(Type):
        _sortorder = 0

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
                        return float64

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
            return List(self.of.resolve())

    class IntermediateRecord(Record, Intermediate):
        def __init__(self, of):
            self.of = of  # avoid Record's sorting and just maintain a dictionary
            Intermediate.__init__(self)

        def resolve(self):
            return Record(**dict((fn, ft.resolve()) for fn, ft in self.of.items()))

    class IntermediateUnion(Union, Intermediate):
        def __init__(self, of):
            self.of = of  # avoid Union's flattening, which would be premature here
            Intermediate.__init__(self)

        def resolve(self):
            return Union(*(x.resolve() for x in self.of))

    def unify2(x, y):
        # eliminate placeholders
        if isinstance(x, Unknown):
            return y

        elif isinstance(y, Unknown):
            return x

        # P
        elif isinstance(x, Boolean) and isinstance(y, Boolean):
            return Boolean()

        elif isinstance(x, Number) and isinstance(y, Number):
            return Number(min(x.min, y.min), max(x.max, y.max), x.whole and y.whole, x.real and y.real)

        # L
        elif isinstance(x, IntermediateList) and isinstance(y, IntermediateList):
            return IntermediateList(unify2(x.of, y.of))

        # U
        elif isinstance(x, IntermediateUnion) and isinstance(y, IntermediateUnion):
            return unify(x.of + y.of)

        elif isinstance(x, IntermediateUnion):
            return unify(x.of + [y])

        elif isinstance(y, IntermediateUnion):
            return unify([x] + y.of)

        # R
        elif isinstance(x, IntermediateRecord) and isinstance(y, IntermediateRecord) and set(x.of.keys()) == set(y.of.keys()):
            return IntermediateRecord(dict((n, unify2(x.of[n], y.of[n])) for n in x.of.keys()))

        # can't be unified
        else:
            return IntermediateUnion([x, y])

    def unify(types):
        if len(types) == 0:
            return Unknown()

        elif len(types) == 1:
            return types[0]

        elif len(types) == 2:
            return unify2(types[0], types[1])

        else:
            flattened = [y for x in types if isinstance(x, IntermediateUnion) for y in x.of] + [x for x in types if not isinstance(x, IntermediateUnion)]

            distinct = []
            for x in flattened:
                found = False

                for i, y in enumerate(distinct):
                    merged = unify2(x, y)
                    if not isinstance(merged, IntermediateUnion):
                        distinct[i] = merged
                        found = True
                        break

                if not found:
                    distinct.append(x)

            if len(distinct) == 1:
                return distinct[0]
            else:
                return IntermediateUnion(distinct)

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

