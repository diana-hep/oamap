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

import numpy

if sys.version_info[0] > 2:
    xrange = range

# superclass of all proxies
class Proxy(object):
    @classmethod
    def _getarray(cls, arrays, name, cache, cacheslot):
        if cacheslot >= len(cache):
            cache.extend([None] * (1 + cacheslot - len(cache)))
        if cache[cacheslot] is None:
            cache[cacheslot] = arrays[name]
        return cache[cacheslot]

# mix-in for masked proxies
class Masked(object):
    def __new__(cls, arrays, index=0, cache=None):
        if cache is None:
            cache = []
        if cls._getarray(arrays, cls._mask, cache, cls._maskidx)[index]:
            return None
        else:
            return cls.__bases__[1].__new__(cls, arrays, index=index)

################################################################ Primitives

class PrimitiveProxy(Proxy):
    def __new__(cls, arrays, index=0, cache=None):
        if cache is None:
            cache = []
        return cls._getarray(arrays, cls._data, cache, cls._dataidx)[index]

################################################################ Lists

class ListProxy(Proxy):
    __slots__ = ["_arrays", "_start", "_stop", "_step"]

    def __new__(cls, arrays, index=0, cache=None):
        if cache is None:
            cache = []
        starts = cls._getarray(arrays, cls._starts, cache, cls._startsidx)
        stops = cls._getarray(arrays, cls._stops, cache, cls._stopsidx)
        return cls._slice(arrays, cache, starts[index], stops[index], 1)

    @classmethod
    def _slice(cls, arrays, cache, start, stop, step):
        out = Proxy.__new__(cls)
        out._arrays = arrays
        out._cache = cache
        out._start = start
        out._stop = stop
        out._step = step
        return out

    def __repr__(self, memo=None):
        if memo is None:
            memo = set()
        key = (self._starts, self._stops, self._start, self._stop, self._step)
        if key in memo:
            return "[...]"
        memo.add(key)
        if len(self) > 10:
            before = self[:5]
            after = self[-5:]
            return "[{0}, ..., {1}".format(", ".join(x.__repr__(memo) if isinstance(x, (ListProxy, TupleProxy)) else repr(x) for x in before),
                                           ", ".join(x.__repr__(memo) if isinstance(x, (ListProxy, TupleProxy)) else repr(x) for x in after))
        else:
            contents = list(self)
            return "[{0}]".format(", ".join(x.__repr__(memo) if isinstance(x, (ListProxy, TupleProxy)) else repr(x) for x in contents))

    def __len__(self):
        return (self._stop - self._start) // self._step

    def __getslice__(self, start, stop):
        # for old-Python compatibility
        return self.__getitem__(slice(start, stop))

    def __getitem__(self, index):
        if isinstance(index, slice):
            lenself = len(self)
            start = 0       if index.start is None else index.start
            stop  = lenself if index.stop  is None else index.stop
            step  = 1       if index.step  is None else index.step

            start = min(lenself, max(0, start))
            stop  = min(lenself, max(0, stop))
            if stop < start:
                stop = start

            if step == 0:
                raise ValueError("slice step cannot be zero")
            else:
                return self.__class__._slice(self._arrays, self._cache, self._start + self._step*start, self._start + self._step*stop, self._step*step)

        else:
            lenself = len(self)
            normalindex = index if index >= 0 else index + lenself
            if not 0 <= normalindex < lenself:
                raise IndexError("index {0} is out of bounds for size {1}".format(index, lenself))
            return self._content(self._arrays, index=(self._start + self._step*normalindex), cache=self._cache)

    def __iter__(self):
        return (self._content(self._arrays, index=i, cache=self._cache) for i in xrange(self._start, self._stop, self._step))

    def __hash__(self):
        # lists aren't usually hashable, but since ListProxy is immutable, we can add this feature
        return hash((ListProxy,) + tuple(self))

    def __eq__(self, other):
        if isinstance(other, ListProxy):
            return list(self) == list(other)
        elif isinstance(other, list):
            return list(self) == other
        else:
            return False

    def __lt__(self, other):
        if isinstance(other, ListProxy):
            return list(self) < list(other)
        elif isinstance(other, list):
            return list(self) < other
        else:
            raise TypeError("unorderable types: list() < {1}()".format(other.__class__))

    # all of the following emulate normal list functionality using the overloaded methods above

    def __ne__(self, other): return not self.__eq__(other)
    def __le__(self, other): return self.__lt__(other) or self.__eq__(other)
    def __gt__(self, other): return not self.__lt__(other) and not self.__eq__(other)
    def __ge__(self, other): return not self.__lt__(other)

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

################################################################ Unions

class UnionProxy(Proxy):
    def __new__(cls, arrays, index=0, cache=None):
        if cache is None:
            cache = []
        tags = cls._getarray(arrays, cls._tags, cache, cls._tagsidx)
        offsets = cls._getarray(arrays, cls._offsets, cache, cls._offsetsidx)
        return cls._possibilities[tags[index]](arrays, index=offsets[index], cache=cache)

################################################################ Records

class RecordProxy(Proxy):
    __slots__ = ["_arrays", "_index"]

    def __new__(cls, arrays, index=0, cache=None):
        if cache is None:
            cache = []
        out = Proxy.__new__(cls)
        out._arrays = arrays
        out._cache = cache
        out._index = index
        return out

    def __repr__(self):
        name = self.__class__.__name__
        return "<{0} at index {1}>".format("Record" if name == "" else name, self._index)

    def __hash__(self):
        return hash((RecordProxy, self.__class__.__name__) + self._fields + tuple(getattr(self, n) for n in self._fields))

    def __eq__(self, other):
        return isinstance(other, RecordProxy) and self.__class__.__name__ == other.__class__.__name__ and self._fields == other._fields and all(getattr(self, n) == getattr(other, n) for n in self._fields)

    def __lt__(self, other):
        if isinstance(other, RecordProxy) and self.__class__.__name__ == other.__class__.__name__ and self._fields == other._fields:
            return [getattr(self, n) for n in self._fields] < [getattr(other, n) for n in self._fields]
        else:
            name = self.__class__.__name__
            raise TypeError("unorderable types: {0}() < {1}()".format(repr("type <'Anonymous ({0} fields)'>".format(len(self._fields))) if name == "" else self.__class__, other.__class__))

    def __ne__(self, other): return not self.__eq__(other)
    def __le__(self, other): return self.__lt__(other) or self.__eq__(other)
    def __gt__(self, other): return not self.__lt__(other) and not self.__eq__(other)
    def __ge__(self, other): return not self.__lt__(other)

################################################################ Tuples

class TupleProxy(Proxy):
    __slots__ = ["_arrays", "_index"]

    def __new__(cls, arrays, index=0, cache=None):
        if cache is None:
            cache = []
        out = Proxy.__new__(cls)
        out._arrays = arrays
        out._cache = cache
        out._index = index
        return out

    def __repr__(self, memo=None):
        if memo is None:
            memo = set()
        key = (self._index,) + tuple(id(x) for x in self._types)
        if key in memo:
            return "(...)"
        memo.add(key)
        contents = list(self)
        return "({0}{1})".format(", ".join(x.__repr__(memo) if isinstance(x, (ListProxy, TupleProxy)) else repr(x) for x in contents), "," if len(self) == 1 else "")

    def __len__(self):
        return len(self._types)

    def __getslice__(self, start, stop):
        # for old-Python compatibility
        return self.__getitem__(slice(start, stop))

    def __getitem__(self, index):
        if isinstance(index, slice):
            lenself = len(self)
            start = 0       if index.start is None else index.start
            stop  = lenself if index.stop  is None else index.stop
            step  = 1       if index.step  is None else index.step
            return tuple(self[i] for i in range(start, stop, step))

        else:
            return self._types[index](self._arrays, index=self._index, cache=self._cache)

    def __iter__(self):
        return (t(self._arrays, self._index) for t in self._types)

    def __hash__(self):
        return hash(tuple(self))

    def __eq__(self, other):
        if isinstance(other, TupleProxy):
            return tuple(self) == tuple(other)
        elif isinstance(other, tuple):
            return tuple(self) == other
        else:
            return False

    def __lt__(self, other):
        if isinstance(other, TupleProxy):
            return tuple(self) < tuple(other)
        elif isinstance(other, tuple):
            return tuple(self) < other
        else:
            raise TypeError("unorderable types: tuple() < {1}()".format(other.__class__))

    # all of the following emulate normal tuple functionality using the overloaded methods above

    def __ne__(self, other): return not self.__eq__(other)
    def __le__(self, other): return self.__lt__(other) or self.__eq__(other)
    def __gt__(self, other): return not self.__lt__(other) and not self.__eq__(other)
    def __ge__(self, other): return not self.__lt__(other)

    def __add__(self, other): return tuple(self) + tuple(other)
    def __mul__(self, reps): return tuple(self) * reps
    def __rmul__(self, reps): return reps * tuple(self)
    def __reversed__(self):
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

################################################################ Pointers

class PointerProxy(Proxy):
    def __new__(cls, arrays, index=0, cache=None):
        if cache is None:
            cache = []
        positions = cls._getarray(arrays, cls._positions, cache, cls._positionsidx)
        return cls._target(arrays, index=positions[index], cache=cache)
