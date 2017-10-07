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

import collections
import numbers
import json
import sys

import numpy
import numpy.ma

import arrowed.proxy

if sys.version_info[0] <= 2:
    string_types = (unicode, str)
else:
    string_types = (str,)

# Arrow layout reference:
# -----------------------
# 
# https://github.com/apache/arrow/blob/master/format/Layout.md
#
# FIXME: Structs (Record and Tuple) must optionally support missing data masks.
# FIXME: handle null BITmaps, not just BYTEmaps: is_valid[j] -> bitmap[j / 8] & (1 << (j % 8))

class ObjectArrayMapping(object):
    def toJsonString(self):
        return json.dumps(self.toJson())

    @staticmethod
    def fromJsonString(string):
        return ObjectArrayMapping.fromJson(json.loads(string))

    @property
    def name(self):
        base = self
        while base.base is not None:
            base = base.base
        return base._name

    @property
    def primaryarray(self):
        return None

    def hasbase(self, base):
        obj = self
        while obj is not None:
            if obj is base:
                return True
            obj = obj.base
        return False

    def proxy(self, index=0):
        raise TypeError("cannot get a proxy for an unresolved ObjectArrayMap; call the resolved method first or pass a source to this method")

    def compile(self, function, paramtypes={}, env={}, numba={"nopython": True, "nogil": True}, debug=False):
        import arrowed.compiler
        paramtypes = paramtypes.copy()
        paramtypes[0] = self

        return arrowed.compiler.compile(function, paramtypes, env=env, numbaargs=numba, debug=debug)

    def run(self, function, paramtypes={}, env={}, numba={"nopython": True, "nogil": True}, debug=False, *args):
        import arrowed.compiler

        if not isinstance(function, arrowed.compiler.Compiled):
            base = self
            while base.base is not None:
                base = base.base
            function = base.compile(function, paramtypes=paramtypes, env=env, numba=numba, debug=debug)

        return function(self, *args)

    @staticmethod
    def _toint32(array):
        if array.dtype != numpy.dtype(numpy.int32):
            if getattr(array, "mask", None) is not None:
                return numpy.ma.MaskedArray(array, dtype=numpy.int32)
            else:
                return numpy.array(array, dtype=numpy.int32)
        else:
            return array

    @staticmethod
    def _resolved_check(array, message, nullable, extracheck):
        if nullable:
            message = message.format("masked")
            extracheck2 = lambda x: getattr(x, "mask", None) is not None
        else:
            message = message.format("non-masked")
            extracheck2 = lambda x: getattr(x, "mask", None) is None
        assert hasattr(array, "dtype") and not isinstance(array, numpy.recarray) and len(array.shape) == 1 and extracheck(array) and extracheck2(array), message
        return array

    def _resolved(self, obj, source, message, nullable, extracheck=lambda x: True):
        if isinstance(obj, numpy.ndarray):
            return ObjectArrayMapping._resolved_check(obj, message, nullable, extracheck)

        elif callable(obj):
            if hasattr(obj, "__code__") and obj.__code__.co_argcount == 0:
                return ObjectArrayMapping._resolved_check(obj(), message, nullable, extracheck)
            elif hasattr(obj, "__code__") and obj.__code__.co_argcount == 1:
                return ObjectArrayMapping._resolved_check(obj(source), message, nullable, extracheck)
            elif hasattr(obj, "__code__") and obj.__code__.co_argcount == 2:
                return ObjectArrayMapping._resolved_check(obj(source, self), message, nullable, extracheck)
            else:
                return ObjectArrayMapping._resolved_check(obj(source, self, self.__class__), message, nullable, extracheck)

        elif isinstance(obj, collections.Hashable) and obj in source:
            return ObjectArrayMapping._resolved_check(source[obj], message, nullable, extracheck)

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
            
            if getattr(array, "mask", None) is not None:
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
                
    def format(self, indent="", highlight=lambda t: "", width=80):
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

        return "\n".join(self._format(indent, width, refs, {}))

################################################################ primitives

class Primitive(ObjectArrayMapping):
    def __init__(self, array, nullable=False, base=None):
        self.array = array
        self.nullable = nullable
        self.base = base

    def walk(self, rootfirst=True, _memo=None):
        yield self

    def accessedby(self, accessor, feedself=False, _memo=None):
        return Primitive(accessor(self) if feedself else accessor, self.nullable, self)

    def findbybase(self, base, _memo=None):
        if self.hasbase(base):
            return self
        else:
            return None

    @property
    def _name(self):
        if isinstance(self.array, string_types):
            return self.array
        else:
            return None

    @property
    def primaryarray(self):
        return self.array

    def resolved(self, source, lazy=False, _memo=None):
        def resolve():
            return self._resolved(self.array, source, "Primitive array must map to a one-dimensional, {0}, non-record array", self.nullable)

        if lazy:
            return Primitive(resolve, self.nullable, self)
        else:
            return Primitive(resolve(), self.nullable, self)

    def proxy(self, index=0):
        if callable(self.array):
            self.array = self.array()

        if getattr(self.array, "mask", None) is not None and self.array.mask[index]:
            return None
        else:
            return self.array[index]

    def get(self, attr):
        if callable(self.array):
            self.array = self.array()

        if attr == "array":
            return self.array
        else:
            raise NameError("Primitive has no array {0}".format(repr(attr)))

    def members(self, _memo=None):
        return [self]

    def hasany(self, others, _memo=None):
        return any(x is self for x in others)

    def projection(self, required, _memo=None):
        if self.hasany(required):
            return Primitive(self.array, self.nullable, self)
        else:
            return None

    def isinstance(self, obj, _memo=None):
        if _memo is None:
            _memo = set()
        if id(self) in _memo:
            return False
        else:
            _memo.add(id(self))

        if isinstance(self.array, numpy.dtype):
            dtype = self.array
        elif isinstance(self.array, tuple) and isinstance(self.array[1], numpy.dtype):
            dtype = self.array[1]
        elif hasattr(self.array, "dtype"):
            dtype = self.array.dtype
        else:
            raise TypeError("cannot determine dtype of {0} with array {1}".format(self, self.array))

        if obj is None and self.nullable:
            return True
        elif (obj is False or obj is True) and str(dtype) == "bool":
            return True
        elif obj is not False and obj is not True and isinstance(obj, numbers.Integral) and issubclass(dtype.type, numpy.integer) and numpy.iinfo(dtype.type).min <= obj <= numpy.iinfo(dtype.type).max:
            return True
        elif isinstance(obj, numbers.Real) and issubclass(dtype.type, numpy.floating):
            return True
        elif isinstance(obj, numbers.Complex) and issubclass(dtype.type, numpy.complex):
            return True
        else:
            return False
        
    def _format_with_preamble(self, preamble, indent, width, refs, memo):
        for line in self._format(indent, width - len(preamble), refs, memo):
            yield indent + preamble + line[len(indent):]

    def _format(self, indent, width, refs, memo):
        self._recursion_check(memo)
        preamble = refs.get(id(self), "")
        yield indent + preamble + self._format_array(self.array, width - len(preamble) - len(indent))

    def __eq__(self, other):
        return isinstance(other, Primitive) and ((isinstance(self.array, ndarray) and isinstance(other.array, ndarray) and numpy.array_equal(self.array, other.array)) or self.array == other.array) and self.base == other.base

    def __ne__(self, other):
        return not self.__eq__(self, other)

################################################################ lists

class List(ObjectArrayMapping):
    def __init__(self, *args, **kwds):
        raise TypeError("List is abstract; use ListCount, ListOffset, or ListBeginEnd instead")

    def walk(self, rootfirst=True, _memo=None):
        if _memo is None:
            _memo = set()
        if id(self) not in _memo:
            _memo.add(id(self))
            if rootfirst:
                yield self
            for x in self.contents.walk(rootfirst, _memo):
                yield x
            if not rootfirst:
                yield self

    def findbybase(self, base, _memo=None):
        if self.hasbase(base):
            return self
        else:
            if _memo is None:
                _memo = set()
            if id(self.contents) not in _memo:
                _memo.add(id(self.contents))
                return self.contents.findbybase(base, _memo)
            else:
                return None

    def members(self, _memo=None):
        if _memo is None:
            _memo = set()
        out = [self]
        if id(self.contents) not in _memo:
            _memo.add(id(self.contents))
            return out + self.contents.members(_memo)
        else:
            return out

    def hasany(self, others, _memo=None):
        if any(x is self for x in others):
            return True
        if _memo is None:
            _memo = set()
        if id(self.contents) not in _memo:
            _memo.add(id(self.contents))
            return self.contents.hasany(others, _memo)
        else:
            return False

    def isinstance(self, obj, _memo=None):
        if _memo is None:
            _memo = set()
        if id(self) in _memo:
            return False
        else:
            _memo.add(id(self))

        if obj is None and self.nullable:
            return True
        try:
            iter(obj)
            if isinstance(obj, dict) or (isinstance(obj, tuple) and hasattr(obj, "_fields")):
                raise TypeError
        except TypeError:
            return False
        else:
            return all(self.contents.isinstance(x) for x in obj)

class ListCount(List):
    def __init__(self, countarray, contents, nullable=False, base=None):
        self.countarray = countarray
        self.contents = contents
        self.nullable = nullable
        self.base = base
        assert isinstance(self.contents, ObjectArrayMapping), "contents must be an ObjectArrayMapping"

    def accessedby(self, accessor, feedself=False, _memo=None):
        if _memo is None:
            _memo = {}
        if id(self.contents) not in _memo:
            _memo[id(self.contents)] = None
            _memo[id(self.contents)] = self.contents.accessedby(accessor, feedself, _memo)
        contents = _memo[id(self.contents)]
        return ListCount(accessor(self) if feedself else accessor, contents, self.nullable, self)

    @property
    def _name(self):
        if isinstance(self.countarray, string_types):
            return self.countarray
        else:
            return None

    @property
    def primaryarray(self):
        return self.countarray

    def resolved(self, source, lazy=False, _memo=None):
        def resolve():
            countarray = self._resolved(self.countarray, source, "ListCount countarray must map to a one-dimensional, {0}, non-record array of integers", self.nullable, lambda x: issubclass(x.dtype.type, numpy.integer))
            offsetarray = numpy.empty(len(countarray) + 1, dtype=numpy.int32)   # new allocation
            countarray.cumsum(out=offsetarray[1:])                              # fill with offsets
            offsetarray[0] = 0
            beginarray = offsetarray[:-1]  # overlapping views
            endarray = offsetarray[1:]     # overlapping views

            if getattr(countarray, "mask", None) is not None:
                beginarray = numpy.ma.MaskedArray(beginarray, mask=countarray.mask)

            return beginarray, endarray

        _memo = self._recursion_check(_memo)
        if lazy:
            _memo[id(self)] = ListBeginEnd(resolve, None, self.contents.resolved(source, lazy, _memo), self.nullable, self)
        else:
            beginarray, endarray = resolve()
            _memo[id(self)] = ListBeginEnd(beginarray, endarray, self.contents.resolved(source, lazy, _memo), self.nullable, self)
        return _memo[id(self)]

    def get(self, attr):
        if callable(self.countarray):
            self.countarray = self.countarray()

        if attr == "countarray":
            return self.countarray
        else:
            raise NameError("ListCount has no array {0}".format(repr(attr)))

    def projection(self, required, _memo=None):
        if self.hasany(required):
            if _memo is None:
                _memo = {}
            if id(self.contents) not in _memo:
                _memo[id(self.contents)] = None
                _memo[id(self.contents)] = self.contents.projection(required, _memo)
            contents = _memo[id(self.contents)]
            if contents is None:
                contents = Primitive(self.countarray, self.nullable)
            return ListCount(self.countarray, contents, self.nullable, self)
        else:
            return None

    def _format(self, indent, width, refs, memo):
        self._recursion_check(memo)
        yield indent + refs.get(id(self), "") + "List" + (" (nullable)" if self.nullable else "") + " ["
        indent += "  "
        preamble = "countarray = "
        yield indent + preamble + self._format_array(self.countarray, width - len(preamble) - len(indent))
        for line in self.contents._format(indent, width, refs, memo):
            yield line
        yield indent + "]"

    def __eq__(self, other):
        return isinstance(other, ListCount) and ((isinstance(self.countarray, ndarray) and isinstance(other.countarray, ndarray) and numpy.array_equal(self.countarray, other.countarray)) or self.countarray == other.countarray) and self.contents == other.contents and self.base == other.base

    def __ne__(self, other):
        return not self.__eq__(self, other)

class ListOffset(List):
    def __init__(self, offsetarray, contents, nullable=False, base=None):
        self.offsetarray = offsetarray
        self.contents = contents
        self.nullable = nullable
        self.base = base
        assert isinstance(self.contents, ObjectArrayMapping), "contents must be an ObjectArrayMapping"

    def accessedby(self, accessor, feedself=False, _memo=None):
        if _memo is None:
            _memo = {}
        if id(self.contents) not in _memo:
            _memo[id(self.contents)] = None
            _memo[id(self.contents)] = self.contents.accessedby(accessor, feedself, _memo)
        contents = _memo[id(self.contents)]
        return ListOffset(accessor(self) if feedself else accessor, contents, self.nullable, self)

    @property
    def _name(self):
        if isinstance(self.offsetarray, string_types):
            return self.offsetarray
        else:
            return None

    @property
    def primaryarray(self):
        return self.offsetarray

    def resolved(self, source, lazy=False, _memo=None):
        def resolve():
            offsetarray = self._toint32(self._resolved(self.offsetarray, source, "ListOffset offsetarray must map to a one-dimensional, {0}, non-record array of integers", self.nullable, lambda x: issubclass(x.dtype.type, numpy.integer)))
            beginarray = offsetarray[:-1]  # overlapping views
            endarray = offsetarray[1:]     # overlapping views
            return beginarray, endarray

        _memo = self._recursion_check(_memo)
        if lazy:
            _memo[id(self)] = ListBeginEnd(resolve, None, self.contents.resolved(source, lazy, _memo), self.nullable, self)
        else:
            beginarray, endarray = resolve()
            _memo[id(self)] = ListBeginEnd(beginarray, endarray, self.contents.resolved(source, lazy, _memo), self.nullable, self)
        return _memo[id(self)]

    def get(self, attr):
        if callable(self.offsetarray):
            self.offsetarray = self.offsetarray()

        if attr == "offsetarray":
            return self.offsetarray
        else:
            raise NameError("ListOffset has no array {0}".format(repr(attr)))

    def projection(self, required, _memo=None):
        if self.hasany(required):
            if _memo is None:
                _memo = {}
            if id(self.contents) not in _memo:
                _memo[id(self.contents)] = None
                _memo[id(self.contents)] = self.contents.projection(required, _memo)
            contents = _memo[id(self.contents)]
            if contents is None:
                contents = Primitive(self.offsetarray, self.nullable)
            return ListOffset(self.offsetarray, contents, self.nullable, self)
        else:
            return None

    def _format(self, indent, width, refs, memo):
        self._recursion_check(memo)
        yield indent + refs.get(id(self), "") + "List" + (" (nullable)" if self.nullable else "") + " ["
        indent += "  "
        preamble = "offsetarray = "
        yield indent + preamble + self._format_array(self.offsetarray, width - len(preamble) - len(indent))
        for line in self.contents._format(indent, width, refs, memo):
            yield line
        yield indent + "]"

    def __eq__(self, other):
        return isinstance(other, ListOffset) and ((isinstance(self.offsetarray, ndarray) and isinstance(other.offsetarray, ndarray) and numpy.array_equal(self.offsetarray, other.offsetarray)) or self.offsetarray == other.offsetarray) and self.contents == other.contents and self.base == other.base

    def __ne__(self, other):
        return not self.__eq__(self, other)
        
class ListBeginEnd(List):
    def __init__(self, beginarray, endarray, contents, nullable=False, base=None):
        self.beginarray = beginarray
        self.endarray = endarray
        self.contents = contents
        self.nullable = nullable
        self.base = base
        assert isinstance(self.contents, ObjectArrayMapping), "contents must be an ObjectArrayMapping"

    def accessedby(self, accessor, feedself=False, _memo=None):
        if _memo is None:
            _memo = {}
        if id(self.contents) not in _memo:
            _memo[id(self.contents)] = None
            _memo[id(self.contents)] = self.contents.accessedby(accessor, feedself, _memo)
        contents = _memo[id(self.contents)]

        result = accessor(self) if feedself else accessor
        if isinstance(result, tuple) and len(result) == 2:
            return ListBeginEnd(result[0], result[1], contents, self.nullable, self)
        else:
            return ListBeginEnd(result, None, contents, self.nullable, self)

    @property
    def _name(self):
        if isinstance(self.beginarray, string_types):
            return self.beginarray
        else:
            return None

    @property
    def primaryarray(self):
        return self.beginarray

    def resolved(self, source, lazy=False, _memo=None):
        def resolve():
            beginarray = self._toint32(self._resolved(self.beginarray, source, "ListBeginEnd beginarray must map to a one-dimensional, {0}, non-record array of integers", self.nullable, lambda x: issubclass(x.dtype.type, numpy.integer)))
            endarray = self._toint32(self._resolved(self.beginarray, source, "ListBeginEnd endarray must map to a one-dimensional, {0}, non-record array of integers", self.nullable, lambda x: issubclass(x.dtype.type, numpy.integer)))
            return beginarray, endarray

        _memo = self._recursion_check(_memo)
        if lazy:
            _memo[id(self)] = ListBeginEnd(resolve, None, self.contents.resolved(source, lazy, _memo), self.nullable, self)
        else:
            beginarray, endarray = resolve()
            _memo[id(self)] = ListBeginEnd(beginarray, endarray, self.contents.resolved(source, lazy, _memo), self.nullable, self)
        return _memo[id(self)]

    def proxy(self, index=0):
        if callable(self.beginarray):
            self.beginarray, self.endarray = self.beginarray()

        if (getattr(self.beginarray, "mask", None) is not None and self.beginarray.mask[index]) or (getattr(self.endarray, "mask", None) is not None and self.endarray.mask[index]):
            return None
        else:
            return arrowed.proxy.ListProxy(self, index)

    def get(self, attr):
        if callable(self.beginarray):
            self.beginarray, self.endarray = self.beginarray()

        if attr == "beginarray":
            return self.beginarray
        elif attr == "endarray":
            return self.endarray
        else:
            raise NameError("ListBeginEnd has no array {0}".format(repr(attr)))

    def projection(self, required, _memo=None):
        if self.hasany(required):
            if _memo is None:
                _memo = {}
            if id(self.contents) not in _memo:
                _memo[id(self.contents)] = None
                _memo[id(self.contents)] = self.contents.projection(required, _memo)
            contents = _memo[id(self.contents)]
            if contents is None:
                contents = Primitive(self.beginarray, self.nullable)
            return ListBeginEnd(self.beginarray, self.endarray, contents, self.nullable, self)
        else:
            return None

    def _format(self, indent, width, refs, memo):
        self._recursion_check(memo)
        yield indent + refs.get(id(self), "") + "List" + (" (nullable)" if self.nullable else "") + " ["
        indent += "  "
        preamble = "beginarray = "
        yield indent + preamble + self._format_array(self.beginarray, width - len(preamble) - len(indent))
        preamble = "endarray   = "
        yield indent + preamble + self._format_array(self.endarray, width - len(preamble) - len(indent))
        for line in self.contents._format(indent, width, refs, memo):
            yield line
        yield indent + "]"

    def __eq__(self, other):
        return isinstance(other, ListBeginEnd) and ((isinstance(self.beginarray, ndarray) and isinstance(other.beginarray, ndarray) and numpy.array_equal(self.beginarray, other.beginarray)) or self.beginarray == other.beginarray) and ((isinstance(self.endarray, ndarray) and isinstance(other.endarray, ndarray) and numpy.array_equal(self.endarray, other.endarray)) or self.endarray == other.endarray) and self.contents == other.contents and self.base == other.base

    def __ne__(self, other):
        return not self.__eq__(self, other)

################################################################ records and tuples

class Struct(ObjectArrayMapping):
    """We call a Struct with field names a "Record" and a Struct without field names a "Tuple". In Arrow."""
    pass

class Record(Struct):
    __nameindex = 0

    def __init__(self, contents, base=None, name=None):
        self.contents = contents
        self.base = base
        if name is None:
            self._name = "Record-{0}".format(self.__nameindex)
            self.__nameindex += 1
        else:
            self._name = name

        assert isinstance(self.contents, dict)
        assert all(isinstance(x, string_types) for x in self.contents.keys()), "contents must be a dict from strings to ObjectArrayMappings"
        assert all(isinstance(x, ObjectArrayMapping) for x in self.contents.values()), "contents must be a dict from strings to ObjectArrayMappings"

        if self.base is None:
            superclasses = (arrowed.proxy.RecordProxy,)
        else:
            superclasses = self.base.proxyclass.__bases__

        def makeproperty(n, c):
            return property(lambda self: c.proxy(self._index))

        self.proxyclass = type(self._name, superclasses, dict((n, makeproperty(n, c)) for n, c in self.contents.items()))
        self.proxyclass.__slots__ = ["_schema", "_index"]

    def walk(self, rootfirst=True, _memo=None):
        if _memo is None:
            _memo = set()
        if id(self) not in _memo:
            _memo.add(id(self))
            if rootfirst:
                yield self
            for x in self.contents.value():
                for y in x.walk(rootfirst, _memo):
                    yield y
            if not rootfirst:
                yield self

    def accessedby(self, accessor, feedself=False, _memo=None):
        if _memo is None:
            _memo = {}
        contents = collections.OrderedDict()
        for n, c in self.contents.items():
            if id(c) not in _memo:
                _memo[id(c)] = None
                _memo[id(c)] = c.accessedby(accessor, feedself, _memo)
            contents[n] = _memo[id(c)]
        return Record(contents, self)

    def findbybase(self, base, _memo=None):
        if self.hasbase(base):
            return self
        else:
            if _memo is None:
                _memo = set()
            for x in self.contents.values():
                if id(x) not in _memo:
                    _memo.add(id(x))
                    out = x.findbybase(base, _memo)
                    if out is not None:
                        return out
            return None

    def resolved(self, source, lazy=False, _memo=None):
        # a record is a purely organizational type; it has no arrays of its own, so just pass on the dereferencing request
        _memo = self._recursion_check(_memo)
        _memo[id(self)] = Record(collections.OrderedDict((k, v.resolved(source, lazy, _memo)) for k, v in self.contents.items()), self)
        return _memo[id(self)]

    def proxy(self, index=0):
        return self.proxyclass(self, index)

    def get(self, attr):
        raise NameError("Record has no array {0}".format(repr(attr)))

    def members(self, _memo=None):
        if _memo is None:
            _memo = set()
        out = [self]
        for x in self.contents.values():
            if id(x) not in _memo:
                _memo.add(id(x))
                out.extend(x.members(_memo))
        return out

    def hasany(self, others, _memo=None):
        if any(x is self for x in others):
            return True
        if _memo is None:
            _memo = set()
        for x in self.contents.values():
            if id(x) not in _memo:
                _memo.add(id(x))
                return x.hasany(others, _memo)
        return False

    def projection(self, required, _memo=None):
        if self.hasany(required):
            if _memo is None:
                _memo = {}
            contents = collections.OrderedDict()
            for n, x in self.contents.items():
                if id(x) not in _memo:
                    _memo[id(x)] = None
                    _memo[id(x)] = x.projection(required, _memo)
                content = _memo[id(x)]
                if content is not None:
                    contents[n] = content
            if len(contents) > 0:
                return Record(contents, self)
            else:
                return None
        else:
            return None

    def isinstance(self, obj, _memo=None):
        if _memo is None:
            _memo = set()
        if id(self) in _memo:
            return False
        else:
            _memo.add(id(self))

        # if obj is None and self.nullable:
        #     return True
        if isinstance(obj, dict):
            return all(n in obj and c.isinstance(obj[n]) for n, c in self.contents.items())
        else:
            return all(hasattr(obj, n) and c.isinstance(getattr(obj, n)) for n, c in self.contents.items())

    def _format(self, indent, width, refs, memo):
        self._recursion_check(memo)
        yield indent + refs.get(id(self), "") + "Record {"   # FIXME + (" (nullable)" if self.nullable else "")
        indent += "  "
        if self._name is not None:
            yield indent + "name = {0}".format(repr(self._name))

        for key, contents in self.contents.items():
            for line in contents._format_with_preamble("{0}: ".format(key), indent, width, refs, memo):
                yield line
        yield indent + "}"

    def __eq__(self, other):
        return isinstance(other, Record) and self.contents == other.contents and self.base == other.base and self._name == other._name

    def __ne__(self, other):
        return not self.__eq__(self, other)

class Tuple(Struct):
    def __init__(self, contents, base=None, name=None):
        self.contents = tuple(contents)
        self.base = base
        self._name = name
        assert all(isinstance(x, ObjectArrayMapping) for x in self.contents), "contents must be a tuple of ObjectArrayMappings"

    def walk(self, rootfirst=True, _memo=None):
        if _memo is None:
            _memo = set()
        if id(self) not in _memo:
            _memo.add(id(self))
            if rootfirst:
                yield self
            for x in self.contents:
                for y in x.walk(rootfirst, _memo):
                    yield y
            if not rootfirst:
                yield self

    def accessedby(self, accessor, feedself=False, _memo=None):
        if _memo is None:
            _memo = {}
        contents = []
        for c in self.contents:
            if id(c) not in _memo:
                _memo[id(c)] = None
                _memo[id(c)] = c.accessedby(accessor, feedself, _memo)
            contents.append(_memo[id(c)])
        return Tuple(contents, self)

    def findbybase(self, base, _memo=None):
        if self.hasbase(base):
            return self
        else:
            if _memo is None:
                _memo = set()
            for x in self.contents:
                if id(x) not in _memo:
                    _memo.add(id(x))
                    out = x.findbybase(base, _memo)
                    if out is not None:
                        return out
            return None

    def resolved(self, source, lazy=False, _memo=None):
        # a tuple is a purely organizational type; it has no arrays of its own, so just pass on the dereferencing request
        _memo = self._recursion_check(_memo)
        _memo[id(self)] = Tuple(tuple(x.resolved(source, lazy, _memo) for x in self.contents), self)
        return _memo[id(self)]

    def proxy(self, index=0):
        return arrowed.proxy.TupleProxy(self, index)

    def get(self, attr):
        raise NameError("Tuple has no array {0}".format(repr(attr)))

    def members(self, _memo=None):
        if _memo is None:
            _memo = set()
        out = [self]
        for x in self.contents:
            if id(x) not in _memo:
                _memo.add(id(x))
                out.extend(x.members(_memo))
        return out

    def hasany(self, others, _memo=None):
        if any(x is self for x in others):
            return True
        if _memo is None:
            _memo = set()
        for x in self.contents:
            if id(x) not in _memo:
                _memo.add(id(x))
                return x.hasany(others, _memo)
        return False

    def projection(self, required, _memo=None):
        if self.hasany(required):
            if _memo is None:
                _memo = {}
            contents = []
            for x in self.contents:
                if id(x) not in _memo:
                    _memo[id(x)] = None
                    _memo[id(x)] = x.projection(required, _memo)
                content = _memo[id(x)]
                if content is not None:
                    contents.append(content)
            if len(contents) > 0:
                return Tuple(contents, self)
            else:
                return None
        else:
            return None

    def isinstance(self, obj, _memo=None):
        if _memo is None:
            _memo = set()
        if id(self) in _memo:
            return False
        else:
            _memo.add(id(self))

        # if obj is None and self.nullable:
        #     return True
        if isinstance(obj, tuple) and len(obj) == len(self.contents):
            return all(c.isinstance(x) for x, c in zip(obj, self.contents))
        else:
            return False

    def _format(self, indent, width, refs, memo):
        self._recursion_check(memo)
        yield indent + refs.get(id(self), "") + "Tuple ("   # FIXME + (" (nullable)" if self.nullable else "")
        indent += "  "
        if self._name is not None:
            yield indent + "name = {0}".format(repr(self._name))

        for index, contents in enumerate(self.contents):
            for line in contents._format_with_preamble("{0}: ".format(index), indent, width, refs, memo):
                yield line
        yield indent + ")"

    def __eq__(self, other):
        return isinstance(other, Tuple) and self.contents == other.contents and self.base == other.base

    def __ne__(self, other):
        return not self.__eq__(self, other)

################################################################ unions

class Union(ObjectArrayMapping):
    def __init__(self, *args, **kwds):
        raise TypeError("Union is abstract; use UnionDense or UnionDenseOffset instead")

    def walk(self, rootfirst=True, _memo=None):
        if _memo is None:
            _memo = set()
        if id(self) not in _memo:
            _memo.add(id(self))
            if rootfirst:
                yield self
            for x in self.contents:
                for y in x.walk(rootfirst, _memo):
                    yield y
            if not rootfirst:
                yield self

    def findbybase(self, base, _memo=None):
        if self.hasbase(base):
            return self
        else:
            if _memo is None:
                _memo = set()
            for x in self.contents:
                if id(x) not in _memo:
                    _memo.add(id(x))
                    out = x.findbybase(base, _memo)
                    if out is not None:
                        return out
            return None

    def members(self, _memo=None):
        if _memo is None:
            _memo = set()
        out = [self]
        for x in self.contents:
            if id(x) not in _memo:
                _memo.add(id(x))
                out.extend(x.members(_memo))
        return out

    def hasany(self, others, _memo=None):
        if any(x is self for x in others):
            return True
        if _memo is None:
            _memo = set()
        for x in self.contents:
            if id(x) not in _memo:
                _memo.add(id(x))
                return x.hasany(others, _memo)
        return False

    def isinstance(self, obj, _memo=None):
        if _memo is None:
            _memo = set()
        if id(self) in _memo:
            return False
        else:
            _memo.add(id(self))

        if obj is None and self.nullable:
            return True
        return any(c.isinstance(obj) for c in self.contents)

class UnionDense(Union):
    def __init__(self, tagarray, contents, nullable=False, base=None):
        self.tagarray = tagarray
        self.contents = tuple(contents)
        self.nullable = nullable
        self.base = base
        if isinstance(self.contents, tuple):
            assert all(isinstance(x, ObjectArrayMapping) for x in self.contents), "contents must be a tuple of ObjectArrayMappings"
        else:
            raise AssertionError("contents must be a tuple")

    def accessedby(self, accessor, feedself=False, _memo=None):
        if _memo is None:
            _memo = {}
        contents = []
        for c in self.contents:
            if id(c) not in _memo:
                _memo[id(c)] = None
                _memo[id(c)] = c.accessedby(accessor, feedself, _memo)
            contents.append(_memo[id(c)])
        return UnionDense(accessor(self) if feedself else accessor, contents, self.nullable, self)

    @property
    def _name(self):
        if isinstance(self.tagarray, string_types):
            return self.tagarray
        else:
            return None

    @property
    def primaryarray(self):
        return self.tagarray

    def resolved(self, source, lazy=False, _memo=None):
        def resolve():
            tagarray = self._toint32(self._resolved(self.tagarray, source, "UnionDense tagarray must map to a one-dimensional, {0}, non-record array of integers", self.nullable, lambda x: issubclass(x.dtype.type, numpy.integer)))

            offsetarray = numpy.empty(len(tagarray), dtype=numpy.int32)
            for tag in range(len(self.contents)):    # for each possible tag
                matches = (tagarray == tag)          # find the elements of tagarray that match this tag
                nummatches = matches.sum()
                offsetarray[matches] = numpy.linspace(0, nummatches - 1, nummatches, dtype=numpy.int32)
                                                     # offsets corresponding to matching tags should be increasing integers
            return tagarray, offsetarray
        
        _memo = self._recursion_check(_memo)
        if lazy:
            _memo[id(self)] = UnionDenseOffset(resolve, None, [x.resolved(source, lazy, _memo) for x in self.contents], self.nullable, self)
        else:
            tagarray, offsetarray = resolve()
            _memo[id(self)] = UnionDenseOffset(tagarray, offsetarray, [x.resolved(source, lazy, _memo) for x in self.contents], self.nullable, self)
        return _memo[id(self)]

    def get(self, attr):
        if callable(self.tagarray):
            self.tagarray = self.tagarray()

        if attr == "tagarray":
            return self.tagarray
        else:
            raise NameError("UnionDense has no array {0}".format(repr(attr)))

    def projection(self, required, _memo=None):
        if self.hasany(required):
            if _memo is None:
                _memo = {}
            contents = []
            for x in self.contents:
                if id(x) not in _memo:
                    _memo[id(x)] = None
                    _memo[id(x)] = x.projection(required, _memo)
                content = _memo[id(x)]
                if content is not None:
                    contents.append(content)
            if len(contents) > 0:
                return UnionDense(self.tagarray, contents, self.nullable, self)
            else:
                return None
        else:
            return None

    def _format(self, indent, width, refs, memo):
        self._recursion_check(memo)
        yield indent + refs.get(id(self), "") + "Union" + (" (nullable)" if self.nullable else "") + " <"
        indent += "  "
        preamble = "tagarray = "
        yield indent + preamble + self._format_array(self.tagarray, width - len(preamble) - len(indent))
        for index, contents in enumerate(self.contents):
            for line in contents._format_with_preamble("{0}: ".format(index), indent, width, refs, memo):
                yield line
        yield indent + ">"

    def __eq__(self, other):
        return isinstance(other, UnionDense) and ((isinstance(self.tagarray, ndarray) and isinstance(other.tagarray, ndarray) and numpy.array_equal(self.tagarray, other.tagarray)) or self.tagarray == other.tagarray) and self.contents == other.contents and self.base == other.base

    def __ne__(self, other):
        return not self.__eq__(self, other)

class UnionDenseOffset(Union):
    def __init__(self, tagarray, offsetarray, contents, nullable=False, base=None):
        self.tagarray = tagarray
        self.offsetarray = offsetarray
        self.contents = tuple(contents)
        self.nullable = nullable
        self.base = base
        if isinstance(self.contents, tuple):
            assert all(isinstance(x, ObjectArrayMapping) for x in self.contents), "contents must be a tuple of ObjectArrayMappings"
        else:
            raise AssertionError("contents must be a tuple")

    def accessedby(self, accessor, feedself=False, _memo=None):
        if _memo is None:
            _memo = {}
        contents = []
        for c in self.contents:
            if id(c) not in _memo:
                _memo[id(c)] = None
                _memo[id(c)] = c.accessedby(accessor, feedself, _memo)
            contents.append(_memo[id(c)])

        result = accessor(self) if feedself else accessor
        if isinstance(result, tuple) and len(result) == 2:
            return UnionDenseOffset(result[0], result[1], contents, self.nullable, self)
        else:
            return UnionDenseOffset(result, None, contents, self.nullable, self)
        
    @property
    def _name(self):
        if isinstance(self.tagarray, string_types):
            return self.tagarray
        else:
            return None

    @property
    def primaryarray(self):
        return self.tagarray

    def resolved(self, source, lazy=False, _memo=None):
        def resolve():
            tagarray = self._toint32(self._resolved(self.tagarray, source, "UnionDenseOffset tagarray must map to a one-dimensional, {0}, non-record array of integers", self.nullable, lambda x: issubclass(x.dtype.type, numpy.integer)))
            offsetarray = self._toint32(self._resolved(self.offsetarray, source, "UnionDenseOffset offsetarray must map to a one-dimensional, {0}, non-record array of integers", self.nullable, lambda x: issubclass(x.dtype.type, numpy.integer)))
            return tagarray, offsetarray

        _memo = self._recursion_check(_memo)
        if lazy:
            _memo[id(self)] = UnionDenseOffset(resolve, None, [x.resolved(source, lazy, _memo) for x in self.contents], self.nullable, self)
        else:
            tagarray, offsetarray = resolve()
            _memo[id(self)] = UnionDenseOffset(tagarray, offsetarray, [x.resolved(source, lazy, _memo) for x in self.contents], self.nullable, self)
        return _memo[id(self)]

    def proxy(self, index=0):
        if callable(self.tagarray):
            self.tagarray, self.offsetarray = self.tagarray()

        if (getattr(self.tagarray, "mask", None) is not None and self.tagarray.mask[index]) or (getattr(self.offsetarray, "mask", None) is not None and self.offsetarray.mask[index]):
            return None
        else:
            tag = self.tagarray[index]
            offset = self.offsetarray[index]
            return self.contents[tag].proxy(offset)

    def get(self, attr):
        if callable(self.tagarray):
            self.tagarray, self.offsetarray = self.tagarray()

        if attr == "tagarray":
            return self.tagarray
        elif attr == "offsetarray":
            return self.offsetarray
        else:
            raise NameError("UnionDenseOffset has no array {0}".format(repr(attr)))

    def projection(self, required, _memo=None):
        if self.hasany(required):
            if _memo is None:
                _memo = {}
            contents = []
            for x in self.contents:
                if id(x) not in _memo:
                    _memo[id(x)] = None
                    _memo[id(x)] = x.projection(required, _memo)
                content = _memo[id(x)]
                if content is not None:
                    contents.append(content)
            if len(contents) > 0:
                return UnionDenseOffset(self.tagarray, self.offsetarray, contents, self.nullable, self)
            else:
                return None
        else:
            return None

    def _format(self, indent, width, refs, memo):
        self._recursion_check(memo)
        yield indent + refs.get(id(self), "") + "Union" + (" (nullable)" if self.nullable else "") + " <"
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
        return isinstance(other, UnionDenseOffset) and ((isinstance(self.tagarray, ndarray) and isinstance(other.tagarray, ndarray) and numpy.array_equal(self.tagarray, other.tagarray)) or self.tagarray == other.tagarray) and ((isinstance(self.offsetarray, ndarray) and isinstance(other.offsetarray, ndarray) and numpy.array_equal(self.offsetarray, other.offsetarray)) or self.offsetarray == other.offsetarray) and self.contents == other.contents and self.base == other.base

    def __ne__(self, other):
        return not self.__eq__(self, other)

################################################################ pointers

class Pointer(ObjectArrayMapping):
    def __init__(self, indexarray, target, nullable=False, base=None):
        self.indexarray = indexarray
        self.target = target
        self.nullable = nullable
        self.base = base
        assert isinstance(self.target, ObjectArrayMapping), "target must be an ObjectArrayMapping"
        assert self.target is not self, "pointer's target may contain the pointer, but it must not be the pointer itself"

    def walk(self, rootfirst=True, _memo=None):
        if _memo is None:
            _memo = set()
        if id(self) not in _memo:
            _memo.add(id(self))
            if rootfirst:
                yield self
            for x in self.target.walk(rootfirst, _memo):
                yield x
            if not rootfirst:
                yield self

    def accessedby(self, accessor, feedself=False, _memo=None):
        if _memo is None:
            _memo = {}
        if id(self.target) not in _memo:
            _memo[id(self.target)] = None
            _memo[id(self.target)] = self.target.accessedby(accessor, feedself, _memo)
        target = _memo[id(self.target)]
        return Pointer(accessor(self) if feedself else accessor, target, self.nullable, self)

    def findbybase(self, base, _memo=None):
        if self.hasbase(base):
            return self
        else:
            if _memo is None:
                _memo = set()
            if id(self.target) not in _memo:
                _memo.add(id(self.target))
                return self.target.findbybase(base, _memo)
            else:
                return None

    @property
    def _name(self):
        if isinstance(self.indexarray, string_types):
            return self.indexarray
        else:
            return None

    @property
    def primaryarray(self):
        return self.indexarray

    def resolved(self, source, lazy=False, _memo=None):
        def resolve():
            return self._toint32(self._resolved(self.indexarray, source, "Pointer indexarray must map to a one-dimensional, {0}, non-record array of integers", self.nullable, lambda x: issubclass(x.dtype.type, numpy.integer)))

        # (only) pointers are allowed to reference themselves, but don't resolve the same pointer more than once
        if _memo is None:
            _memo = {}
        if id(self.target) not in _memo:
            self.target.resolved(source, lazy, _memo)

        if lazy:
            _memo[id(self)] = Pointer(resolve, _memo[id(self.target)], self.nullable, self)
        else:
            _memo[id(self)] = Pointer(resolve(), _memo[id(self.target)], self.nullable, self)
        return _memo[id(self)]

    def proxy(self, index=0):
        if callable(self.indexarray):
            self.indexarray = self.indexarray()

        if getattr(self.indexarray, "mask", None) is not None and self.indexarray.mask[index]:
            return None
        else:
            offset = self.indexarray[index]
            return self.target.proxy(offset)

    def get(self, attr):
        if callable(self.indexarray):
            self.indexarray = self.indexarray()

        if attr == "indexarray":
            return self.indexarray
        else:
            raise NameError("Pointer has no array {0}".format(repr(attr)))

    def members(self, _memo=None):
        if _memo is None:
            _memo = set()
        out = [self]
        if id(self.target) not in _memo:
            _memo.add(id(self.target))
            return out + self.target.members(_memo)
        else:
            return out

    def hasany(self, others, _memo=None):
        if any(x is self for x in others):
            return True
        if _memo is None:
            _memo = set()
        if id(self.target) not in _memo:
            _memo.add(id(self.target))
            return self.target.hasany(others, _memo)
        else:
            return False

    def projection(self, required, _memo=None):
        if self.hasany(required):
            if _memo is None:
                _memo = {}
            if id(self.target) not in _memo:
                _memo[id(self.target)] = None
                _memo[id(self.target)] = self.target.projection(required, _memo)
            target = _memo[id(self.target)]
            if target is None:
                target = Primitive(self.indexarray, self.nullable)
            return Pointer(self.indexarray, target, self.nullable, self)
        else:
            return None

    def isinstance(self, obj, _memo=None):
        if _memo is None:
            _memo = set()
        if id(self) in _memo:
            return False
        else:
            _memo.add(id(self))

        if obj is None and self.nullable:
            return True
        return self.target.isinstance(obj)

    def _format(self, indent, width, refs, memo):
        yield indent + refs.get(id(self), "") + "Pointer" + (" (nullable)" if self.nullable else "") + " (*"
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
        return isinstance(other, Pointer) and ((isinstance(self.indexarray, ndarray) and isinstance(other.indexarray, ndarray) and numpy.array_equal(self.indexarray, other.indexarray)) or self.indexarray == other.indexarray) and self.target is other.target and self.base == other.base

    def __ne__(self, other):
        return not self.__eq__(self, other)
