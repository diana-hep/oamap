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

if sys.version_info[0] > 2:
    xrange = range

# base class of all runtime types that require proxies: List, Record, and Tuple
class Proxy(object): pass

################################################################ Lists

class ListProxy(Proxy):
    __slots__ = ["_name", "_arrays", "_cache", "_content", "_start", "_stop", "_step"]

    def __init__(self, name, arrays, cache, content, start, stop, step):
        self._name = name
        self._arrays = arrays
        self._cache = cache
        self._content = content
        self._start = start
        self._stop = stop
        self._step = step

    def __repr__(self, memo=None):
        if memo is None:
            memo = set()
        key = (id(self._content), self._start, self._stop, self._step)
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
                return ListProxy(self._name, self._arrays, self._cache, self._content, self._start + self._step*start, self._start + self._step*stop, self._step*step)

        else:
            lenself = len(self)
            normalindex = index if index >= 0 else index + lenself
            if not 0 <= normalindex < lenself:
                raise IndexError("index {0} is out of bounds for size {1}".format(index, lenself))
            return self._content._generate(self._arrays, self._start + self._step*normalindex, self._cache)

    def __iter__(self):
        return (self._content._generate(self._arrays, i, self._cache) for i in xrange(self._start, self._stop, self._step))

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

################################################################ Records

class RecordProxy(Proxy):
    __slots__ = ["_fields", "_name", "_arrays", "_cache", "_index"]

    def __init__(self, fields, name, arrays, cache, index):
        self._fields = fields
        self._name = name
        self._arrays = arrays
        self._cache = cache
        self._index = index

    def __repr__(self):
        return "<{0} at index {1}>".format("Record" if self._name is None else self._name, self._index)

    def __getattr__(self, field):
        if field.startswith("_"):
            return super(RecordProxy, self).__getattr__(field)
        else:
            try:
                generator = self._fields[field]
            except KeyError:
                raise AttributeError("{0} object has no attribute {1}".format(repr("Record" if self._name is None else self._name), repr(field)))
            else:
                return generator._generate(self._arrays, self._index, self._cache)

    def __hash__(self):
        return hash((RecordProxy, self._name) + tuple(self._fields.items()))

    def __eq__(self, other):
        return isinstance(other, RecordProxy) and self._name == other._name and set(self._fields) == set(other._fields) and all(self.__getattr__(n) for n in self._fields)

    def __lt__(self, other):
        if isinstance(other, RecordProxy) and self._name == other._name and set(self._fields) == set(other._fields):
            return [self.__getattr__(n) for n in self._fields] < [other.__getattr__(n) for n in self._fields]
        else:
            raise TypeError("unorderable types: {0}() < {1}()".format("<type 'Record'>" if self._name is None else "<type {0}>".format(repr(self._name)), other.__class__))

    def __ne__(self, other): return not self.__eq__(other)
    def __le__(self, other): return self.__lt__(other) or self.__eq__(other)
    def __gt__(self, other): return not self.__lt__(other) and not self.__eq__(other)
    def __ge__(self, other): return not self.__lt__(other)

################################################################ Tuples

class TupleProxy(Proxy):
    __slots__ = ["_types", "_name", "_arrays", "_cache", "_index"]

    def __init__(self, types, name, arrays, cache, index):
        self._types = types
        self._name = name
        self._arrays = arrays
        self._cache = cache
        self._index = index

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
            return self._types[index]._generate(self._arrays, self._index, self._cache)

    def __iter__(self):
        return (t._generate(self._arrays, self._index, self._cache) for t in self._types)

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
