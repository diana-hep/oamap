import math
import numbers
from functools import reduce

import numpy

from pquiver.typesystem.defs import Nullable
from pquiver.typesystem.defs import Type
from pquiver.typesystem.defs import TypeDefinitionError
from pquiver.typesystem.lrup import List
from pquiver.typesystem.lrup import Record
from pquiver.typesystem import np

class Intermediate(Type):
    def __init__(self, nullable):
        self._nullable = nullable

    @property
    def nullable(self):
        return self._nullable

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
        if self.nullable:
            return Nullable(np.boolean)
        else:
            return np.boolean

class Number(Intermediate):
    def __init__(self, min, max, whole, real, nullable):
        self._min = min
        self._max = max
        self._whole = whole
        self._real = real
        super(Number, self).__init__(nullable)

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
    def nullable(self):
        return self._nullable

    @property
    def concrete(self):
        if self.whole:
            if self.min >= 0:
                if self.max <= numpy.iinfo(numpy.uint8).max:
                    return Nullable(np.uint8) if nullable else np.uint8
                elif self.max <= numpy.iinfo(numpy.uint16).max:
                    return Nullable(np.uint16) if nullable else np.uint16
                elif self.max <= numpy.iinfo(numpy.uint32).max:
                    return Nullable(np.uint32) if nullable else np.uint32
                elif self.max <= numpy.iinfo(numpy.uint64).max:
                    return Nullable(np.uint64) if nullable else np.uint64
                else:
                    return Nullable(np.float64) if nullable else np.float64
            else:
                if numpy.iinfo(numpy.int8).min <= self.min and self.max <= numpy.iinfo(numpy.int8).max:
                    return Nullable(np.int8) if nullable else np.int8
                elif numpy.iinfo(numpy.int16).min <= self.min and self.max <= numpy.iinfo(numpy.int16).max:
                    return Nullable(np.int16) if nullable else np.int16
                elif numpy.iinfo(numpy.int32).min <= self.min and self.max <= numpy.iinfo(numpy.int32).max:
                    return Nullable(np.int32) if nullable else np.int32
                elif numpy.iinfo(numpy.int64).min <= self.min and self.max <= numpy.iinfo(numpy.int64).max:
                    return Nullable(np.int64) if nullable else np.int64
                else:
                    return Nullable(np.float64) if nullable else np.float64
        elif self.real:
            return Nullable(np.float64) if nullable else np.float64
        else:
            return Nullable(np.complex128) if nullable else np.complex128

class IntermediateList(List, Intermediate):
    def __init__(self, items, nullable):
        List.__init__(self, items)
        Intermediate.__init__(self, nullable)

    @property
    def concrete(self):
        if self.nullable:
            return Nullable(List(self.items))
        else:
            return List(self.items)

class IntermediateRecord(Record, Intermediate):
    def __init__(self, fields, nullable):
        Record.__init__(self, **fields)
        Intermediate.__init__(self, nullable)

    @property
    def concrete(self):
        if self.nullable:
            return Nullable(Record(**dict(self.fields)))
        else:
            return Record(**dict(self.fields))

def heterogeneous(types):
    if len(types) == 0 or all(isinstance(x, Unknown) for x in types):
        if any(x.nullable for x in types):
            return Unknown(True)
        else:
            return Unknown(False)

    elif all(isinstance(x, (Unknown, Boolean)) for x in types):
        if any(x.nullable for x in types):
            return Boolean(True)
        else:
            return Boolean(False)

    elif all(isinstance(x, (Unknown, Number)) for x in types):
        return Number(min(x.min for x in types if isinstance(x, Number)),
                      max(x.max for x in types if isinstance(x, Number)),
                      all(x.whole for x in types if isinstance(x, Number)),
                      all(x.real for x in types if isinstance(x, Number)),
                      any(x.nullable for x in types))

    elif all(isinstance(x, (Unknown, IntermediateList)) for x in types):
        return IntermediateList(homogeneous([x.items for x in types if isinstance(x, IntermediateList)]),
                                any(x.nullable for x in types))

    elif all(isinstance(x, (Unknown, IntermediateRecord)) for x in types):
        fields = {}
        for n in reduce(lambda x, y: x.union(y), (set(x.fields) for x in types if isinstance(x, IntermediateRecord)), set()):
            fields[n] = homogeneous([x.fields.get(n, nullable) for x in types if isinstance(x, IntermediateRecord)])
        return IntermediateRecord(fields, any(x.nullable for x in types))

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
