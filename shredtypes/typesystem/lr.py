import re

from shredtypes.typesystem.defs import *

class Primitive(Type):
    def __init__(self, dtype, nullable=False, label=None, runtime=None, repr=None):
        self._dtype = dtype
        super(Primitive, self).__init__(nullable, label, runtime, repr)

    @property
    def dtype(self):
        return self._dtype

    @property
    def params(self):
        return (self._dtype,)

    def _repr_memo(self, memo):
        if self._repr is not None:
            return self._repr
        out = self._update_memo(memo)
        if out is not None:
            return repr(out)
        else:
            params = repr(self._dtype)
            if self.label is not None:
                params += ", label={0}".format(repr(self.label))
            out = "Primitive({0})".format(params)
            if self.nullable:
                return "nullable({0})".format(out)
            else:
                return out

    def __contains__(self, other):
        if other.__class__ == Primitive:
            if self._dtype.kind == "c":
                if other._dtype.kind == "i" or other._dtype.kind == "u":
                    return True
                elif other._dtype.kind == "c" or other._dtype.kind == "f":
                    return other._dtype.itemsize <= self._dtype.itemsize
                else:
                    return False

            elif self._dtype.kind == "f":
                if other._dtype.kind == "i" or other._dtype.kind == "u":
                    return True
                elif other._dtype.kind == "f":
                    return other._dtype.itemsize <= self._dtype.itemsize
                else:
                    return False

            elif self._dtype.kind == "i":
                if other._dtype.kind == "i":
                    return other._dtype.itemsize <= self._dtype.itemsize
                elif other._dtype.kind == "u":
                    return other._dtype.itemsize <= self._dtype.itemsize - 0.125
                else:
                    return False

            elif self._dtype.kind == "u":
                if other._dtype.kind == "u":
                    return other._dtype.itemsize <= self._dtype.itemsize
                else:
                    return False

            else:
                return False

        elif isinstance(other, complex):
            return self._dtype.kind == "c"

        elif isinstance(other, float):
            return self._dtype.kind == "c" or self._dtype.kind == "f"

        elif isinstance(other, int):
            if self._dtype.kind == "c" or self._dtype.kind == "f":
                return True

            elif self._dtype.kind == "i":
                bits = self._dtype.itemsize * 8 - 1
                return -2**bits <= other < 2**bits

            elif self._dtype.kind == "u":
                bits = self._dtype.itemsize * 8
                return 0 <= other < 2**bits

            else:
                return False

        elif hasattr(other, "dtype"):
            return self.__contains__(Primitive(other.dtype))

        else:
            return False

class List(Type):
    def __init__(self, items, nullable=False, label=None, runtime=None, repr=None):
        self._items = items
        super(List, self).__init__(nullable, label, runtime, repr)

    @property
    def items(self):
        return self._items

    @property
    def params(self):
        return (self._items,)

    @property
    def children(self):
        return (self._items,)

    def resolve(self, labelstolinks):
        if self._items in labelstolinks:
            self._items = labelstolinks[self._items]

    def _repr_memo(self, memo):
        if self._repr is not None:
            return self._repr
        out = self._update_memo(memo)
        if out is not None:
            return repr(out)
        else:
            if isinstance(self._items, Type):
                params = self._items._repr_memo(memo)
            else:
                params = repr(self._items)
            if self.label is not None:
                params += ", label={0}".format(repr(self.label))
            out = "List({0})".format(params)
            if self.nullable:
                return "nullable({0})".format(out)
            else:
                return out

    def __contains__(self, other):
        if other.__class__ == List:
            return other._items in self._items

        else:
            try:
                return all(x in self._dtype for x in other)
            except TypeError:
                return False
            
class Record(Type):
    def __init__(self, fields, nullable=False, label=None, runtime=None, repr=None):
        for field in fields:
            if re.match(self.identifier, field) is None:
                raise ValueError("field names must match [a-zA-Z_][0-9a-zA-Z_]*: {0}".format(field))
        self._fields = fields
        super(Record, self).__init__(nullable, label, runtime, repr)

    @property
    def fields(self):
        return self._fields.copy()

    @property
    def sortedfields(self):
        return [(x, self._fields[x]) for x in sorted(self._fields)]

    @property
    def params(self):
        return tuple(self.sortedfields)

    @property
    def children(self):
        return tuple(v for n, v in self.sortedfields)

    def resolve(self, labelstolinks):
        for fn, ft in self._fields.items():
            if ft in labelstolinks:
                self._fields[fn] = labelstolinks[ft]

    def _repr_memo(self, memo):
        if self._repr is not None:
            return self._repr
        out = self._update_memo(memo)
        if out is not None:
            return repr(out)
        else:
            nested = []
            for fn, ft in self.sortedfields:
                if isinstance(ft, Type):
                    nested.append(repr(fn) + ": " + ft._repr_memo(memo))
                else:
                    nested.append(repr(fn) + ": " + repr(ft))
            params = "{" + ", ".join(nested) + "}"
            if self.label is not None:
                params += ", label={0}".format(repr(self.label))
            out = "Record({0})".format(params)
            if self.nullable:
                return "nullable({0})".format(out)
            else:
                return out

    def __contains__(self, other):
        if other.__class__ == Record:
            for fn, ft in self._fields.items():
                if fn not in other._fields or other._fields[fn] not in ft:
                    return False
            return True

        elif isinstance(other, dict):
            for fn, ft in self._fields.items():
                if not fn in other or other[fn] not in ft:
                    return False
            return True

        else:
            for fn, ft in self._fields.items():
                if not hasattr(other, fn) or getattr(other, fn) not in ft:
                    return False
            return True
