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

from collections import OrderedDict

from schema import *

################################################################ structured name objects

class Name(object):
    LIST_COUNT    = "Lc"
    LIST_OFFSET   = "Lo"
    LIST_BEGIN    = "Lb"
    LIST_END      = "Le"
    LIST_DATA     = "Ld"
    RECORD_FIELD  = "R_"
    TUPLE_INDEX   = "Rn"
    UNION_TAG     = "Ut"
    UNION_OFFSET  = "Uo"
    UNION_DATA    = "Ud"
    POINTER_INDEX = "Pi"
    POINTER_DATA  = "Pd"

    def __init__(self, prefix="", path=(), delimiter="-"):
        self.prefix = prefix
        self.path = path
        self.delimiter = delimiter

    @staticmethod
    def parse(string, prefix="", delimiter="-"):
        if not string.startswith(prefix):
            return None
        else:
            path = tuple((token[:2], token[2:]) if len(token) > 2 else (token,) for token in string[len(prefix):].split(delimiter) if token != "")
            return Name(prefix, path, delimiter=delimiter)

    def __repr__(self):
        delimiter = "" if self.delimiter == "-" else ", delimiter = " + repr(self.delimiter)
        return "Name({0}, {1}{2})".format(repr(self.prefix), repr(self.path), delimiter)

    def str(self, prefix=None):
        if prefix is None:
            prefix = self.prefix
        if prefix == "":
            return self.delimiter.join(x if isinstance(x, str) else x[0] + x[1] for x in self.path)
        else:
            return prefix + self.delimiter + self.str("")

    def __str__(self):
        return self.str()

    def __hash__(self):
        return hash((self.__class__, self.prefix, self.path, self.delimiter))

    def __eq__(self, other):
        return isinstance(other, Name) and self.prefix == other.prefix and self.path == other.path and self.delimiter == other.delimiter

    def __lt__(self, other):
        if isinstance(other, Name):
            if self.prefix == other.prefix:
                if self.path == other.path:
                    return self.delimiter < other.delimiter
                else:
                    return self.path < other.path
            else:
                return self.prefix < other.prefix
        else:
            raise TypeError("unorderable types: {0} < {1}".format(self.__class__.__name__, other.__class__.__name__))

    def __ne__(self, other): return not self.__eq__(other)
    def __le__(self, other): return self.__lt__(other) or self.__eq__(other)
    def __gt__(self, other): return other.__lt__(self)
    def __ge__(self, other): return other.__lt__(self) or self.__eq__(other)

    def toListCount(self):
        return Name(self.prefix, self.path + (Name.LIST_COUNT,), self.delimiter)

    def toListOffset(self):
        return Name(self.prefix, self.path + (Name.LIST_OFFSET,), self.delimiter)

    def toListBegin(self):
        return Name(self.prefix, self.path + (Name.LIST_BEGIN,), self.delimiter)

    def toListEnd(self):
        return Name(self.prefix, self.path + (Name.LIST_END,), self.delimiter)

    def toListData(self):
        return Name(self.prefix, self.path + (Name.LIST_DATA,), self.delimiter)

    def toRecordField(self, name):
        return Name(self.prefix, self.path + ((Name.RECORD_FIELD, name),), self.delimiter)

    def toTupleIndex(self, number):
        assert isinstance(number, int)
        return Name(self.prefix, self.path + ((Name.TUPLE_INDEX, repr(number)),), self.delimiter)

    def toUnionTag(self):
        return Name(self.prefix, self.path + (Name.UNION_TAG,), self.delimiter)

    def toUnionOffset(self):
        return Name(self.prefix, self.path + (Name.UNION_OFFSET,), self.delimiter)

    def toUnionData(self, number):
        assert isinstance(number, int)
        return Name(self.prefix, self.path + ((Name.UNION_DATA, repr(number)),), self.delimiter)

    def toPointerIndex(self):
        return Name(self.prefix, self.path + (Name.POINTER_INDEX,), self.delimiter)

    def toPointerData(self):
        return Name(self.prefix, self.path + (Name.POINTER_DATA,), self.delimiter)

    def isPrimitive(self):
        return len(self.path) == 0

    def isListCount(self, index=0):
        return -len(self.path) <= index < len(self.path) and self.path[index] == Name.LIST_COUNT

    def isListOffset(self, index=0):
        return -len(self.path) <= index < len(self.path) and self.path[index] == Name.LIST_OFFSET

    def isListBegin(self, index=0):
        return -len(self.path) <= index < len(self.path) and self.path[index] == Name.LIST_BEGIN

    def isListEnd(self, index=0):
        return -len(self.path) <= index < len(self.path) and self.path[index] == Name.LIST_END

    def isListData(self, index=0):
        return -len(self.path) <= index < len(self.path) and self.path[index] == Name.LIST_DATA

    def isRecordField(self, name=None, index=0):
        if name is None:
            return -len(self.path) <= index < len(self.path) and self.path[index][0] == Name.RECORD_FIELD
        else:
            return -len(self.path) <= index < len(self.path) and self.path[index] == (Name.RECORD_FIELD, name)

    def isTupleIndex(self, number=None, index=0):
        if number is None:
            return -len(self.path) <= index < len(self.path) and self.path[index][0] == Name.TUPLE_INDEX
        else:
            return -len(self.path) <= index < len(self.path) and self.path[index] == (Name.TUPLE_INDEX, repr(number))

    def isUnionTag(self, index=0):
        return -len(self.path) <= index < len(self.path) and self.path[index] == Name.UNION_TAG

    def isUnionOffset(self, index=0):
        return -len(self.path) <= index < len(self.path) and self.path[index] == Name.UNION_OFFSET

    def isUnionData(self, number=None, index=0):
        if number is None:
            return -len(self.path) <= index < len(self.path) and self.path[index][0] == Name.UNION_DATA
        else:
            return -len(self.path) <= index < len(self.path) and self.path[index] == (Name.UNION_DATA, repr(number))

    def isPointerIndex(self, index=0):
        return -len(self.path) <= index < len(self.path) and self.path[index] == Name.POINTER_INDEX

    def isPointerData(self, index=0):
        return -len(self.path) <= index < len(self.path) and self.path[index] == Name.POINTER_DATA

################################################################ add names to base

def isnamed(oam):
    for x in oam.walk():
        if x.name is None:
            return False
    return True

def namebase(oam, prefix="", delimiter="-"):
    def drill(oam):
        out = oam
        while out.base is not None:
            out = out.base
        return out

    def recurse(name, oam, memo):
        if id(oam) not in memo:
            memo.add(id(oam))

            if isinstance(oam, Primitive):
                drill(oam).base = Primitive(name.str(), nullable=oam.nullable)

            elif isinstance(oam, ListCount):
                drill(oam).base = ListCount(name.toListCount().str(), recurse(name.toListData(), oam.contents, memo), nullable=oam.nullable)

            elif isinstance(oam, ListOffset):
                drill(oam).base = ListOffset(name.toListOffset().str(), recurse(name.toListData(), oam.contents, memo), nullable=oam.nullable)

            elif isinstance(oam, ListBeginEnd):
                drill(oam).base = ListBeginEnd(name.toListBegin().str(), name.toListEnd().str(), recurse(name.toListData(), oam.contents, memo), nullable=oam.nullable)

            elif isinstance(oam, Record):
                drill(oam).base = Record(OrderedDict((n, recurse(name.toRecordField(n), c, memo)) for n, c in oam.contents.items()), name=name.str())

            elif isinstance(oam, Tuple):
                drill(oam).base = Tuple([recurse(name.toTupleIndex(i), x, memo) for i, x in enumerate(oam.contents)], name=name.str())

            elif isinstance(oam, UnionDense):
                drill(oam).base = UnionDense(name.toUnionTag().str(), [recurse(name.toUnionData(i), x, memo) for i, x in enumerate(oam.contents)], nullable=oam.nullable)

            elif isinstance(oam, UnionDenseOffset):
                drill(oam).base = UnionDenseOffset(name.toUnionTag().str(), name.toUnionOffset().str(), [recurse(name.toUnionData(i), x, memo) for i, x in enumerate(oam.contents)], nullable=oam.nullable)

            elif isinstance(oam, Pointer):
                drill(oam).base = Pointer(name.toPointerIndex().str(), recurse(name.toPointerData(), oam.target, memo), nullable=oam.nullable)

            else:
                raise AssertionError

        return drill(oam)

    return recurse(Name(prefix, (), delimiter), oam, set())
