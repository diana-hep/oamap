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

from plur.util import *
from plur.types.type import Type

class Union(Type):
    _sortorder = 2

    def __init__(self, *of):
        def flatten(x):
            if isinstance(x, tuple):
                for y in x:
                    for z in flatten(y):
                        yield z

            elif isinstance(x, Union):
                for y in flatten(x.of):
                    yield y
            else:
                yield x

        self.of = tuple(sorted(set(flatten(of))))
        if len(self.of) < 2:
            raise TypeDefinitionError("union must have at least two possibilities")

        super(Union, self).__init__()

    @property
    def args(self):
        return self.of

    @property
    def children(self):
        return self.of

    def __contains__(self, element):
        return any(element in x for x in self.of)

    def issubtype(self, supertype):
        # Type.issubtype(supertype) handles the inverse case (supertype is a Union and self isn't); all other Types try that first

        if isinstance(supertype, Union) and supertype.rtname == self.rtname and supertype.rtargs == self.rtargs:
            # supertype is a Union; everything that we have must fit into one of its possibilities
            for tpe in self.of:
                if not any(tpe.issubtype(x) for x in supertype.of):
                    return False
            return True

        elif self.rtname == supertype.rtname:
            # supertype is not a Union; everything that we have must fit into it
            for tpe in self.of:
                if not tpe.issubtype(supertype):
                    return False
            return True

        else:
            return False

    def toJson(self):
        return {"union": [x.toJson() for x in self.of]}

    class Choices(object):
        def __init__(self, parent):
            self.__dict__["__parent"] = parent

        def __repr__(self):
            return "<Union.Choices of {0}>".format(" ".join(repr(t) for t in self.__dict__["__parent"].of))

        def __getattr__(self, name):
            for t in self.__dict__["__parent"].of:
                if repr(t) == name:
                    return t
            raise KeyError(name)

        def __setattr__(self, name, tpe):
            possibilities = list(self.__dict__["__parent"].of)

            for i, t in enumerate(possibilities):
                if repr(t) == name:
                    possibilities[i] = tpe
                    replacement = Union(*possibilities)
                    self.__dict__["__parent"].of = replacement.of
                    return
            raise KeyError(name)

    @property
    def choices(self):
        return self.Choices(self)
