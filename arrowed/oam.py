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

class ObjectArrayMapping(object):
    pass

class PrimitiveOAM(ObjectArrayMapping):
    def __init__(self, array):
        self.array = array

    def __repr__(self):
        return "PrimitiveOAM({0})".format(repr(self.array))

class ListOAM(ObjectArrayMapping):
    def __init__(self, *args, **kwds):
        raise TypeError("ListOAM is abstract; use ListCountOAM, ListOffsetOAM, or ListStartEndOAM instead")

class ListCountOAM(ListOAM):
    def __init__(self, countarray, contents):
        self.countarray = countarray
        self.contents = contents

    def __repr__(self):
        return "ListCountOAM({0}, {1})".format(repr(self.countarray), repr(self.contents))

class ListOffsetOAM(ListOAM):
    def __init__(self, offsetarray, contents):
        self.offsetarray = offsetarray
        self.contents = contents

    def __repr__(self):
        return "ListOffsetOAM({0}, {1})".format(repr(self.offsetarray), repr(self.contents))

class ListStartEndOAM(ListOAM):
    def __init__(self, startarray, endarray, contents):
        self.startarray = startarray
        self.endarray = endarray
        self.contents = contents

    def __repr__(self):
        return "ListStartEndOAM({0}, {1}, {2})".format(repr(self.startarray), repr(self.endarray), repr(self.contents))

class RecordOAM(ObjectArrayMapping):
    def __init__(self, contents):
        self.contents = contents

    def __repr__(self):
        return "RecordOAM({0})".format(repr(self.contents))

class UnionOAM(ObjectArrayMapping):
    def __init__(self, *args, **kwds):
        raise TypeError("UnionOAM is abstract; use UnionSparse or UnionSparseOffset instead")

class UnionSparseOAM(UnionOAM):
    def __init__(self, tagarray, contents):
        self.tagarray = tagarray
        self.contents = contents

    def __repr__(self):
        return "UnionSparseOAM({0}, {1})".format(repr(self.tagarray), repr(self.contents))

class UnionSparseOffsetOAM(UnionOAM):
    def __init__(self, tagarray, offsetarray, contents):
        self.tagarray = tagarray
        self.offsetarray = offsetarray
        self.contents = contents

    def __repr__(self):
        return "UnionSparseOffsetOAM({0}, {1})".format(repr(self.tagarray), repr(self.offsetarray), repr(self.contents))


