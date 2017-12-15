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

################################################################ Primitives have type objects, but no special proxies

class PrimitiveType(type):
    def __new__(cls, arrays, index=0):
        return arrays[cls.data][index]

class MaskedPrimitiveType(type):
    def __new__(cls, arrays, index=0):
        if arrays[cls.mask][index]:
            return None
        else:
            return arrays[cls.data][index]

################################################################ Lists have proxies and type objects

class ListProxy(list):
    __slots__ = ["_arrays", "_start", "_stop", "_step"]

    def __init__(self, arrays, start, stop, step):
        self._arrays = arrays
        self._start = start
        self._stop = stop
        self._step = step

    def __repr__(self):
        dots = ", ..." if len(self) > 4 else ""
        return "[{0}{1}]".format(", ".join([repr(x) for x in self[:4]]), dots)

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
                return ListProxy(self._arrays, self._start + self._step*start, self._start + self._step*stop, self._step*step)

        else:
            lenself = len(self)
            normalindex = index if index >= 0 else index + lenself
            if not 0 <= normalindex < lenself:
                raise IndexError("index {0} is out of bounds for size {1}".format(index, lenself))
            return self._content(self._arrays, self._start + self._step*normalindex)

    def __iter__(self):
        return (self._content(self._arrays, i) for i in xrange(self._start, self._stop, self._step))

    def __hash__(self):
        # lists aren't usually hashable, but since ListProxy is immutable, we can add this feature
        return hash((ListProxy, self.__class__.__name__) + tuple(self))

    def __eq__(self, other):
        return isinstance(other, ListProxy) and self.__class__.__name__ == other.__class__.__name__ and len(self) == len(other) and all(x == y for x, y in zip(self, other))

    def __lt__(self, other):
        if isinstance(other, ListProxy) and self.__class__.__name__ == other.__class__.__name__:
            return list(self) < list(other)
        else:
            raise TypeError("unorderable types: {0} < {1}".format(self.__class__, other.__class__))

    # all of the following either prohibit normal list functionality (because ListProxy is immutable) or emulate it using the overloaded methods above

    def __ne__(self, other): return not self.__eq__(other)
    def __le__(self, other): return self.__lt__(other) or self.__eq__(other)
    def __gt__(self, other): return not self.__lt__(other) and not self.__eq__(other)
    def __ge__(self, other): return not self.__lt__(other)

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

class AnonymousListProxy(ListProxy):
    def __hash__(self):
        return hash((AnonymousListProxy,) + tuple(self))

    def __eq__(self, other):
        if isinstance(other, AnonymousListProxy):
            return list(self) == list(other)
        elif isinstance(other, list):
            return list(self) == other
        else:
            return False

    def __lt__(self, other):
        if isinstance(other, AnonymousListProxy):
            return list(self) < list(other)
        elif isinstance(other, list):
            return list(self) < other
        else:
            raise TypeError("unorderable types: {0} < {1}".format(self.__class__, other.__class__))

class ListType(type):
    def __new__(cls, arrays, index=0):
        return cls.proxytype(arrays, arrays[cls.starts][index], arrays[cls.stops][index], 1)

class MaskedListType(type):
    def __new__(cls, arrays, index=0):
        if arrays[cls.mask][index]:
            return None
        else:
            return cls.proxytype(arrays, arrays[cls.starts][index], arrays[cls.stops][index], 1)

################################################################ Unions have type objects, but no special proxies

class UnionType(type):
    def __new__(cls, arrays, index=0):
        tag = arrays[cls.tags][index]
        return cls.possibilities[tag](arrays, cls.offsets[tag])

class MaskedUnionType(type):
    def __new__(cls, arrays, index=0):
        if arrays[cls.mask][index]:
            return None
        else:
            tag = arrays[cls.tags][index]
            return cls.possibilities[tag](arrays, cls.offsets[tag])

################################################################ Records have proxies and type objects

class RecordProxy(object):
    __slots__ = ["_arrays", "_index"]

    def __init__(self, arrays, index):
        self._arrays = arrays
        self._index = index

    def __repr__(self):
        return "<{0} at {1:012x}>".format(self.__class__.__name__, id(self))

    def __hash__(self):
        return hash((RecordProxy, self.__class__.__name__) + self._fields + tuple(getattr(self, n) for n in self._fields))

    def __eq__(self, other):
        return isinstance(other, RecordProxy) and self.__class__.__name__ == other.__class__.__name__ and self._fields == other._fields and all(getattr(self, n) == getattr(other, n) for n in self._fields)

    def __lt__(self, other):
        if isinstance(other, RecordProxy) and self.__class__.__name__ == other.__class__.__name__ and self._fields == other._fields:
            return [getattr(self, n) for n in self._fields] < [getattr(other, n) for n in self._fields]
        else:
            raise TypeError("unorderable types: {0} < {1}".format(self.__class__, other.__class__))

    def __ne__(self, other): return not self.__eq__(other)
    def __le__(self, other): return self.__lt__(other) or self.__eq__(other)
    def __gt__(self, other): return not self.__lt__(other) and not self.__eq__(other)
    def __ge__(self, other): return not self.__lt__(other)

class RecordType(type):
    def __new__(cls, arrays, index=0):
        return cls.proxytype(arrays, index)

class MaskedRecordType(type):
    def __new__(cls, arrays, index=0):
        if arrays[cls.mask][index]:
            return None
        else:
            return cls.proxytype(arrays, index)

################################################################ Tuples have proxies and type objects

class TupleProxy(tuple):
    __slots__ = ["_arrays", "_index"]

    def __init__(self, arrays, index):
        self._arrays = arrays
        self._index = index

    def __repr__(self):
        return "(" + ", ".join(repr(x) for x in self) + ")"

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
            return self._types[index](self._arrays, self._index)

    def __iter__(self):
        return (t(self._arrays, self._index) for t in self._types)

    def __hash__(self):
        return hash((TupleProxy, self.__class__.__name__, len(self)) + tuple(self))

    def __eq__(self, other):
        return isinstance(other, TupleProxy) and self.__class__.__name__ == other.__class__.__name__ and len(self._types) == len(other._types) and all(x == y for x, y in zip(self, other))

    def __lt__(self, other):
        if isinstance(other, TupleProxy) and self.__class__.__name__ == other.__class__.__name__:
            return tuple(self) < tuple(other)
        else:
            raise TypeError("unorderable types: {0} < {1}".format(self.__class__, other.__class__))

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

class AnonymousTupleProxy(TupleProxy):
    def __hash__(self):
        return hash(tuple(self))

    def __eq__(self, other):
        if isinstance(other, AnonymousTupleProxy):
            return tuple(self) == tuple(other)
        elif isinstance(other, tuple):
            return tuple(self) == other
        else:
            return False

    def __lt__(self, other):
        if isinstance(other, AnonymousTupleProxy):
            return tuple(self) < tuple(other)
        elif isinstance(other, tuple):
            return tuple(self) < other
        else:
            raise TypeError("unorderable types: {0} < {1}".format(self.__class__, other.__class__))

class TupleType(type):
    def __new__(cls, arrays, index=0):
        return cls.proxytype(arrays, index)

class MaskedTupleType(type):
    def __new__(cls, arrays, index=0):
        if arrays[cls.mask][index]:
            return None
        else:
            return cls.proxytype(arrays, index)

################################################################ Pointers have type objects, but no special proxies

class PointerType(type):
    def __new__(cls, arrays, index=0):
        return cls.target(arrays, arrays[cls.indexes][index])

class MaskedPointerType(type):
    def __new__(cls, arrays, index=0):
        if arrays[cls.mask][index]:
            return None
        else:
            return cls.target(arrays, arrays[cls.indexes][index])
