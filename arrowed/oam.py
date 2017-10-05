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
import sys

import numpy
import numpy.ma

import arrowed.proxy

if sys.version_info[0] <= 2:
    string_types = (unicode, str)
else:
    string_types = (str,)

class ObjectArrayMapping(object):
    def toJsonString(self):
        return json.dumps(self.toJson())

    @staticmethod
    def fromJsonString(string):
        return ObjectArrayMapping.fromJson(json.loads(string))

    def proxy(self, index):
        raise TypeError("cannot get a proxy for an unresolved ObjectArrayMap; call the resolved method first or pass a source to this method")

    def compile(self, function, paramtypes={}, env={}, numba={"nopython": True, "nogil": True}, debug=False):
        import arrowed.compiler
        paramtypes = paramtypes.copy()
        paramtypes[0] = self
        if not hasattr(self, "_functions"):
            self._functions = {}
        self._functions[id(function)] = arrowed.compiler.compile(function, paramtypes, env=env, numbaargs=numba, debug=debug)
        return self._functions[id(function)]

    def run(self, function, source, paramtypes={}, env={}, numba={"nopython": True, "nogil": True}, debug=False, *args):
        compiled = self.compile(function, paramtypes=paramtypes, env=env, numba=numba, debug=debug)

        resolved = {}
        for param in set(paramtypes).union(set([0])):
            resolved[param] = compiled.paramtypes[param].resolved(source)

        return compiled(resolved, *args)

    @staticmethod
    def _toint64(array):
        if array.dtype != numpy.dtype(numpy.int64):
            if isinstance(array, numpy.ma.MaskedArray) and array.mask is not None:
                return numpy.ma.MaskedArray(array, dtype=numpy.int64)
            else:
                return numpy.array(array, dtype=numpy.int64)
        else:
            return array

    @staticmethod
    def _resolved_check(array, message, extracheck):
        assert hasattr(array, "dtype") and not isinstance(array, numpy.recarray) and len(array.shape) == 1 and extracheck(array), message
        return array

    @staticmethod
    def _resolved(obj, source, message, extracheck=lambda x: True):
        if isinstance(obj, numpy.ndarray):
            return ObjectArrayMapping._resolved_check(obj, message, extracheck)

        elif callable(obj):
            if hasattr(obj, "__code__") and obj.__code__.co_argcount == 0:
                return ObjectArrayMapping._resolved_check(obj(), message, extracheck)
            else:
                return ObjectArrayMapping._resolved_check(obj(source), message, extracheck)

        elif isinstance(obj, collections.Hashable) and obj in source:
            return ObjectArrayMapping._resolved_check(source[obj], message, extracheck)

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

        elif isinstance(array, string_types + (bytes,)):
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

    def resolved(self, source, lazy=False, _memo=None):
        if lazy:
            return PrimitiveOAM(lambda: self._resolved(self.array, source, "PrimitiveOAM array must map to a one-dimensional, non-record array"), self)
        else:
            return PrimitiveOAM(self._resolved(self.array, source, "PrimitiveOAM array must map to a one-dimensional, non-record array"), self)

    def proxy(self, index):
        if callable(self.array):
            self.array = self.array()

        if isinstance(self.array, numpy.ma.MaskedArray) and self.array.mask is not None and self.array.mask[index]:
            return None
        else:
            return self.array[index]

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

    def resolved(self, source, lazy=False, _memo=None):
        def resolve():
            countarray = self._resolved(self.countarray, source, "ListCountOAM countarray must map to a one-dimensional, non-record array of integers", lambda x: issubclass(x.dtype.type, numpy.integer))
            offsetarray = numpy.empty(len(countarray) + 1, dtype=numpy.int64)   # new allocation
            countarray.cumsum(out=offsetarray[1:])                              # fill with offsets
            offsetarray[0] = 0
            startarray = offsetarray[:-1]  # overlapping views
            endarray = offsetarray[1:]     # overlapping views

            if isinstance(countarray, numpy.ma.MaskedArray) and countarray.mask is not None:
                startarray = numpy.ma.MaskedArray(startarray, mask=countarray.mask)

            return startarray, endarray

        _memo = self._recursion_check(_memo)
        if lazy:
            _memo[id(self)] = ListStartEndOAM(resolve, None, self.contents.resolved(source, lazy, _memo), self)
        else:
            startarray, endarray = resolve()
            _memo[id(self)] = ListStartEndOAM(startarray, endarray, self.contents.resolved(source, lazy, _memo), self)
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

    def resolved(self, source, lazy=False, _memo=None):
        def resolve():
            offsetarray = self._toint64(self._resolved(self.offsetarray, source, "ListOffsetOAM offsetarray must map to a one-dimensional, non-record array of integers", lambda x: issubclass(x.dtype.type, numpy.integer)))
            startarray = offsetarray[:-1]  # overlapping views
            endarray = offsetarray[1:]     # overlapping views
            return startarray, endarray

        _memo = self._recursion_check(_memo)
        if lazy:
            _memo[id(self)] = ListStartEndOAM(resolve, None, self.contents.resolved(source, lazy, _memo), self)
        else:
            startarray, endarray = resolve()
            _memo[id(self)] = ListStartEndOAM(startarray, endarray, self.contents.resolved(source, lazy, _memo), self)
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

    def resolved(self, source, lazy=False, _memo=None):
        def resolve():
            startarray = self._toint64(self._resolved(self.startarray, source, "ListStartEndOAM startarray must map to a one-dimensional, non-record array of integers", lambda x: issubclass(x.dtype.type, numpy.integer)))
            endarray = self._toint64(self._resolved(self.startarray, source, "ListStartEndOAM endarray must map to a one-dimensional, non-record array of integers", lambda x: issubclass(x.dtype.type, numpy.integer)))
            return startarray, endarray

        _memo = self._recursion_check(_memo)
        if lazy:
            _memo[id(self)] = ListStartEndOAM(resolve, None, self.contents.resolved(source, lazy, _memo), self)
        else:
            startarray, endarray = resolve()
            _memo[id(self)] = ListStartEndOAM(startarray, endarray, self.contents.resolved(source, lazy, _memo), self)
        return _memo[id(self)]

    def proxy(self, index):
        if callable(self.startarray):
            self.startarray, self.endarray = self.startarray()

        if isinstance(self.startarray, numpy.ma.MaskedArray) and self.startarray.mask is not None and self.startarray.mask[index]:
            return None
        else:
            return arrowed.proxy.ListProxy(self, index)

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
    __nameindex = 0

    def __init__(self, contents, base=None, name=None):
        self.contents = contents
        self.base = base
        if name is None:
            self.name = "Record-{0}".format(self.__nameindex)
            self.__nameindex += 1
        else:
            self.name = name

        assert isinstance(self.contents, dict)
        assert all(isinstance(x, string_types) for x in self.contents.keys()), "contents must be a dict from strings to ObjectArrayMappings"
        assert all(isinstance(x, ObjectArrayMapping) for x in self.contents.values()), "contents must be a dict from strings to ObjectArrayMappings"

        if self.base is None:
            superclasses = (arrowed.proxy.RecordProxy,)
        else:
            superclasses = self.base.proxyclass.__bases__

        def makeproperty(n, c):
            return property(lambda self: c.proxy(self._index))

        self.proxyclass = type(str(self.name), superclasses, dict((n, makeproperty(n, c)) for n, c in self.contents.items()))
        self.proxyclass.__slots__ = ["_oam", "_index"]
        
    def resolved(self, source, lazy=False, _memo=None):
        # a record is a purely organizational type; it has no arrays of its own, so just pass on the dereferencing request
        _memo = self._recursion_check(_memo)
        _memo[id(self)] = RecordOAM(dict((k, v.resolved(source, lazy, _memo)) for k, v in self.contents.items()), self, self.name)
        return _memo[id(self)]

    def proxy(self, index):
        return self.proxyclass(self, index)

    def _format(self, indent, width, refs, memo):
        self._recursion_check(memo)
        yield indent + refs.get(id(self), "") + "Record {"
        indent += "  "
        yield indent + "name = {0}".format(repr(self.name))

        for key, contents in self.contents.items():
            for line in contents._format_with_preamble("{0}: ".format(key), indent, width, refs, memo):
                yield line
        yield indent + "}"

    def __eq__(self, other):
        return isinstance(other, RecordOAM) and self.contents == other.contents and self.base == other.base and self.name == other.name

    def __ne__(self, other):
        return not self.__eq__(self, other)

class TupleOAM(ObjectArrayMapping):
    def __init__(self, contents, base=None):
        self.contents = tuple(contents)
        self.base = base
        assert all(isinstance(x, ObjectArrayMapping) for x in self.contents), "contents must be a tuple of ObjectArrayMappings"

    def resolved(self, source, lazy=False, _memo=None):
        # a tuple is a purely organizational type; it has no arrays of its own, so just pass on the dereferencing request
        _memo = self._recursion_check(_memo)
        _memo[id(self)] = TupleOAM(tuple(x.resolved(source, lazy, _memo) for x in self.contents), self)
        return _memo[id(self)]

    def proxy(self, index):
        return arrowed.proxy.TupleProxy(self, index)

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
        return isinstance(other, TupleOAM) and self.contents == other.contents and self.base == other.base

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

    def resolved(self, source, lazy=False, _memo=None):
        def resolve():
            tagarray = self._toint64(self._resolved(self.tagarray, source, "UnionSparseOAM tagarray must map to a one-dimensional, non-record array of integers", lambda x: issubclass(x.dtype.type, numpy.integer)))

            offsetarray = numpy.empty(len(tagarray), dtype=numpy.int64)
            for tag in range(len(self.contents)):    # for each possible tag
                matches = (tagarray == tag)          # find the elements of tagarray that match this tag
                nummatches = matches.sum()
                offsetarray[matches] = numpy.linspace(0, nummatches - 1, nummatches, dtype=numpy.int64)
                                                     # offsets corresponding to matching tags should be increasing integers
            return tagarray, offsetarray
        
        _memo = self._recursion_check(_memo)
        if lazy:
            _memo[id(self)] = UnionSparseOffsetOAM(resolve, None, tuple(x.resolved(source, lazy, _memo) for x in self.contents), self)
        else:
            tagarray, offsetarray = resolve()
            _memo[id(self)] = UnionSparseOffsetOAM(tagarray, offsetarray, tuple(x.resolved(source, lazy, _memo) for x in self.contents), self)
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

    def resolved(self, source, lazy=False, _memo=None):
        def resolve():
            tagarray = self._toint64(self._resolved(self.tagarray, source, "UnionSparseOffsetOAM tagarray must map to a one-dimensional, non-record array of integers", lambda x: issubclass(x.dtype.type, numpy.integer)))
            offsetarray = self._toint64(self._resolved(self.offsetarray, source, "UnionSparseOffsetOAM offsetarray must map to a one-dimensional, non-record array of integers", lambda x: issubclass(x.dtype.type, numpy.integer)))
            return tagarray, offsetarray

        _memo = self._recursion_check(_memo)
        if lazy:
            _memo[id(self)] = UnionSparseOffsetOAM(resolve, None, tuple(x.resolved(source, lazy, _memo) for x in self.contents), self)
        else:
            tagarray, offsetarray = resolve()
            _memo[id(self)] = UnionSparseOffsetOAM(tagarray, offsetarray, tuple(x.resolved(source, lazy, _memo) for x in self.contents), self)
        return _memo[id(self)]

    def proxy(self, index):
        if callable(self.tagarray):
            self.tagarray, self.offsetarray = self.tagarray()

        if isinstance(self.tagarray, numpy.ma.MaskedArray) and self.tagarray.mask is not None and self.tagarray.mask[index]:
            return None
        else:
            tag = self.tagarray[index]
            offset = self.offsetarray[index]
            return self.contents[tag].proxy(offset)

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

    def resolved(self, source, lazy=False, _memo=None):
        def resolve():
            return self._toint64(self._resolved(self.indexarray, source, "PointerOAM indexarray must map to a one-dimensional, non-record array of integers", lambda x: issubclass(x.dtype.type, numpy.integer)))

        # (only) pointers are allowed to reference themselves, but don't resolve the same pointer more than once
        if _memo is None:
            _memo = {}
        if id(self.target) not in _memo:
            self.target.resolved(source, lazy, _memo)

        if lazy:
            _memo[id(self)] = PointerOAM(resolve, _memo[id(self.target)], self)
        else:
            _memo[id(self)] = PointerOAM(resolve(), _memo[id(self.target)], self)
        return _memo[id(self)]

    def proxy(self, index):
        if callable(self.indexarray):
            self.indexarray = self.indexarray()

        if isinstance(self.indexarray, numpy.ma.MaskedArray) and self.indexarray.mask is not None and self.indexarray.mask[index]:
            return None
        else:
            offset = self.indexarray[index]
            return self.target.proxy(offset)

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
