import math
import numbers
from functools import reduce

from shredtypes.typesystem.lr import *
from shredtypes.typesystem.np import *

class Unknown(Type):
    def __init__(self, nullable):
        super(Unknown, self).__init__(repr="unknown", nullable=nullable)

unknown = Unknown(False)
hasnull = Unknown(True)

class Number(Type):
    def __init__(self, min, max, whole, real, nullable):
        self._min = min
        self._max = max
        self._whole = whole
        self._real = real
        super(Number, self).__init__(nullable=nullable)

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

    def _repr_memo(self, memo):
        return "Number(min={0}, max={1}, whole={2}, real={3}, nullable={4})".format(self._min, self._max, self._whole, self._real, self.nullable)

def homogeneous(types):
    if len(types) == 0 or all(isinstance(x, Unknown) for x in types):
        if any(x == hasnull for x in types):
            return hasnull
        else:
            return unknown

    elif all(isinstance(x, (Unknown, Number)) for x in types):
        return Number(min(x.min for x in types if isinstance(x, Number)),
                      max(x.max for x in types if isinstance(x, Number)),
                      all(x.whole for x in types if isinstance(x, Number)),
                      all(x.real for x in types if isinstance(x, Number)),
                      nullable=any(x.nullable for x in types))
    
    elif all(isinstance(x, (Unknown, List)) for x in types):
        return List(homogeneous([x.items for x in types if isinstance(x, List)]),
                    nullable=any(x.nullable for x in types))

    elif all(isinstance(x, (Unknown, Record)) for x in types):
        fields = {}
        for fn in reduce(lambda x, y: x.union(y), (set(x.fields) for x in types if isinstance(x, Record)), set()):
            fields[fn] = homogeneous([x.fields.get(fn, hasnull) for x in types if isinstance(x, Record)])
        return Record(fields, nullable=any(x.nullable for x in types))

    else:
        raise TypeError("unable to build homogeneous types in an L+R typesystem:\n    {0}".format("\n    ".join(map(repr, types))))

def infertype(obj):
    def firstpass(obj):
        if obj is None or (isinstance(obj, float) and math.isnan(obj)):
            return hasnull
        elif obj is False:
            return Number(0, 0, True, True, False)
        elif obj is True:
            return Number(1, 1, True, True, False)
        elif isinstance(obj, numbers.Integral):
            return Number(int(obj), int(obj), True, True, False)
        elif isinstance(obj, numbers.Real):
            return Number(float(obj), float(obj), False, True, False)
        elif isinstance(obj, numbers.Complex):
            return Number(float("-inf"), float("inf"), False, False, False)
        elif isinstance(obj, dict):
            return Record(dict((n, firstpass(v)) for n, v in obj.items()))
        else:
            try:
                obj = list(obj)
            except TypeError:
                return Record(dict((n, firstpass(getattr(obj, n))) for n in dir(obj) if not n.startswith("_")))
            else:
                # don't hide these TypeErrors
                return List(homogeneous([firstpass(x) for x in obj]))

    def secondpass(tpe):
        if isinstance(tpe, Unknown):
            raise TypeError("unable to resolve type (some fields are all None or lists or all empty)")
        elif isinstance(tpe, Number):
            return selecttype(tpe.min, tpe.max, tpe.whole, tpe.real, tpe.nullable)
        elif isinstance(tpe, List):
            return List(secondpass(tpe.items), nullable=tpe.nullable)
        elif isinstance(tpe, Record):
            return Record(dict((n, secondpass(v)) for n, v in tpe.fields.items()), nullable=tpe.nullable)
        else:
            return tpe

    return secondpass(firstpass(obj))
