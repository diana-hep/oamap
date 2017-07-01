import re

from rolup.typesystem.defs import Type
from rolup.typesystem.defs import TypeDefinitionError
from rolup.typesystem import naming

class List(Type):
    def __init__(self, items):
        self._items = items
        super(List, self).__init__()

    @property
    def items(self):
        return self._items

    @property
    def args(self):
        return (self._items,)

    @property
    def children(self):
        return (self._items,)

    def __contains__(self, element):
        try:
            lst = list(element)
        except TypeError:
            return False
        else:
            return all(x in self._items for x in lst)

    def issubtype(self, supertype):
        # Lists are covariant
        return supertype.generic == "List" and self._items.issubtype(supertype._items)

class Record(Type):
    @staticmethod
    def ordered(self, fields):
        out = Record()
        out._fields = fields
        return out

    def __init__(self, positional, **named):
        for field in positional + tuple(named):
            if re.match(naming.identifier, field) is None:
                raise TypeDefinitionError("field name doesn't match /{0}/: \"{1}\"".format(naming.identifier.pattern, field))
        self._fields = tuple((i, t) for i, t in positional) + tuple((n, named[n]) for n in sorted(named))
        super(Record, self).__init__()

    def has(self, name):
        for n, t in self._fields:
            if n == name:
                return True
        else:
            return False

    def field(self, name):
        for n, t in self._fields:
            if n == name:
                return t
        raise KeyError("no field named \"{0}\"".format(name))

    @property
    def fields(self):
        return self._fields

    @property
    def args(self):
        return tuple(t for n, t in self._fields if isinstance(n, int))

    @property
    def kwds(self):
        return dict((n, t) for n, t in self._fields if not isinstance(n, int))

    @property
    def children(self):
        return tuple(t for n, t in self._fields)

    def __contains__(self, element):
        if isinstance(element, dict):
            for n, t in self._fields:
                if n not in element or element[n] not in t:
                    return False
            return True

        else:
            for n, t in self._fields:
                if not hasattr(element, n) or getattr(element, n) not in t:
                    return False
            return True

    def issubtype(self, supertype):
        if supertype.generic == "Record":
            for n, t in supertype._fields:
                if not self.has(n) or not self.field(n).issubtype(supertype.field(n)):
                    return False
            return True
        else:
            return False
