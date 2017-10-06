#!/usr/bin/env python

# Copyright (c) 2017, DIANA-HEP
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# 
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# 
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import numbers
from collections import OrderedDict

import numpy

from arrowed.schema import *

def inferschema(obj):
    class Intermediate(object):
        def __init__(self, size, missing):
            self.size = size
            self.missing = missing

        def copy(self, size, missing):
            return self.__class__(size, missing)

    class Unknown(Intermediate):
        def resolve(self):
            raise TypeError("could not resolve a type (e.g. all lists at a given level are empty)")
        
    class Boolean(Intermediate):
        def resolve(self):
            return Primitive(((self.size,), numpy.dtype(numpy.bool_)), self.missing)
        
    class Number(Intermediate):
        def __init__(self, size, missing, min, max, whole, real):
            Intermediate.__init__(self, size, missing)
            self.min = min
            self.max = max
            self.whole = whole
            self.real = real

        def copy(self, size, missing):
            return Number(size, missing, self.min, self.max, self.whole, self.real)

        def resolve(self):
            if self.whole:
                if self.min >= 0:
                    if self.max <= numpy.iinfo(numpy.uint8).max:
                        t = numpy.uint8
                    elif self.max <= numpy.iinfo(numpy.uint16).max:
                        t = numpy.uint16
                    elif self.max <= numpy.iinfo(numpy.uint32).max:
                        t = numpy.uint32
                    elif self.max <= numpy.iinfo(numpy.uint64).max:
                        t = numpy.uint64
                    else:
                        t = numpy.float64
                else:
                    if numpy.iinfo(numpy.int8).min <= self.min and self.max <= numpy.iinfo(numpy.int8).max:
                        t = numpy.int8
                    elif numpy.iinfo(numpy.int16).min <= self.min and self.max <= numpy.iinfo(numpy.int16).max:
                        t = numpy.int16
                    elif numpy.iinfo(numpy.int32).min <= self.min and self.max <= numpy.iinfo(numpy.int32).max:
                        t = numpy.int32
                    elif numpy.iinfo(numpy.int64).min <= self.min and self.max <= numpy.iinfo(numpy.int64).max:
                        t = numpy.int64
                    else:
                        t = numpy.float64

            elif self.real:
                t = numpy.float64

            else:
                t = numpy.complex128

            return Primitive(((self.size,), numpy.dtype(t)), self.missing)

    class IntermediateList(Intermediate):
        def __init__(self, size, missing, contents):
            Intermediate.__init__(self, size, missing)
            self.contents = contents

        def copy(self, size, missing):
            return IntermediateList(size, missing, self.contents)

        def resolve(self):
            return ListOffset(((self.size + 1,), numpy.dtype(numpy.int64)), self.contents.resolve(), self.missing)  # FIXME: offset arrays will someday be 32-bit

    class IntermediateRecord(Intermediate):
        def __init__(self, size, missing, contents, classname):
            Intermediate.__init__(self, size, missing)
            self.contents = contents
            self.classname = classname

        def copy(self, size, missing):
            return IntermediateRecord(size, missing, self.contents, self.classname)

        def resolve(self):
            return Record(OrderedDict((k, v.resolve()) for k, v in self.contents.items()), name=self.classname)  # FIXME: Records will someday have an optional masking array

    class IntermediateTuple(Intermediate):
        def __init__(self, size, missing, contents):
            Intermediate.__init__(self, size, missing)
            self.contents = contents

        def copy(self, size, missing):
            return IntermediateTuple(size, missing, self.contents)

        def resolve(self):
            return Tuple([x.resolve() for x in self.contents], name=self.classname)  # FIXME: Tuples will someday have an optional masking array

    class IntermediateUnion(Intermediate):
        def __init__(self, size, missing, contents):
            Intermediate.__init__(self, size, missing)
            self.contents = contents

        def copy(self, size, missing):
            return IntermediateUnion(size, missing, self.contents)

        def resolve(self):
            return UnionDense(((self.size,), numpy.dtype(numpy.int8)), [x.resolve() for x in self.contents], self.missing)

    def unify2(x, y):
        size = x.size + y.size
        missing = x.missing or y.missing

        if isinstance(x, Unknown) and isinstance(y, Unknown):
            return Unknown(size, missing)

        elif isinstance(x, Unknown):
            return y.copy(size, missing)

        elif isinstance(y, Unknown):
            return x.copy(size, missing)

        elif isinstance(x, Boolean) and isinstance(y, Boolean):
            return Boolean(size, missing)

        elif isinstance(x, Number) and isinstance(y, Number):
            return Number(size, missing, min(x.min, y.min), max(x.max, y.max), x.whole and y.whole, x.real and y.real)

        elif isinstance(x, IntermediateList) and isinstance(y, IntermediateList):
            return IntermediateList(size, missing, unify2(x.contents, y.contents))

        elif isinstance(x, IntermediateRecord) and isinstance(y, IntermediateRecord) and set(x.contents.keys()) == set(y.contents.keys()):
            return IntermediateRecord(size, missing, dict((n, unify2(x.contents[n], y.contents[n])) for n in x.contents.keys()), x.classname if x.classname == y.classname else None)

        elif isinstance(x, IntermediateTuple) and isinstance(y, IntermediateTuple) and len(x.contents) == len(y.contents):
            return IntermediateTuple(size, missing, [unify2(xi, yi) for xi, yi in zip(x.contents, y.contents)])

        # x is not an IntermediateUnion because it comes directly from flattened (see below); y might be
        elif isinstance(y, IntermediateUnion):
            distinct = []
            found = False
            for yi in y.contents:
                merged = unify2(x, yi)   # doesn't recurse forever because yi is not an IntermediateUnion
                if not isinstance(merged, IntermediateUnion):
                    distinct[i] = merged
                    found = True
                    break

            if not found:
                distinct.append(x)

            return IntermediateUnion(size, missing, distinct)

        else:
            # can't be unified
            return IntermediateUnion(size, missing, [x, y])

    def unify(types):
        if len(types) == 0:
            return Unknown(0, False)

        elif len(types) == 1:
            return types[0]

        elif len(types) == 2:
            return unify2(types[0], types[1])

        else:
            # there are no IntermediateUnions in flattened
            flattened = [y for x in types if isinstance(x, IntermediateUnion) for y in x.contents] + [x for x in types if not isinstance(x, IntermediateUnion)]

            distinct = []
            for x in flattened:
                found = False

                for i, y in enumerate(distinct):
                    # x is not an IntermediateUnion because it comes directly from flattened; y might be
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
                return IntermediateUnion(sum(x.size for x in distinct), False, distinct)

    def buildintermediate(obj):
        if obj is None:
            return Unknown(1, True)

        elif obj is False or obj is True:
            return Boolean(1, False)

        elif isinstance(obj, numbers.Integral):
            return Number(1, False, int(obj), int(obj), True, True)

        elif isinstance(obj, numbers.Real):
            return Number(1, False, float(obj), float(obj), False, True)

        elif isinstance(obj, numbers.Complex):
            return Number(1, False, float("-inf"), float("inf"), False, False)

        elif isinstance(obj, dict):
            return IntermediateRecord(1, False, dict((k, buildintermediate(v)) for k, v in obj.items()), None)

        elif isinstance(obj, tuple) and hasattr(obj, "_fields"):
            # named tuple is more like a Record than a Tuple
            return IntermediateRecord(1, False, dict((n, buildintermediate(getattr(obj, n))) for n in obj._fields), obj.__class__.__name__)

        elif isinstance(obj, tuple):
            return IntermediateTuple(1, False, [buildintermediate(x) for x in obj])

        else:
            try:
                iter(obj)
            except TypeError:
                return IntermediateRecord(1, False, dict((n, buildintermediate(getattr(obj, n))) for n in dir(obj) if not n.startswith("_")), obj.__class__.__name__)
            else:
                return IntermediateList(1, False, unify([buildintermediate(x) for x in obj]))

    return buildintermediate(obj).resolve()
