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

import collections
import json

import numpy
import numpy.ma

class ObjectArrayMapping(object):
    def toJsonString(self):
        return json.dumps(self.toJson())

    @staticmethod
    def fromJsonString(string):
        return ObjectArrayMapping.fromJson(json.loads(string))

    @staticmethod
    def _dereference_check(array, message, extracheck):
        assert isinstance(array, numpy.ndarray) and not isinstance(array, numpy.recarray) and len(array.shape) == 1 and extracheck(array), message
        return array

    @staticmethod
    def _dereference(obj, source, message, extracheck=lambda x: True):
        if isinstance(obj, numpy.ndarray):
            return ObjectArrayMapping._dereference_check(obj, message, extracheck)

        elif callable(obj):
            if hasattr(obj, "__code__") and obj.__code__.co_argcount == 0:
                return ObjectArrayMapping._dereference_check(obj(), message, extracheck)
            else:
                return ObjectArrayMapping._dereference_check(obj(source), message, extracheck)

        elif isinstance(obj, collections.Hashable) and obj in source:
            return ObjectArrayMapping._dereference_check(source[obj], message, extracheck)

        else:
            raise ValueError("array cannot be found for key {0}".format(repr(obj)))

    def _recursion_check(self, _memo):
        if _memo is None:
            _memo = set()

        if id(self) in _memo:
            raise TypeError("a container type cannot be included more than once in the same nested tree")

        _memo.add(id(self))
        return _memo

class PrimitiveOAM(ObjectArrayMapping):
    def __init__(self, array):
        self.array = array

    def dereference(self, source, _memo=None):
        return PrimitiveOAM(self._dereference(self.array, source, "PrimitiveOAM array must map to a one-dimensional, non-record array"))

class ListOAM(ObjectArrayMapping):
    def __init__(self, *args, **kwds):
        raise TypeError("ListOAM is abstract; use ListCountOAM, ListOffsetOAM, or ListStartEndOAM instead")

class ListCountOAM(ListOAM):
    def __init__(self, countarray, contents):
        self.countarray = countarray
        self.contents = contents
        assert isinstance(self.contents, ObjectArrayMapping), "contents must be an ObjectArrayMapping"

    def dereference(self, source, _memo=None):
        countarray = self._dereference(self.countarray, source, "ListCountOAM countarray must map to a one-dimensional, non-record array of integers", lambda x: issubclass(x.dtype.type, numpy.integer))
        offsetarray = numpy.empty(len(countarray) + 1, dtype=numpy.int64)   # new allocation
        numpy.cumsum(countarray, offsetarray[1:])                           # fill with offsets
        offsetarray[0] = 0
        startarray = offsetarray[:-1]  # overlapping views
        endarray = offsetarray[1:]     # overlapping views
        _memo = self._recursion_check(_memo)
        return ListStartEndOAM(startarray, endarray, self.contents.dereference(source, _memo))

class ListOffsetOAM(ListOAM):
    def __init__(self, offsetarray, contents):
        self.offsetarray = offsetarray
        self.contents = contents
        assert isinstance(self.contents, ObjectArrayMapping), "contents must be an ObjectArrayMapping"

    def dereference(self, source, _memo=None):
        offsetarray = self._dereference(self.offsetarray, source, "ListOffsetOAM offsetarray must map to a one-dimensional, non-record array of integers", lambda x: issubclass(x.dtype.type, numpy.integer))
        startarray = offsetarray[:-1]  # overlapping views
        endarray = offsetarray[1:]     # overlapping views
        _memo = self._recursion_check(_memo)
        return ListStartEndOAM(startarray, endarray, self.contents.dereference(source, _memo))
        
class ListStartEndOAM(ListOAM):
    def __init__(self, startarray, endarray, contents):
        self.startarray = startarray
        self.endarray = endarray
        self.contents = contents
        assert isinstance(self.contents, ObjectArrayMapping), "contents must be an ObjectArrayMapping"

    def dereference(self, source, _memo=None):
        startarray = self._dereference(self.startarray, source, "ListStartEndOAM startarray must map to a one-dimensional, non-record array of integers", lambda x: issubclass(x.dtype.type, numpy.integer))
        endarray = self._dereference(self.startarray, source, "ListStartEndOAM endarray must map to a one-dimensional, non-record array of integers", lambda x: issubclass(x.dtype.type, numpy.integer))
        _memo = self._recursion_check(_memo)
        return ListStartEndOAM(startarray, endarray, self.contents.dereference(source, _memo))

class RecordOAM(ObjectArrayMapping):
    def __init__(self, contents):
        self.contents = contents
        if isinstance(self.contents, tuple):
            assert all(isinstance(x, ObjectArrayMapping) for x in self.contents), "contents must be a tuple or dict of ObjectArrayMappings"
        elif isinstance(self.contents, dict):
            assert all(isinstance(x, ObjectArrayMapping) for x in self.contents.values()), "contents must be a tuple or dict of ObjectArrayMappings"
            assert all(isinstance(x, str) for x in self.contents.keys()), "keys of contents dict must be strings"
        else:
            raise AssertionError("contents must be a tuple or dict")

    def dereference(self, source, _memo=None):
        # a record is a purely organizational type; it has no arrays of its own, so just pass on the dereferencing request
        _memo = self._recursion_check(_memo)
        if isinstance(self.contents, tuple):
            return RecordOAM(tuple(x.dereference(source, _memo) for x in self.contents))
        else:
            return RecordOAM(dict((k, v.dereference(source, _memo)) for k, v in self.contents.items()))

class UnionOAM(ObjectArrayMapping):
    def __init__(self, *args, **kwds):
        raise TypeError("UnionOAM is abstract; use UnionSparse or UnionSparseOffset instead")

class UnionSparseOAM(UnionOAM):
    def __init__(self, tagarray, contents):
        self.tagarray = tagarray
        self.contents = contents
        if isinstance(self.contents, tuple):
            assert all(isinstance(x, ObjectArrayMapping) for x in self.contents), "contents must be a tuple of ObjectArrayMappings"
        else:
            raise AssertionError("contents must be a tuple")

    def dereference(self, source, _memo=None):
        tagarray = self._dereference(self.tagarray, source, "UnionSparseOAM tagarray must map to a one-dimensional, non-record array of integers", lambda x: issubclass(x.dtype.type, numpy.integer))
        offsetarray = numpy.empty(len(tagarray), dtype=numpy.int64)
        for tag in range(len(self.contents)):    # for each possible tag
            matches = (tagarray == tag)          # find the elements of tagarray that match this tag
            nummatches = matches.sum()
            offsetarray[matches] = numpy.linspace(0, nummatches - 1, nummatches, dtype=numpy.int64)
                                                 # offsets corresponding to matching tags should be increasing integers
        _memo = self._recursion_check(_memo)
        return UnionSparseOffsetOAM(tagarray, offsetarray, tuple(x.dereference(source, _memo) for x in self.contents))

class UnionSparseOffsetOAM(UnionOAM):
    def __init__(self, tagarray, offsetarray, contents):
        self.tagarray = tagarray
        self.offsetarray = offsetarray
        self.contents = contents
        if isinstance(self.contents, tuple):
            assert all(isinstance(x, ObjectArrayMapping) for x in self.contents), "contents must be a tuple of ObjectArrayMappings"
        else:
            raise AssertionError("contents must be a tuple")

    def dereference(self, source, _memo=None):
        tagarray = self._dereference(self.tagarray, source, "UnionSparseOffsetOAM tagarray must map to a one-dimensional, non-record array of integers", lambda x: issubclass(x.dtype.type, numpy.integer))
        offsetarray = self._dereference(self.offsetarray, source, "UnionSparseOffsetOAM offsetarray must map to a one-dimensional, non-record array of integers", lambda x: issubclass(x.dtype.type, numpy.integer))
        _memo = self._recursion_check(_memo)
        return UnionSparseOffsetOAM(tagarray, offsetarray, tuple(x.dereference(source, _memo) for x in self.contents))

class PointerOAM(ObjectArrayMapping):
    def __init__(self, indexarray, target):
        self.indexarray = indexarray
        self.target = target
        assert isinstance(self.target, ObjectArrayMapping), "target must be an ObjectArrayMapping"

    def dereference(self, source, _memo=None):
        indexarray = self._dereference(self.indexarray, source, "PointerOAM indexarray must map to a one-dimensional, non-record array of integers", lambda x: issubclass(x.dtype.type, numpy.integer))
        # (only) pointers are allowed to reference themselves, but don't resolve the same pointer more than once
        if _memo is None:
            _memo = set()
        if id(self) in _memo:
            out = PointerOAM(indexarray, self.target)
        else:
            out = PointerOAM(indexarray, self.target.dereference(source, set([id(self)])))
        _memo.add(id(self))
        return out
