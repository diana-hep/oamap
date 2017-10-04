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

    def _recursion_check(self, memo):
        if memo is None:
            memo = {}
        if id(self) in memo:
            raise TypeError("a container type cannot be included more than once in the same nested tree")
        memo[id(self)] = None
        return memo

    @staticmethod
    def _format_array(array, arraywidth):
        if isinstance(array, numpy.ndarray):
            end = ", dtype={0})".format(repr(str(array.dtype)))
            arraywidth -= len(end)
            
            if isinstance(array, numpy.ma.MaskedArray):
                out = ["masked_array(["]
                arraywidth -= len(out[-1])
                index = 0
                while index < len(array) and arraywidth - 4 > 0:
                    if index != 0:
                        out.append(" ")
                        arraywidth -= 1

                    if array.mask[index]:
                        out.append("--")
                        arraywidth -= 2
                    else:
                        out.append("{0:g}".format(array.data[index]))
                        arraywidth -= len(out[-1])

                    index += 1

            else:
                out = ["array(["]
                arraywidth -= len(out[-1])
                index = 0
                while index < len(array) and arraywidth - 4 > 0:
                    if index != 0:
                        out.append(" ")
                        arraywidth -= 1

                    out.append("{0:g}".format(array[index]))
                    arraywidth -= len(out[-1])

                    index += 1

            if index < len(array):
                out.append("...]")
            else:
                out.append("]")
            out.append(end)

            return "".join(out)

        elif isinstance(array, (str, bytes)):
            out = repr(array)
            if len(out) > arraywidth:
                out = out[:arraywidth - 4] + "...'"
            return out

        else:
            return repr(array)

    def _format_with_preamble(self, preamble, indent, width, refs, memo):
        first = True
        for line in self._format(indent, width, refs, memo):
            if first:
                yield indent + preamble + line[len(indent):]
                first = False
            else:
                yield line
                
    def format(self, highlight=lambda t: "", width=80):
        ids = {}
        refs = {}
        def recurse(t):
            if id(t) in ids:
                refs[id(t)] = "[{0}] ".format(len(refs))
            else:
                ids[id(t)] = t
                c = getattr(t, "contents", ())
                if isinstance(c, tuple):
                    for ci in c:
                        recurse(ci)
                elif isinstance(c, dict):
                    for ci in c.values():
                        recurse(ci)
                else:
                    recurse(c)
                c = getattr(t, "target", None)
                if c is not None:
                    recurse(c)
        recurse(self)

        return "\n".join(self._format("", width, refs, {}))

################################################################ primitives

class PrimitiveOAM(ObjectArrayMapping):
    def __init__(self, array, base=None):
        self.array = array
        self.base = base

    def dereference(self, source, _memo=None):
        return PrimitiveOAM(self._dereference(self.array, source, "PrimitiveOAM array must map to a one-dimensional, non-record array"), self)

    def _format_with_preamble(self, preamble, indent, width, refs, memo):
        for line in self._format(indent, width - len(preamble), refs, memo):
            yield indent + preamble + line[len(indent):]

    def _format(self, indent, width, refs, memo):
        self._recursion_check(memo)
        preamble = refs.get(id(self), "")
        yield indent + preamble + self._format_array(self.array, width - len(preamble) - len(indent))

    def __eq__(self, other):
        return isinstance(other, PrimitiveOAM) and ((isinstance(self.array, ndarray) and isinstance(other.array, ndarray) and numpy.array_equal(self.array, other.array)) or self.array == other.array) and self.base == other.base

    def __ne__(self, other):
        return not self.__eq__(self, other)

################################################################ lists

class ListOAM(ObjectArrayMapping):
    def __init__(self, *args, **kwds):
        raise TypeError("ListOAM is abstract; use ListCountOAM, ListOffsetOAM, or ListStartEndOAM instead")

class ListCountOAM(ListOAM):
    def __init__(self, countarray, contents, base=None):
        self.countarray = countarray
        self.contents = contents
        self.base = base
        assert isinstance(self.contents, ObjectArrayMapping), "contents must be an ObjectArrayMapping"

    def dereference(self, source, _memo=None):
        countarray = self._dereference(self.countarray, source, "ListCountOAM countarray must map to a one-dimensional, non-record array of integers", lambda x: issubclass(x.dtype.type, numpy.integer))
        offsetarray = numpy.empty(len(countarray) + 1, dtype=numpy.int64)   # new allocation
        numpy.cumsum(countarray, offsetarray[1:])                           # fill with offsets
        offsetarray[0] = 0
        startarray = offsetarray[:-1]  # overlapping views
        endarray = offsetarray[1:]     # overlapping views
        _memo = self._recursion_check(_memo)
        _memo[id(self)] = ListStartEndOAM(startarray, endarray, self.contents.dereference(source, _memo), self)
        return _memo[id(self)]

    def _format(self, indent, width, refs, memo):
        self._recursion_check(memo)
        yield indent + refs.get(id(self), "") + "List ["
        indent += "  "
        preamble = "countarray = "
        yield indent + preamble + self._format_array(self.countarray, width - len(preamble) - len(indent))
        for line in self.contents._format(indent, width, refs, memo):
            yield line
        yield indent + "]"

    def __eq__(self, other):
        return isinstance(other, ListCountOAM) and ((isinstance(self.countarray, ndarray) and isinstance(other.countarray, ndarray) and numpy.array_equal(self.countarray, other.countarray)) or self.countarray == other.countarray) and self.contents == other.contents and self.base == other.base

    def __ne__(self, other):
        return not self.__eq__(self, other)

class ListOffsetOAM(ListOAM):
    def __init__(self, offsetarray, contents, base=None):
        self.offsetarray = offsetarray
        self.contents = contents
        self.base = base
        assert isinstance(self.contents, ObjectArrayMapping), "contents must be an ObjectArrayMapping"

    def dereference(self, source, _memo=None):
        offsetarray = self._dereference(self.offsetarray, source, "ListOffsetOAM offsetarray must map to a one-dimensional, non-record array of integers", lambda x: issubclass(x.dtype.type, numpy.integer))
        startarray = offsetarray[:-1]  # overlapping views
        endarray = offsetarray[1:]     # overlapping views
        _memo = self._recursion_check(_memo)
        _memo[id(self)] = ListStartEndOAM(startarray, endarray, self.contents.dereference(source, _memo), self)
        return _memo[id(self)]

    def _format(self, indent, width, refs, memo):
        self._recursion_check(memo)
        yield indent + refs.get(id(self), "") + "List ["
        indent += "  "
        preamble = "offsetarray = "
        yield indent + preamble + self._format_array(self.offsetarray, width - len(preamble) - len(indent))
        for line in self.contents._format(indent, width, refs, memo):
            yield line
        yield indent + "]"

    def __eq__(self, other):
        return isinstance(other, ListOffsetOAM) and ((isinstance(self.offsetarray, ndarray) and isinstance(other.offsetarray, ndarray) and numpy.array_equal(self.offsetarray, other.offsetarray)) or self.offsetarray == other.offsetarray) and self.contents == other.contents and self.base == other.base

    def __ne__(self, other):
        return not self.__eq__(self, other)
        
class ListStartEndOAM(ListOAM):
    def __init__(self, startarray, endarray, contents, base=None):
        self.startarray = startarray
        self.endarray = endarray
        self.contents = contents
        self.base = base
        assert isinstance(self.contents, ObjectArrayMapping), "contents must be an ObjectArrayMapping"

    def dereference(self, source, _memo=None):
        startarray = self._dereference(self.startarray, source, "ListStartEndOAM startarray must map to a one-dimensional, non-record array of integers", lambda x: issubclass(x.dtype.type, numpy.integer))
        endarray = self._dereference(self.startarray, source, "ListStartEndOAM endarray must map to a one-dimensional, non-record array of integers", lambda x: issubclass(x.dtype.type, numpy.integer))
        _memo = self._recursion_check(_memo)
        _memo[id(self)] = ListStartEndOAM(startarray, endarray, self.contents.dereference(source, _memo), self)
        return _memo[id(self)]

    def _format(self, indent, width, refs, memo):
        self._recursion_check(memo)
        yield indent + refs.get(id(self), "") + "List ["
        indent += "  "
        preamble = "startarray = "
        yield indent + preamble + self._format_array(self.startarray, width - len(preamble) - len(indent))
        preamble = "endarray   = "
        yield indent + preamble + self._format_array(self.endarray, width - len(preamble) - len(indent))
        for line in self.contents._format(indent, width, refs, memo):
            yield line
        yield indent + "]"

    def __eq__(self, other):
        return isinstance(other, ListStartEndOAM) and ((isinstance(self.startarray, ndarray) and isinstance(other.startarray, ndarray) and numpy.array_equal(self.startarray, other.startarray)) or self.startarray == other.startarray) and ((isinstance(self.endarray, ndarray) and isinstance(other.endarray, ndarray) and numpy.array_equal(self.endarray, other.endarray)) or self.endarray == other.endarray) and self.contents == other.contents and self.base == other.base

    def __ne__(self, other):
        return not self.__eq__(self, other)

################################################################ records and tuples

class RecordOAM(ObjectArrayMapping):
    def __init__(self, contents, base=None):
        self.contents = contents
        self.base = base
        assert isinstance(self.contents, dict)
        assert all(isinstance(x, str) for x in self.contents.keys()), "contents must be a dict from strings to ObjectArrayMappings"
        assert all(isinstance(x, ObjectArrayMapping) for x in self.contents.values()), "contents must be a dict from strings to ObjectArrayMappings"

    def dereference(self, source, _memo=None):
        # a record is a purely organizational type; it has no arrays of its own, so just pass on the dereferencing request
        _memo = self._recursion_check(_memo)
        _memo[id(self)] = RecordOAM(dict((k, v.dereference(source, _memo)) for k, v in self.contents.items()), self)
        return _memo[id(self)]

    def _format(self, indent, width, refs, memo):
        self._recursion_check(memo)
        yield indent + refs.get(id(self), "") + "Record {"
        indent += "  "
        for key, contents in self.contents.items():
            for line in contents._format_with_preamble("{0}: ".format(key), indent, width, refs, memo):
                yield line
        yield indent + "}"

    def __eq__(self, other):
        return isinstance(other, RecordOAM) self.contents == other.contents and self.base == other.base

    def __ne__(self, other):
        return not self.__eq__(self, other)

class TupleOAM(ObjectArrayMapping):
    def __init__(self, contents, base=None):
        self.contents = tuple(contents)
        self.base = base
        assert all(isinstance(x, ObjectArrayMapping) for x in self.contents), "contents must be a tuple of ObjectArrayMappings"

    def dereference(self, source, _memo=None):
        # a tuple is a purely organizational type; it has no arrays of its own, so just pass on the dereferencing request
        _memo = self._recursion_check(_memo)
        _memo[id(self)] = TupleOAM(tuple(x.dereference(source, _memo) for x in self.contents), self)
        return _memo[id(self)]

    def _format(self, indent, width, refs, memo):
        self._recursion_check(memo)
        if isinstance(self.contents, tuple):
            yield indent + refs.get(id(self), "") + "Tuple ("
            indent += "  "
            for index, contents in enumerate(self.contents):
                for line in contents._format_with_preamble("{0}: ".format(index), indent, width, refs, memo):
                    yield line
            yield indent + ")"

    def __eq__(self, other):
        return isinstance(other, TupleOAM) self.contents == other.contents and self.base == other.base

    def __ne__(self, other):
        return not self.__eq__(self, other)

################################################################ unions

class UnionOAM(ObjectArrayMapping):
    def __init__(self, *args, **kwds):
        raise TypeError("UnionOAM is abstract; use UnionSparse or UnionSparseOffset instead")

class UnionSparseOAM(UnionOAM):
    def __init__(self, tagarray, contents, base=None):
        self.tagarray = tagarray
        self.contents = contents
        self.base = base
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
        _memo[id(self)] = UnionSparseOffsetOAM(tagarray, offsetarray, tuple(x.dereference(source, _memo) for x in self.contents), self)
        return _memo[id(self)]

    def _format(self, indent, width, refs, memo):
        self._recursion_check(memo)
        yield indent + refs.get(id(self), "") + "Union <"
        indent += "  "
        preamble = "tagarray = "
        yield indent + preamble + self._format_array(self.tagarray, width - len(preamble) - len(indent))
        for index, contents in enumerate(self.contents):
            for line in contents._format_with_preamble("{0}: ".format(index), indent, width, refs, memo):
                yield line
        yield indent + ">"

    def __eq__(self, other):
        return isinstance(other, UnionSparseOAM) and ((isinstance(self.tagarray, ndarray) and isinstance(other.tagarray, ndarray) and numpy.array_equal(self.tagarray, other.tagarray)) or self.tagarray == other.tagarray) and self.contents == other.contents and self.base == other.base

    def __ne__(self, other):
        return not self.__eq__(self, other)

class UnionSparseOffsetOAM(UnionOAM):
    def __init__(self, tagarray, offsetarray, contents, base=None):
        self.tagarray = tagarray
        self.offsetarray = offsetarray
        self.contents = contents
        self.base = base
        if isinstance(self.contents, tuple):
            assert all(isinstance(x, ObjectArrayMapping) for x in self.contents), "contents must be a tuple of ObjectArrayMappings"
        else:
            raise AssertionError("contents must be a tuple")

    def dereference(self, source, _memo=None):
        tagarray = self._dereference(self.tagarray, source, "UnionSparseOffsetOAM tagarray must map to a one-dimensional, non-record array of integers", lambda x: issubclass(x.dtype.type, numpy.integer))
        offsetarray = self._dereference(self.offsetarray, source, "UnionSparseOffsetOAM offsetarray must map to a one-dimensional, non-record array of integers", lambda x: issubclass(x.dtype.type, numpy.integer))
        _memo = self._recursion_check(_memo)
        _memo[id(self)] = UnionSparseOffsetOAM(tagarray, offsetarray, tuple(x.dereference(source, _memo) for x in self.contents), self)
        return _memo[id(self)]

    def _format(self, indent, width, refs, memo):
        self._recursion_check(memo)
        yield indent + refs.get(id(self), "") + "Union <"
        indent += "  "
        preamble = "tagarray    = "
        yield indent + preamble + self._format_array(self.tagarray, width - len(preamble) - len(indent))
        preamble = "offsetarray = "
        yield indent + preamble + self._format_array(self.offsetarray, width - len(preamble) - len(indent))
        for index, contents in enumerate(self.contents):
            for line in contents._format_with_preamble("{0}: ".format(index), indent, width, refs, memo):
                yield line
        yield indent + ">"

    def __eq__(self, other):
        return isinstance(other, UnionSparseOffsetOAM) and ((isinstance(self.tagarray, ndarray) and isinstance(other.tagarray, ndarray) and numpy.array_equal(self.tagarray, other.tagarray)) or self.tagarray == other.tagarray) and ((isinstance(self.offsetarray, ndarray) and isinstance(other.offsetarray, ndarray) and numpy.array_equal(self.offsetarray, other.offsetarray)) or self.offsetarray == other.offsetarray) and self.contents == other.contents and self.base == other.base

    def __ne__(self, other):
        return not self.__eq__(self, other)

################################################################ pointers

class PointerOAM(ObjectArrayMapping):
    def __init__(self, indexarray, target, base=None):
        self.indexarray = indexarray
        self.target = target
        self.base = base
        assert isinstance(self.target, ObjectArrayMapping), "target must be an ObjectArrayMapping"
        assert self.target is not self, "pointer's target may contain the pointer, but it must not be the pointer itself"

    def dereference(self, source, _memo=None):
        indexarray = self._dereference(self.indexarray, source, "PointerOAM indexarray must map to a one-dimensional, non-record array of integers", lambda x: issubclass(x.dtype.type, numpy.integer))
        # (only) pointers are allowed to reference themselves, but don't resolve the same pointer more than once
        if _memo is None:
            _memo = {}
        if id(self.target) not in _memo:
            self.target.dereference(source, _memo)
        _memo[id(self)] = PointerOAM(indexarray, _memo[id(self.target)], self)
        return _memo[id(self)]

    def _format(self, indent, width, refs, memo):
        yield indent + refs.get(id(self), "") + "Pointer (*"
        indent += "  "
        preamble = "indexarray = "
        yield indent + preamble + self._format_array(self.indexarray, width - len(preamble) - len(indent))
        if id(self.target) in refs:
            yield indent + "target: " + refs[id(self.target)].strip()
        else:
            for line in self.target._format(indent, width, refs, {}):
                yield line
        yield indent + "*)"

    def __eq__(self, other):
        return isinstance(other, PointerOAM) and ((isinstance(self.indexarray, ndarray) and isinstance(other.indexarray, ndarray) and numpy.array_equal(self.indexarray, other.indexarray)) or self.indexarray == other.indexarray) and self.target is other.target and self.base == other.base

    def __ne__(self, other):
        return not self.__eq__(self, other)
