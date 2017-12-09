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
        try:
            return arrays[cls.data][index]

        except KeyError as err:
            raise KeyError("could not find PrimitiveType data {0} in array namespace".format(repr(cls.data)))

        except IndexError as err:
            raise IndexError(err.message + " when instantiating PrimitiveType from data {0}".format(repr(cls.data)))

class MaskedPrimitiveType(type):
    def __new__(cls, arrays, index=0):
        try:
            if arrays[cls.mask][index]:
                return None
            else:
                return arrays[cls.data][index]

        except KeyError as err:
            raise KeyError("could not find MaskedPrimitiveType data {0} and mask {1} in array namespace".format(repr(cls.data), repr(cls.mask)))

        except IndexError as err:
            raise IndexError(err.message + " when instantiating MaskedPrimitiveType from data {0} and mask {1}".format(repr(cls.data), repr(cls.mask)))

################################################################ Lists have proxies and type objects

class ListProxy(list):
    __slots__ = ["_contents", "_arrays", "_start", "_stop", "_step"]

    def __init__(self, contents, arrays, start, stop, step):
        self._contents = contents
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
        lenself = len(self)
        if start < 0:
            start += lenself
        if stop < 0:
            stop += lenself
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
                return ListProxy(self._contents, self._arrays, self._start + self._step*start, self._start + self._step*stop, self._step*step)

        else:
            lenself = len(self)
            normalindex = index if index >= 0 else index + lenself
            if not 0 <= normalindex < lenself:
                raise IndexError("index {0} is out of bounds for size {1}".format(index, lenself))
            return self._contents(self._arrays, self._start + self._step*normalindex)

    def __iter__(self):
        return (self._contents(self._arrays, i) for i in xrange(self._start, self._stop, self._step))

    def __hash__(self):
        # lists aren't usually hashable, but since ListProxy is immutable, we can add this feature
        return hash(tuple(self))

    # all of the following either prohibit normal list functionality (because ListProxy is immutable) or emulate it using the overloaded methods above

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

class ListType(type):
    def __new__(cls, arrays, index=0):
        try:
            return ListProxy(cls.contents, arrays, arrays[cls.starts][index], arrays[cls.stops][index], 1)

        except KeyError as err:
            raise KeyError("could not find ListType start {0} and stop {1} in array namespace".format(repr(cls.start), repr(cls.stop)))

        except IndexError as err:
            raise IndexError(err.message + " when instantiating ListType from start {0} and stop {1}".format(repr(cls.start), repr(cls.stop)))

class MaskedListType(type):
    def __new__(cls, arrays, index=0):
        try:
            if arrays[cls.mask][index]:
                return None
            else:
                return ListProxy(cls.contents, arrays, arrays[cls.starts][index], arrays[cls.stops][index], 1)

        except KeyError as err:
            raise KeyError("could not find MaskedListType start {0}, stop {1}, and mask {2} in array namespace".format(repr(cls.start), repr(cls.stop), repr(cls.mask)))

        except IndexError as err:
            raise IndexError(err.message + " when instantiating MaskedListType from start {0}, stop {1}, and mask {2}".format(repr(cls.start), repr(cls.stop), repr(cls.mask)))

################################################################ Unions have type objects, but no special proxies



################################################################ Records have proxies and type objects


