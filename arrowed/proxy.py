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

import sys
import json
import math

import numpy

class Proxy(object):
    def _toJsonString(self):
        return json.dumps(self._toJson())

def toJson(obj):
    if isinstance(obj, Proxy):
        return obj._toJson()
    elif isinstance(obj, numpy.integer):
        return int(obj)
    elif isinstance(obj, numpy.floating):
        if math.isnan(obj):
            return "nan"
        elif math.isinf(obj) and obj > 0:
            return "inf"
        elif math.isinf(obj):
            return "-inf"
        else:
            return float(obj)
    elif isinstance(obj, numpy.complex):
        return {"real": toJson(obj.real), "imag": toJson(obj.imag)}
    elif isinstance(obj, numpy.ndarray):
        return obj.tolist()
    else:
        return obj

################################################################ list proxy

class ListProxy(list, Proxy):
    __slots__ = ["_schema", "_index"]

    def __init__(self, schema, index):
        self._schema = schema
        self._index = index

    def __repr__(self):
        dots = ", ..." if len(self) > 4 else ""
        return "[{0}{1}]".format(", ".join(map(repr, self[:4])), dots)

    def __len__(self):
        return int(self._schema.endarray[self._index] - self._schema.beginarray[self._index])

    def __getitem__(self, index):
        if isinstance(index, slice):
            return sliceofproxy(self, index)
        else:
            index = normalizeindex(self, index, False, 1)
            return self._schema.contents.proxy(self._schema.beginarray[self._index] + index)

    def __getslice__(self, start, stop):
        # for old-Python compatibility
        return self.__getitem__(slice(start, stop))
    
    def __iter__(self):
        if sys.version_info[0] <= 2:
            return (self[i] for i in xrange(len(self)))
        else:
            return (self[i] for i in range(len(self)))

    def append(self, *args, **kwds):       raise TypeError("ListProxy is immutable (cannot be changed in-place)")
    def __delitem__(self, *args, **kwds):  raise TypeError("ListProxy is immutable (cannot be changed in-place)")
    def __delslice__(self, *args, **kwds): raise TypeError("ListProxy is immutable (cannot be changed in-place)")
    def extend(self, *args, **kwds):       raise TypeError("ListProxy is immutable (cannot be changed in-place)")
    def __iadd__(self, *args, **kwds):     raise TypeError("ListProxy is immutable (cannot be changed in-place)")
    def __imul__(self, *args, **kwds):     raise TypeError("ListProxy is immutable (cannot be changed in-place)")
    def insert(self, *args, **kwds):       raise TypeError("ListProxy is immutable (cannot be changed in-place)")
    def pop(self, *args, **kwds):          raise TypeError("ListProxy is immutable (cannot be changed in-place)")
    def remove(self, *args, **kwds):       raise TypeError("ListProxy is immutable (cannot be changed in-place)")
    def reverse(self, *args, **kwds):      raise TypeError("ListProxy is immutable (cannot be changed in-place)")
    def __setitem__(self, *args, **kwds):  raise TypeError("ListProxy is immutable (cannot be changed in-place)")
    def __setslice__(self, *args, **kwds): raise TypeError("ListProxy is immutable (cannot be changed in-place)")
    def sort(self, *args, **kwds):         raise TypeError("ListProxy is immutable (cannot be changed in-place)")

    def __add__(self, other): return list(self) + list(other)
    def __mul__(self, reps): return list(self) * reps
    def __rmul__(self, reps): return reps * list(self)
    def __reversed__(self):
        if sys.version_info[0] <= 2:
            return (self[i - 1] for i in xrange(len(self), 0, -1))
        else:
            return (self[i - 1] for i in range(len(self), 0, -1))
    def count(self, value): return sum(1 for x in self if x == value)
    def index(self, value, *args):
        if len(args) == 0:
            start = 0
            stop = len(self)
        elif len(args) == 1:
            start = args[0]
            stop = len(self)
        elif len(args) == 2:
            start, stop = args
        else:
            raise TypeError("index() takes at most 3 arguments ({0} given)".format(1 + len(args)))
        for i, x in enumerate(self):
            if x == value:
                return i
        raise ValueError("{0} is not in list".format(value))

    def __contains__(self, value):
        for x in self:
            if x == value:
                return True
        return False

    def __hash__(self):
        return hash(tuple(self))

    def __eq__(self, other):
        return isinstance(other, list) and len(self) == len(other) and all(x == y for x, y in zip(self, other))

    def __lt__(self, other):
        if isinstance(other, ListProxy):
            return list(self) < list(other)
        elif isinstance(other, list):
            return list(self) < other
        else:
            raise TypeError("unorderable types: {0} < {1}".format(self.__class__, other.__class__))

    def __ne__(self, other): return not self.__eq__(other)
    def __le__(self, other): return self.__lt__(other) or self.__eq__(other)
    def __gt__(self, other):
        if isinstance(other, ListProxy):
            return list(self) > list(other)
        else:
            return list(self) > other
    def __ge__(self, other): return self.__gt__(other) or self.__eq__(other)

    def _toJson(self):
        return [toJson(x) for x in self]

################################################################ list slice proxy

class ListSliceProxy(ListProxy):
    __slots__ = ["__listproxy", "__start", "__stop", "__step"]

    def __init__(self, listproxy, start, stop, step):
        self.__listproxy = listproxy
        self.__start = start
        self.__stop = stop
        self.__step = step

    @property
    def _schema(self):
        return self.__listproxy._schema

    def __len__(self):
        if self.__step == 1:
            return self.__stop - self.__start
        else:
            return int(math.ceil(float(self.__stop - self.__start) / self.__step))

    def __getitem__(self, index):
        if isinstance(index, slice):
            return sliceofproxy(self, index)
        else:
            return self.__listproxy[self.__start + self.__step*normalizeindex(self, index, False, 1)]

################################################################ record proxy superclass

class RecordProxy(Proxy):
    def __init__(self, schema, index):
        self._schema = schema
        self._index = index

    def __repr__(self):
        return "<{0} at index {1}>".format(self.__class__.__name__, self._index)

    def __eq__(self, other):
        return isinstance(other, RecordProxy) and set(self._schema.contents.keys()) == set(other._schema.contents.keys()) and all(getattr(self, name) == getattr(other, name) for name in self._schema.contents.keys())

    def __lt__(self, other):
        if isinstance(other, RecordProxy):
            if len(self._schema.contents) > len(other._schema.contents):
                return True

            elif len(self._schema.contents) < len(other._schema.contents):
                return False

            elif set(self._schema.contents.keys()) == set(other._schema.contents.keys()):
                return tuple(getattr(self, name) for name in self._schema.contents.keys()) < tuple(getattr(other, name) for name in other._schema.contents.keys())

            else:
                return sorted(self._schema.contents.keys()) == sorted(other._schema.contents.keys())

        else:
            raise TypeError("unorderable types: {0} < {1}".format(self.__class__, other.__class__))
    def __ne__(self, other): return not self.__eq__(other)
    def __le__(self, other): return self.__lt__(other) or self.__eq__(other)
    def __gt__(self, other):
        if isinstance(other, LazyRecord):
            return list(self) > list(other)
        else:
            return list(self) > other
    def __ge__(self, other): return self.__gt__(other) or self.__eq__(other)

    def _toJson(self):
        return dict((name, toJson(getattr(self, name))) for name in self._schema.contents)

################################################################ tuple proxy

class TupleProxy(tuple, Proxy):
    def __init__(self, schema, index):
        self._schema = schema
        self._index = index

    def __repr__(self):
        return "({0})".format(", ".join(repr(x) for x in self))

    def __len__(self):
        return len(self._schema.contents)

    def __getitem__(self, index):
        if isinstance(index, slice):
            return tuple(self[i] for i in range(len(self._schema.contents))[index])
        else:
            return self._schema.contents[index].proxy(self._index)

    def __getslice__(self, start, stop):
        # for old-Python compatibility
        return self.__getitem__(slice(start, stop))

    def __iter__(self):
        return (self[i] for i in range(len(self)))

    def __add__(self, other): return tuple(self) + tuple(other)
    def __mul__(self, reps): return tuple(self) * reps
    def __rmul__(self, reps): return reps * tuple(self)
    def __reversed__(self):
        if sys.version_info[0] <= 2:
            return (self[i - 1] for i in xrange(len(self), 0, -1))
        else:
            return (self[i - 1] for i in range(len(self), 0, -1))
    def count(self, value): return sum(1 for x in self if x == value)
    def index(self, value, *args):
        if len(args) == 0:
            start = 0
            stop = len(self)
        elif len(args) == 1:
            start = args[0]
            stop = len(self)
        elif len(args) == 2:
            start, stop = args
        else:
            raise TypeError("index() takes at most 3 arguments ({0} given)".format(1 + len(args)))
        for i, x in enumerate(self):
            if x == value:
                return i
        raise ValueError("{0} is not in tuple".format(value))

    def __contains__(self, value):
        for x in self:
            if x == value:
                return True
        return False

    def __hash__(self):
        return hash(tuple(self))

    def __eq__(self, other):
        return isinstance(other, tuple) and len(self) == len(other) and all(x == y for x, y in zip(self, other))

    def __lt__(self, other):
        if isinstance(other, TupleProxy):
            return tuple(self) < tuple(other)
        elif isinstance(other, list):
            return tuple(self) < other
        else:
            raise TypeError("unorderable types: {0} < {1}".format(self.__class__, other.__class__))

    def __ne__(self, other): return not self.__eq__(other)
    def __le__(self, other): return self.__lt__(other) or self.__eq__(other)
    def __gt__(self, other):
        if isinstance(other, TupleProxy):
            return tuple(self) > tuple(other)
        else:
            return tuple(self) > other
    def __ge__(self, other): return self.__gt__(other) or self.__eq__(other)

    def _toJson(self):
        return [toJson(x) for x in self]

################################################################ helper functions

def normalizeindex(listproxy, index, clip, step):
    lenproxy = len(listproxy)
    if index < 0:
        j = lenproxy + index
        if j < 0:
            if clip:
                return 0 if step > 0 else lenproxy
            else:
                raise IndexError("index out of range: {0} for length {1}".format(index, lenproxy))
        else:
            return j
    elif index < lenproxy:
        return index
    elif clip:
        return lenproxy if step > 0 else 0
    else:
        raise IndexError("index out of range: {0} for length {1}".format(index, lenproxy))

def sliceofproxy(listproxy, slice):
    if slice.step is None:
        step = 1
    else:
        step = slice.step
    if step == 0:
        raise ValueError("slice step cannot be zero")

    lenproxy = len(listproxy)
    if lenproxy == 0:
        return ListSliceProxy(listproxy, 0, 0, 1)

    if slice.start is None:
        if step > 0:
            start = 0
        else:
            start = lenproxy - 1
    else:
        start = normalizeindex(listproxy, slice.start, True, step)

    if slice.stop is None:
        if step > 0:
            stop = lenproxy
        else:
            stop = -1
    else:
        stop = normalizeindex(listproxy, slice.stop, True, step)

    return ListSliceProxy(listproxy, start, stop, step)
