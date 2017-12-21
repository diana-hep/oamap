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

import numpy

import oamap.schema
from oamap.schema import OrderedDict

################################################################ inferring schemas from data

def fromdata(obj, limititems=None):
    if limititems is None or (isinstance(limititems, numbers.Integral) and limititems >= 0):
        pass
    else:
        raise TypeError("limititems must be None or a non-negative integer, not {0}".format(limititems))

    class Intermediate(object):
        def __init__(self, nullable):
            self.nullable = nullable

    class Unknown(Intermediate):
        def resolve(self):
            raise TypeError("could not resolve a type (e.g. all examples of a List-typed attribute are empty, can't determine its content type)")

    class Boolean(Intermediate):
        def resolve(self):
            return oamap.schema.Primitive(numpy.dtype(numpy.bool_), nullable=self.nullable)

    class Number(Intermediate):
        max_uint8 = numpy.iinfo(numpy.uint8).max
        max_uint16 = numpy.iinfo(numpy.uint16).max
        max_uint32 = numpy.iinfo(numpy.uint32).max
        max_uint64 = numpy.iinfo(numpy.uint64).max
        min_int8 = numpy.iinfo(numpy.int8).min
        max_int8 = numpy.iinfo(numpy.int8).max
        min_int16 = numpy.iinfo(numpy.int16).min
        max_int16 = numpy.iinfo(numpy.int16).max
        min_int32 = numpy.iinfo(numpy.int32).min
        max_int32 = numpy.iinfo(numpy.int32).max
        min_int64 = numpy.iinfo(numpy.int64).min
        max_int64 = numpy.iinfo(numpy.int64).max
        def __init__(self, nullable, min, max, whole, real):
            Intermediate.__init__(self, nullable)
            self.min = min
            self.max = max
            self.whole = whole
            self.real = real
        def resolve(self):
            if self.whole:
                if self.min >= 0:
                    if self.max <= self.max_uint8:
                        t = numpy.uint8
                    elif self.max <= self.max_uint16:
                        t = numpy.uint16
                    elif self.max <= self.max_uint32:
                        t = numpy.uint32
                    elif self.max <= self.max_uint64:
                        t = numpy.uint64
                    else:
                        t = numpy.float64
                else:
                    if self.min_int8 <= self.min and self.max <= self.max_int8:
                        t = numpy.int8
                    elif self.min_int16 <= self.min and self.max <= self.max_int16:
                        t = numpy.int16
                    elif self.min_int32 <= self.min and self.max <= self.max_int32:
                        t = numpy.int32
                    elif self.min_int64 <= self.min and self.max <= self.max_int64:
                        t = numpy.int64
                    else:
                        t = numpy.float64
            elif self.real:
                t = numpy.float64
            else:
                t = numpy.complex128
            return oamap.schema.Primitive(numpy.dtype(t), nullable=self.nullable)

    class IntermediateList(Intermediate):
        def __init__(self, nullable, content):
            Intermediate.__init__(self, nullable)
            self.content = content
        def resolve(self):
            return oamap.schema.List(self.content.resolve(), nullable=self.nullable)

    class IntermediateRecord(Intermediate):
        def __init__(self, nullable, fields, name):
            Intermediate.__init__(self, nullable)
            self.fields = fields
            self.name = name
        def resolve(self):
            return oamap.schema.Record(dict((n, x.resolve()) for n, x in self.fields.items()), nullable=self.nullable, name=self.name)

    class IntermediateTuple(Intermediate):
        def __init__(self, nullable, types):
            Intermediate.__init__(self, nullable)
            self.types = types
        def resolve(self):
            return oamap.schema.Tuple([x.resolve() for x in self.types], nullable=self.nullable)

    # Unions are special for type-inference
    class IntermediateUnion(Intermediate):
        def __init__(self, nullable, possibilities):
            Intermediate.__init__(self, nullable)
            self.possibilities = possibilities
        def resolve(self):
            return oamap.schema.Union([x.resolve() for x in self.possibilities], nullable=self.nullable)

    # no Pointers in type-inference (we'd have to keep a big map of *everything*!)

    def flatten(possibilities):
        return [y for x in possibilities if isinstance(x, IntermediateUnion) for y in x.possibilities] + [x for x in possibilities if not isinstance(x, IntermediateUnion)]

    def unify2(x, y):
        nullable = x.nullable or y.nullable

        if isinstance(x, Unknown) and isinstance(y, Unknown):
            return Unknown(nullable)

        elif isinstance(x, Unknown):
            y.nullable = nullable
            return y

        elif isinstance(y, Unknown):
            x.nullable = nullable
            return x

        elif isinstance(x, Boolean) and isinstance(y, Boolean):
            return Boolean(nullable)

        elif isinstance(x, Number) and isinstance(y, Number):
            return Number(nullable, min(x.min, y.min), max(x.max, y.max), x.whole and y.whole, x.real and y.real)

        elif isinstance(x, IntermediateList) and isinstance(y, IntermediateList):
            return IntermediateList(nullable, unify2(x.content, y.content))

        elif isinstance(x, IntermediateRecord) and isinstance(y, IntermediateRecord) and set(x.fields) == set(y.fields) and (x.name is None or y.name is None or x.name == y.name):
            return IntermediateRecord(nullable, dict((n, unify2(x.fields[n], y.fields[n])) for n in x.fields), name=(y.name if x.name is None else x.name))

        elif isinstance(x, IntermediateTuple) and isinstance(y, IntermediateTuple) and len(x.types) == len(y.types):
            return IntermediateTuple(nullable, [unify2(xi, yi) for xi, yi in zip(x.types, y.types)])

        elif isinstance(x, IntermediateUnion) and isinstance(y, IntermediateUnion):
            return unify(x.possibilities + y.possibilities)

        elif isinstance(x, IntermediateUnion):
            return unify(x.possibilities + [y])

        elif isinstance(y, IntermediateUnion):
            return unify([x] + y.possibilities)

        else:
            # can't be unified
            return IntermediateUnion(nullable, flatten([x, y]))

    def unify(possibilities):
        if len(possibilities) == 0:
            return Unknown(False)

        elif len(possibilities) == 1:
            return possibilities[0]

        elif len(possibilities) == 2:
            return unify2(possibilities[0], possibilities[1])

        else:
            distinct = []
            for x in flatten(possibilities):
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
                return IntermediateUnion(False, flatten(distinct))

    def buildintermediate(obj, limititems, memo):
        if id(obj) in memo:
            raise ValueError("cyclic reference in Python object at {0} (Pointer types cannot be inferred)".format(obj))

        # by copying, rather than modifying in-place (memo.add), we find cyclic references, rather than DAGs
        memo = memo.union(set([id(obj)]))

        if obj is None:
            return Unknown(True)

        elif obj is False or obj is True:
            return Boolean(False)

        elif isinstance(obj, numbers.Integral):
            return Number(False, int(obj), int(obj), True, True)

        elif isinstance(obj, numbers.Real):
            return Number(False, float(obj), float(obj), False, True)

        elif isinstance(obj, numbers.Complex):
            return Number(False, float("-inf"), float("inf"), False, False)

        elif isinstance(obj, dict):
            return IntermediateRecord(False, dict((n, buildintermediate(x, limititems, memo)) for n, x in obj.items()), None)

        elif isinstance(obj, tuple) and hasattr("_fields"):
            # this is a namedtuple; interpret it as a Record, rather than a Tuple
            return IntermediateRecord(False, dict((n, buildintermediate(getattr(obj, n), limititems, memo)) for n in obj._fields), obj.__class__.__name__)

        elif isinstance(obj, tuple):
            return IntermediateTuple(False, [buildintermediate(x, limititems, memo) for x in obj])

        else:
            try:
                limited = []
                for x in obj:
                    if limititems is None or len(limited) < limititems:
                        limited.append(x)
                    else:
                        break
            except TypeError:
                # not iterable, so interpret it as a Record
                return IntermediateRecord(False, dict((n, buildintermediate(getattr(obj, n), limititems, memo)) for n in dir(obj) if not n.startswith("_") and not callable(getattr(obj, n))), obj.__class__.__name__)
            else:
                # iterable, so interpret it as a List
                return IntermediateList(False, unify([buildintermediate(x, None, memo) for x in obj]))

    return buildintermediate(obj, limititems, set()).resolve()

################################################################ inferring schemas from a namespace

