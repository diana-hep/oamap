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

import re
import numbers
import sys
import math

import numpy

import oamap.schema
from oamap.util import OrderedDict

if sys.version_info[0] > 2:
    basestring = str

################################################################ inferring schemas from data

def fromdata(obj, limit=None):
    if limit is None or (isinstance(limit, numbers.Integral) and limit >= 0):
        pass
    else:
        raise TypeError("limit must be None or a non-negative integer, not {0}".format(limit))

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

    class String(Intermediate):
        def __init__(self, nullable, utf8):
            Intermediate.__init__(self, nullable)
            self.utf8 = utf8
        def resolve(self):
            return oamap.schema.List(oamap.schema.Primitive(numpy.uint8), nullable=self.nullable, name=("UTF8String" if self.utf8 else "ByteString"))

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

        elif isinstance(x, String) and isinstance(y, String):
            return String(nullable, x.utf8 or y.utf8)

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

    def buildintermediate(obj, limit, memo):
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

        elif isinstance(obj, bytes):
            return String(False, False)

        elif isinstance(obj, basestring):
            return String(False, True)

        elif isinstance(obj, dict):
            return IntermediateRecord(False, dict((n, buildintermediate(x, limit, memo)) for n, x in obj.items()), None)

        elif isinstance(obj, tuple) and hasattr(obj, "_fields"):
            # this is a namedtuple; interpret it as a Record, rather than a Tuple
            return IntermediateRecord(False, dict((n, buildintermediate(getattr(obj, n), limit, memo)) for n in obj._fields), obj.__class__.__name__)

        elif isinstance(obj, tuple):
            return IntermediateTuple(False, [buildintermediate(x, limit, memo) for x in obj])

        else:
            try:
                limited = []
                for x in obj:
                    if limit is None or len(limited) < limit:
                        limited.append(x)
                    else:
                        break
            except TypeError:
                # not iterable, so interpret it as a Record
                return IntermediateRecord(False, dict((n, buildintermediate(getattr(obj, n), limit, memo)) for n in dir(obj) if not n.startswith("_") and not callable(getattr(obj, n))), obj.__class__.__name__)
            else:
                # iterable, so interpret it as a List
                return IntermediateList(False, unify([buildintermediate(x, None, memo) for x in obj]))

    return buildintermediate(obj, limit, set()).resolve()

################################################################ inferring schemas from a namespace

def fromnames(arraynames, prefix="object", delimiter="-"):
    def filter(arraynames, prefix):
        return [x for x in arraynames if x.startswith(prefix)]
    
    def recurse(arraynames, prefix, byname, internalpointers):
        prefixdelimiter = prefix + delimiter
        name = None
        for n in arraynames:
            if n.startswith(prefixdelimiter):
                if n[len(prefixdelimiter)] == "N":
                    match = oamap.schema.Schema._identifier.match(n[len(prefixdelimiter) + 1:])
                    if match is not None:
                        name = match.group(0)
                        break

        if name is not None:
            prefix = prefixdelimiter + "N" + name
            prefixdelimiter = prefix + delimiter
            
        mask      = prefixdelimiter + "M"
        starts    = prefixdelimiter + "B"
        stops     = prefixdelimiter + "E"
        content   = prefixdelimiter + "L"
        tags      = prefixdelimiter + "T"
        offsets   = prefixdelimiter + "O"
        uniondata = prefixdelimiter + "U"
        field     = prefixdelimiter + "F"
        positions = prefixdelimiter + "P"
        external  = prefixdelimiter + "X"
        primitive = prefixdelimiter + "D"

        nullable = mask in arraynames
        if not nullable:
            mask = None

        if starts in arraynames and stops in arraynames:
            byname[prefix] = None
            byname[prefix] = oamap.schema.List(recurse(filter(arraynames, content), content, byname, internalpointers), nullable=nullable, starts=None, stops=None, mask=None, name=name, doc=None)

        elif tags in arraynames:
            possibilities = []
            while True:
                possibility = uniondata + repr(len(possibilities))
                if any(x.startswith(possibility) for x in arraynames):
                    possibilities.append(possibility)
                else:
                    break
            byname[prefix] = None
            byname[prefix] = oamap.schema.Union([recurse(filter(arraynames, x), x, byname, internalpointers) for x in possibilities], nullable=nullable, tags=None, offsets=None, mask=None, name=name, doc=None)

        elif any(x.startswith(field) for x in arraynames):
            pattern = re.compile("^" + field + "(" + oamap.schema.Schema._identifier.pattern + ")")
            fields = {}
            for x in arraynames:
                matches = pattern.match(x)
                if matches is not None:
                    if matches.group(1) not in fields:
                        fields[matches.group(1)] = []
                    fields[matches.group(1)].append(x)

            types = []
            while True:
                tpe = field + repr(len(types))
                if any(x.startswith(tpe) for x in arraynames):
                    types.append(tpe)
                else:
                    break

            if len(fields) >= 0 and len(types) == 0:
                byname[prefix] = oamap.schema.Record(oamap.schema.OrderedDict([(n, recurse(fields[n], field + n, byname, internalpointers)) for n in sorted(fields)]), nullable=nullable, mask=None, name=name, doc=None)
            elif len(fields) == 0 and len(types) > 0:
                byname[prefix] = oamap.schema.Tuple([recurse(filter(arraynames, n), n, byname, internalpointers) for n in types], nullable=nullable, mask=None, name=name, doc=None)
            else:
                raise KeyError("ambiguous set of array names: may be Record or Tuple at {0}".format(repr(prefix)))

        elif any(x.startswith(positions) for x in arraynames):
            if positions in arraynames:
                # external
                byname2 = {}
                internalpointers2 = []
                target = finalize(recurse(filter(arraynames, external), external, byname2, internalpointers2), byname2, internalpointers2)
                byname[prefix] = oamap.schema.Pointer(target, nullable=nullable, positions=None, mask=None, name=name, doc=None)

            else:
                # internal
                matches = [x[len(positions) + 1:] for x in arraynames if x.startswith(positions)]
                if len(matches) != 1:
                    raise KeyError("ambiguous set of array names: more than one internal Pointer at {0}".format(repr(prefix)))
                target = None   # placeholder! see finalize
                byname[prefix] = oamap.schema.Pointer(target, nullable=nullable, positions=None, mask=None, name=name, doc=None)
                internalpointers.append((byname[prefix], matches[0]))

        elif any(x.startswith(primitive) for x in arraynames):
            matches = [x[len(primitive) - 1:] for x in arraynames if x.startswith(primitive)]
            if len(matches) != 1:
                raise KeyError("ambiguous set of array names: more than one Primitive at {0}".format(repr(prefix)))
            dtype = oamap.schema.Primitive._str2dtype(matches[0], delimiter)
            byname[prefix] = oamap.schema.Primitive(dtype, nullable=nullable, data=None, mask=None, name=name, doc=None)

        else:
            raise KeyError("missing array names: nothing found as {0} contents".format(repr(prefix)))

        return byname[prefix]

    def finalize(out, byname, internalpointers):
        for pointer, targetname in internalpointers:
            if targetname in byname:
                pointer.target = byname[targetname]
            else:
                raise KeyError("Pointer's internal target is {0}, but there is no object with that prefix".format(repr(targetname)))
        return out

    byname = {}
    internalpointers = []
    return finalize(recurse(filter(arraynames, prefix), prefix, byname, internalpointers), byname, internalpointers)
