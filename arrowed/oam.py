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

        return "\n".join(self._format("", width, refs, set()))

################################################################ primitives

class PrimitiveOAM(ObjectArrayMapping):
    def __init__(self, array):
        self.array = array

    def dereference(self, source, _memo=None):
        return PrimitiveOAM(self._dereference(self.array, source, "PrimitiveOAM array must map to a one-dimensional, non-record array"))

    def _format_with_preamble(self, preamble, indent, width, refs, memo):
        for line in self._format(indent, width - len(preamble), refs, memo):
            yield indent + preamble + line[len(indent):]

    def _format(self, indent, width, refs, memo):
        self._recursion_check(memo)
        preamble = refs.get(id(self), "")
        yield indent + preamble + self._format_array(self.array, width - len(preamble) - len(indent))

################################################################ lists

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

    def _format(self, indent, width, refs, memo):
        self._recursion_check(memo)
        yield indent + refs.get(id(self), "") + "List ["
        indent += "  "
        preamble = "counts = "
        yield indent + preamble + self._format_array(self.countarray, width - len(preamble) - len(indent))
        for line in self.contents._format(indent, width, refs, memo):
            yield line
        yield indent + "]"

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

    def _format(self, indent, width, refs, memo):
        self._recursion_check(memo)
        yield indent + refs.get(id(self), "") + "List ["
        indent += "  "
        preamble = "offsets = "
        yield indent + preamble + self._format_array(self.offsetarray, width - len(preamble) - len(indent))
        for line in self.contents._format(indent, width, refs, memo):
            yield line
        yield indent + "]"
        
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

    def _format(self, indent, width, refs, memo):
        self._recursion_check(memo)
        yield indent + refs.get(id(self), "") + "List ["
        indent += "  "
        preamble = "starts = "
        yield indent + preamble + self._format_array(self.startarray, width - len(preamble) - len(indent))
        preamble = "ends   = "
        yield indent + preamble + self._format_array(self.endarray, width - len(preamble) - len(indent))
        for line in self.contents._format(indent, width, refs, memo):
            yield line
        yield indent + "]"

################################################################ records

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

    def _format(self, indent, width, refs, memo):
        self._recursion_check(memo)
        if isinstance(self.contents, tuple):
            yield indent + refs.get(id(self), "") + "Record ("
            indent += "  "
            for index, contents in enumerate(self.contents):
                for line in contents._format_with_preamble("{0}: ".format(index), indent, width, refs, memo):
                    yield line
            yield indent + ")"
        else:
            yield indent + refs.get(id(self), "") + "Record {"
            indent += "  "
            for key, contents in self.contents.items():
                for line in contents._format_with_preamble("{0}: ".format(key), indent, width, refs, memo):
                    yield line
            yield indent + "}"

################################################################ unions

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

    def _format(self, indent, width, refs, memo):
        self._recursion_check(memo)
        yield indent + refs.get(id(self), "") + "Union <"
        indent += "  "
        preamble = "tags = "
        yield indent + preamble + self._format_array(self.tagarray, width - len(preamble) - len(indent))
        for index, contents in enumerate(self.contents):
            for line in contents._format_with_preamble("{0}: ".format(index), indent, width, refs, memo):
                yield line
        yield indent + ">"

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

    def _format(self, indent, width, refs, memo):
        self._recursion_check(memo)
        yield indent + refs.get(id(self), "") + "Union <"
        indent += "  "
        preamble = "tags = "
        yield indent + preamble + self._format_array(self.tagarray, width - len(preamble) - len(indent))
        preamble = "offsets = "
        yield indent + preamble + self._format_array(self.offsetarray, width - len(preamble) - len(indent))
        for index, contents in enumerate(self.contents):
            for line in contents._format_with_preamble("{0}: ".format(index), indent, width, refs, memo):
                yield line
        yield indent + ">"

################################################################ pointers

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

    def _format(self, indent, width, refs, memo):
        yield indent + refs.get(id(self), "") + "Pointer (*"
        indent += "  "
        preamble = "index = "
        yield indent + preamble + self._format_array(self.indexarray, width - len(preamble) - len(indent))
        if id(self.target) in refs:
            yield indent + "ref   = " + refs[id(self.target)].strip()
        else:
            for line in self.target._format(indent, width, refs, set()):
                yield line
        yield indent + "*)"
