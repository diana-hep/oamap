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

class ArrayName(object):
    def __init__(self, prefix, path=(), delimiter="-"):
        self.prefix = prefix
        self.path = path
        self.delimiter = delimiter

    @staticmethod
    def parse(string, prefix, delimiter="-"):
        if not string.startswith(prefix):
            return None
        else:
            path = tuple((token[:2], token[2:]) if len(token) > 2 else (token,) for token in string[len(prefix):].split(delimiter) if token != "")
            return ArrayName(prefix, path, delimiter=delimiter)

    def __repr__(self):
        delimiter = "" if self.delimiter == "-" else ", delimiter = " + repr(self.delimiter)
        return "ArrayName({0}, {1}{2})".format(repr(self.prefix), repr(self.path), delimiter)

    def str(self, prefix=None):
        if prefix is None:
            prefix = self.prefix
        return prefix + "".join(self.delimiter + "".join(x) for x in self.path)

    def __str__(self):
        return self.str()

    def __eq__(self, other):
        return isinstance(other, ArrayName) and self.prefix == other.prefix and self.path == other.path and self.delimiter == other.delimiter

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.__class__, self.prefix, self.path, self.delimiter))

    def __lt__(self, other):
        if isinstance(other, ArrayName):
            if self.prefix == other.prefix:
                if self.path == other.path:
                    return self.delimiter < other.delimiter
                else:
                    return self.path < other.path
            else:
                return self.prefix < other.prefix
        else:
            raise TypeError("unorderable types: {0} < {1}".format(self.__class__.__name__, other.__class__.__name__))

    # P

    # L
    def toListOffset(self):
        return ArrayName(self.prefix, self.path + (("Lo",),), self.delimiter)

    def toListData(self):
        return ArrayName(self.prefix, self.path + (("Ld",),), self.delimiter)

    # U
    def toUnionTag(self):
        return ArrayName(self.prefix, self.path + (("Ut",),), self.delimiter)

    def toUnionOffset(self):
        return ArrayName(self.prefix, self.path + (("Uo",),), self.delimiter)

    def toUnionData(self, tagnum):
        return ArrayName(self.prefix, self.path + (("Ud", repr(tagnum)),), self.delimiter)

    # R
    def toRecord(self, fieldname):
        return ArrayName(self.prefix, self.path + (("R_", fieldname),), self.delimiter)

    # runtime
    def toRuntime(self, rtname, *rtargs):
        path = list(self.path)
        path.append(("T_", rtname))

        if len(rtargs) > 0:
            path.append(("Td",))

        for i, arg in enumerate(rtargs):
            if i != 0:
                path.append(("Tl",))
            path.extend((token[:2], token[2:]) for token in arg.split(self.delimiter))

        if len(rtargs) > 0:
            path.append(("Tb",))

        return ArrayName(self.prefix, tuple(path), self.delimiter)

    def drop(self):
        assert not self.isPrimitive
        return ArrayName(self.prefix, self.path[1:], self.delimiter)

    # P
    @property
    def isPrimitive(self):
        return len(self.path) == 0

    # L
    @property
    def isListOffset(self):
        return len(self.path) > 0 and self.path[0] == ("Lo",)

    @property
    def isListData(self):
        return len(self.path) > 0 and self.path[0] == ("Ld",)

    # U
    @property
    def isUnionTag(self):
        return len(self.path) > 0 and self.path[0] == ("Ut",)

    @property
    def isUnionOffset(self):
        return len(self.path) > 0 and self.path[0] == ("Uo",)

    @property
    def isUnionData(self):
        return len(self.path) > 0 and self.path[0][0] == "Ud"

    @property
    def tagnum(self):
        assert self.isUnionData
        return int(self.path[0][1])

    # R
    @property
    def isRecord(self):
        return len(self.path) > 0 and self.path[0][0] == "R_"

    @property
    def fieldname(self):
        assert self.isRecord
        return self.path[0][1]

    # runtime
    @property
    def isRuntime(self):
        return len(self.path) > 0 and self.path[0][0] == "T_"

    @property
    def rtname(self):
        assert self.isRuntime
        return self.path[0][1]

    @property
    def rtargs(self):
        assert self.isRuntime
        if len(self.path) < 2 or self.path[1] != ("Td",):
            return ()

        else:
            stack = 0
            out = [[]]
            for pathitem in self.path[2:]:
                if stack == 0 and pathitem == ("Tb",):
                    return tuple(self.delimiter.join(item) for item in out if len(item) > 0)
                elif stack == 0 and pathitem == ("Tl",):
                    out.append([])
                elif pathitem == ("Td",):
                    stack += 1
                elif pathitem == ("Tb",):
                    stack -= 1
                    assert stack >= 0
                else:
                    out[-1].append(pathitem[0] + pathitem[1])

            assert False, "missing closing parenthesis in runtime arguments (-Tb)"

    def dropRuntime(self):
        assert self.isRuntime
        if len(self.path) < 2 or self.path[1] != ("Td",):
            return ArrayName(self.prefix, self.path[1:], self.delimiter)

        else:
            stack = 0
            path = self.path
            while len(path) > 0:
                pathitem = path[0]
                path = path[1:]

                if stack == 0 and pathitem == ("Tb",):
                    return ArrayName(self.prefix, path, self.delimiter)
                elif pathitem == ("Td",):
                    stack += 1
                elif pathitem == ("Tb",):
                    stack -= 1
                    assert stack >= 0

            assert False, "missing closing parenthesis in runtime arguments (-Tb)"
