import math
import numbers
from functools import reduce

import numpy

from plour.typesystem.defs import Optional
from plour.typesystem.defs import Type
from plour.typesystem.defs import TypeDefinitionError
from plour.typesystem.lrup import List
from plour.typesystem.lrup import Record
from plour.typesystem import np

class Intermediate(Type):
    def __init__(self, optional):
        self._optional = optional

    @property
    def optional(self):
        return self._optional

    @property
    def concrete(self):
        raise NotImplementedError

class Unknown(Intermediate):
    @property
    def concrete(self):
        raise TypeDefinitionError("could not resolve a type (some fields or list elements are all None or all lists at some level are empty)")
    
class Boolean(Intermediate):
    @property
    def concrete(self):
        if self.optional:
            return Optional(np.boolean)
        else:
            return np.boolean

class Number(Intermediate):
    def __init__(self, min, max, whole, real, optional):
        self._min = min
        self._max = max
        self._whole = whole
        self._real = real
        super(Number, self).__init__(optional)

    @property
    def min(self):
        return self._min

    @property
    def max(self):
        return self._max

    @property
    def whole(self):
        return self._whole

    @property
    def real(self):
        return self._real

    @property
    def optional(self):
        return self._optional

    @property
    def concrete(self):
        if self.whole:
            if self.min >= 0:
                if self.max <= numpy.iinfo(numpy.uint8).max:
                    return Optional(np.uint8) if optional else np.uint8
                elif self.max <= numpy.iinfo(numpy.uint16).max:
                    return Optional(np.uint16) if optional else np.uint16
                elif self.max <= numpy.iinfo(numpy.uint32).max:
                    return Optional(np.uint32) if optional else np.uint32
                elif self.max <= numpy.iinfo(numpy.uint64).max:
                    return Optional(np.uint64) if optional else np.uint64
                else:
                    return Optional(np.float64) if optional else np.float64
            else:
                if numpy.iinfo(numpy.int8).min <= self.min and self.max <= numpy.iinfo(numpy.int8).max:
                    return Optional(np.int8) if optional else np.int8
                elif numpy.iinfo(numpy.int16).min <= self.min and self.max <= numpy.iinfo(numpy.int16).max:
                    return Optional(np.int16) if optional else np.int16
                elif numpy.iinfo(numpy.int32).min <= self.min and self.max <= numpy.iinfo(numpy.int32).max:
                    return Optional(np.int32) if optional else np.int32
                elif numpy.iinfo(numpy.int64).min <= self.min and self.max <= numpy.iinfo(numpy.int64).max:
                    return Optional(np.int64) if optional else np.int64
                else:
                    return Optional(np.float64) if optional else np.float64
        elif self.real:
            return Optional(np.float64) if optional else np.float64
        else:
            return Optional(np.complex128) if optional else np.complex128

class IntermediateList(List, Intermediate):
    def __init__(self, items, optional):
        List.__init__(self, items)
        Intermediate.__init__(self, optional)

    @property
    def concrete(self):
        if self.optional:
            return Optional(List(self.items))
        else:
            return List(self.items)

class IntermediateRecord(Record, Intermediate):
    def __init__(self, fields, optional):
        Record.__init__(self, **fields)
        Intermediate.__init__(self, optional)

    @property
    def concrete(self):
        if self.optional:
            return Optional(Record(**dict(self.fields)))
        else:
            return Record(**dict(self.fields))

def heterogeneous(types):
    if len(types) == 0 or all(isinstance(x, Unknown) for x in types):
        if any(x.optional for x in types):
            return Unknown(True)
        else:
            return Unknown(False)

    elif all(isinstance(x, (Unknown, Boolean)) for x in types):
        if any(x.optional for x in types):
            return Boolean(True)
        else:
            return Boolean(False)

    elif all(isinstance(x, (Unknown, Number)) for x in types):
        return Number(min(x.min for x in types if isinstance(x, Number)),
                      max(x.max for x in types if isinstance(x, Number)),
                      all(x.whole for x in types if isinstance(x, Number)),
                      all(x.real for x in types if isinstance(x, Number)),
                      any(x.optional for x in types))

    elif all(isinstance(x, (Unknown, IntermediateList)) for x in types):
        return IntermediateList(homogeneous([x.items for x in types if isinstance(x, IntermediateList)]),
                                any(x.optional for x in types))

    elif all(isinstance(x, (Unknown, IntermediateRecord)) for x in types):
        fields = {}
        for n in reduce(lambda x, y: x.union(y), (set(x.fields) for x in types if isinstance(x, IntermediateRecord)), set()):
            fields[n] = homogeneous([x.fields.get(n, optional) for x in types if isinstance(x, IntermediateRecord)])
        return IntermediateRecord(fields, any(x.optional for x in types))

    else:
        raise TypeDefinitionError("unable to find a common type among the following:\n    {0}".format("\n    ".join(map(repr, types))))

def infer(obj):
    def recurse(obj):
        if obj is None:
            return Unknown(True)
        elif obj is False or obj is True:
            return Boolean(False)
        elif isinstance(obj, numbers.Integral):
            return Number(int(obj), int(obj), True, True, False)
        elif isinstance(obj, numbers.Real):
            return Number(float(obj), float(obj), False, True, False)
        elif isinstance(obj, numbers.Complex):
            return Number(float("-inf"), float("inf"), False, False, False)
        elif isinstance(obj, dict):
            return IntermediateRecord(**dict((n, firstpass(v)) for n, v in obj.items()))
        else:
            try:
                copy = list(obj)
            except TypeError:
                return IntermediateRecord(dict((n, firstpass(getattr(copy, n))) for n in dir(copy) if not n.startswith("_")))
            else:
                return IntermediateList(homogeneous([firstpass(x) for x in obj]))

    return recurse(obj).concrete
