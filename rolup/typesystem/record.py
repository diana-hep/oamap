import re

from rolup.util import *
from rolup.typesystem.type import Type

class Record(Type):
    @staticmethod
    def fromfields(self, fields):
        out = Record()
        out.of = fields
        return out

    def __init__(self, *positional, **named):
        self.of = [(repr(i), x) for i, x in enumerate(positional)] + sorted(named.items())
        super(Record, self).__init__()

    def has(self, field):
        for fn, ft in self.of:
            if fn == field:
                return True
        return False

    def field(self, field):
        if isinstance(field, int):
            field = repr(field)
        for fn, ft in self.of:
            if fn == field:
                return ft
        raise KeyError("no field named \"{0}\"".format(field))

    _checkPositional = re.compile("^[1-9][0-9]*$")

    @property
    def args(self):
        return tuple(ft for fn, ft in self.of if self._checkPositional.match(fn) is not None)

    @property
    def kwds(self):
        return dict((fn, ft) for fn, ft in self.of if self._checkPositional.match(fn) is None)

    def __contains__(self, element):
        if isinstance(element, dict):
            for fn, ft in self.of:
                if fn not in element or element[fn] not in ft:
                    return False
            return True

        else:
            for fn, ft in self.of:
                if not hasattr(element, fn) or getattr(element, fn) not in ft:
                    return False
            return True

    def issubtype(self, supertype):
        if isinstance(supertype, Record):
            for fn, ft in supertype.of:
                if not self.has(fn) or not self.field(fn).issubtype(supertype.field(fn)):
                    return False
            return True
        else:
            return False

    def toJson(self):
        return {"record": [{fn: ft.toJson()} for fn, ft in self.of]}
