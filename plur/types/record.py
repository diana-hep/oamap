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

import re

from plur.util import *
from plur.types.type import Type

class Record(Type):
    _sortorder = 3
    _checkPositional = re.compile("^(0|[1-9][0-9]*)$")
    _checkNamed = re.compile("^[a-zA-Z_][a-zA-Z_0-9]*$")

    @staticmethod
    def frompairs(pairs):
        out = Record(None)
        out.of = sorted(pairs)
        return out

    def __init__(self, *positional, **named):
        if len(positional) == 0 and len(named) == 0:
            raise TypeDefinitionError("record must have at least one field")
        if len(positional) > 0 and len(named) > 0:
            raise TypeDefinitionError("record fields must all be positional or all be named")
        if any(self._checkNamed.match(n) == None for n in named):
            raise TypeDefinitionError("record names must be identifiers (/{0}/)".format(self._checkNamed.pattern))

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

    @property
    def args(self):
        return tuple(ft for fn, ft in self.of if self._checkPositional.match(fn) is not None)

    @property
    def kwds(self):
        return dict((fn, ft) for fn, ft in self.of if self._checkPositional.match(fn) is None)

    @property
    def children(self):
        return tuple(ft for fn, ft in self.of)

    def __lt__(self, other):
        if isinstance(self, Record) and isinstance(other, Record) and self.rtname == other.rtname and self.rtargs == other.rtargs:
            # ensure that records with more fields go first (so they are checked for union membership first)

            if len(self.of) > len(other.of):
                return True

            elif len(self.of) < len(other.of):
                return False

            else:
                return self.of < other.of

        else:
            return super(Record, self).__lt__(other)

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
        if super(Record, self).issubtype(supertype):
            return True

        elif (isinstance(supertype, self.__class__) or isinstance(self, supertype.__class__)) and supertype.rtname == self.rtname and supertype.rtargs == self.rtargs:
            for fn, ft in supertype.of:
                if not self.has(fn) or not self.field(fn).issubtype(supertype.field(fn)):
                    return False
            return True
        else:
            return False

    def toJson(self):
        return {"record": dict((fn, ft.toJson()) for fn, ft in self.of)}

    class Fields(object):
        def __init__(self, parent):
            self.__dict__["__parent"] = parent

        def __repr__(self):
            return "<Record.Fields of {0}>".format(" ".join(n for n, t in self.__dict__["__parent"].of))

        def __getattr__(self, name):
            for n, t in self.__dict__["__parent"].of:
                if n == name:
                    return t
            raise KeyError(name)

        def __setattr__(self, name, tpe):
            for i, (n, t) in enumerate(self.__dict__["__parent"].of):
                if n == name:
                    self.__dict__["__parent"].of[i] = (n, tpe)
                    return
            raise KeyError(name)

    @property
    def fields(self):
        return self.Fields(self)
