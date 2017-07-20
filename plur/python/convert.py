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

import math

import numpy

from plur.util import *
from plur.types import *
from plur.types.columns import type2columns
from plur.types.columns import columns2type
from plur.types.arrayname import ArrayName
from plur.python.types import infertype
from plur.python.fillmemory import FillableInMemory

def toarrays(prefix, obj, tpe=None, fillable=FillableInMemory, delimiter="-", offsettype=numpy.dtype(numpy.int64), **fillableOptions):
    if tpe is None:
        tpe = infertype(obj)

    dtypes = type2columns(tpe, prefix, delimiter=delimiter, offsettype=offsettype)
    fillables = dict((ArrayName.parse(n, prefix, delimiter=delimiter), fillable(n, d, **fillableOptions)) for n, d in dtypes.items())

    last_list_offset = {}
    last_union_offset = {}

    def recurse(obj, tpe, name):
        if isinstance(tpe, Primitive):
            if not obj in tpe:
                raise TypeError("cannot fill {0} where an object of type {1} is expected".format(obj, tpe))
            fillables[name].fill(obj)

        elif isinstance(tpe, List):
            try:
                iter(obj)
                if isinstance(obj, dict) or (isinstance(obj, tuple) and hasattr(obj, "_fields")):
                    raise TypeError
            except TypeError:
                raise TypeError("cannot fill {0} where an object of type {1} is expected".format(obj, tpe))

            nameoffset = name.toListOffset()
            namedata = name.toListData()

            if nameoffset not in last_list_offset:
                last_list_offset[nameoffset] = 0
            last_list_offset[nameoffset] += len(obj)

            fillables[nameoffset].fill(last_list_offset[nameoffset])
            
            for x in obj:
                recurse(x, tpe.of, namedata)

        elif isinstance(tpe, Union):
            t = infertype(obj)   # can be expensive!
            tag = None
            for i, possibility in enumerate(tpe.of):
                if t.issubtype(possibility):
                    tag = i
                    break
            if tag is None:
                raise TypeError("cannot fill {0} where an object of type {1} is expected".format(obj, tpe))

            nametag = name.toUnionTag()
            nameoffset = name.toUnionOffset()
            namedata = name.toUnionData(tag)

            if namedata not in last_union_offset:
                last_union_offset[namedata] = 0

            fillables[nametag].fill(tag)
            fillables[nameoffset].fill(last_union_offset[namedata])

            last_union_offset[namedata] += 1

            recurse(obj, tpe.of[tag], namedata)

        elif isinstance(tpe, Record):
            if isinstance(obj, dict):
                for fn, ft in tpe.of:
                    if fn not in obj:
                        raise TypeError("cannot fill {0} (missing field \"{1}\") where an object of type {2} is expected".format(obj, fn, tpe))
                    recurse(obj[fn], ft, name.toRecord(fn))

            else:
                for fn, ft in tpe.of:
                    if not hasattr(obj, fn):
                        raise TypeError("cannot fill {0} (missing field \"{1}\") where an object of type {2} is expected".format(obj, fn, tpe))
                    recurse(getattr(obj, fn), ft, name.toRecord(fn))

        else:
            assert False, "unexpected type object: {0}".format(tpe)

    recurse(obj, tpe, ArrayName(prefix, delimiter=delimiter))

    return dict((n.str(), f.finalize()) for n, f in fillables.items())





class LazyList(list):
    __slots__ = ["array", "at", "sub"]

    def __init__(self, array, at, sub):
        self.array = array
        self.at = at
        self.sub = sub

    def __repr__(self):
        dots = ", ..." if len(self) > 4 else ""
        return "[{0}{1}]".format(", ".join(map(repr, self[:4])), dots)

    def __len__(self):
        if self.at == 0:
            return self.array[0]
        else:
            return self.array[self.at] - self.array[self.at - 1]

    def _normalize(self, i, clip, step):
        lenself = len(self)

        if i < 0:
            j = lenself + i
            if j < 0:
                if clip:
                    return 0 if step > 0 else lenself
                else:
                    raise IndexError("LazyList index out of range: {0} for length {1}".format(i, lenself))
            else:
                return j

        elif i < lenself:
            return i

        elif clip:
            return lenself if step > 0 else 0

        else:
            raise IndexError("LazyList index out of range: {0} for length {1}".format(i, lenself))

    def _handleslice(self, i):
        if i.step is None:
            step = 1
        else:
            step = i.step
        if step == 0:
            raise ValueError("slice step cannot be zero")

        lenself = len(self)
        if lenself == 0:
            return LazyListSlice(self, 0, 0, 1)

        if i.start is None:
            if step > 0:
                start = 0
            else:
                start = len(self) - 1
        else:
            start = self._normalize(i.start, True, step)

        if i.stop is None:
            if step > 0:
                stop = len(self)
            else:
                stop = -1
        else:
            stop = self._normalize(i.stop, True, step)

        return LazyListSlice(self, start, stop, step)

    def __getitem__(self, i):
        if isinstance(i, slice):
            return self._handleslice(i)
        else:
            i = self._normalize(i, False, 1)
            if self.at == 0:
                return self.sub(i)
            else:
                return self.sub(self.array[self.at - 1] + i)

    def __getslice__(self, i, j):
        # for old-Python compatibility
        return self.__getitem__(slice(i, j))

    class Iterator(object):
        def __init__(self, lazylist):
            self.lazylist = lazylist
            self.i = 0
            self.length = len(lazylist)

        def __next__(self):
            if self.i >= self.length:
                raise StopIteration
            out = self.lazylist[self.i]
            self.i += 1
            return out

        next = __next__

    def __iter__(self):
        return self.Iterator(self)

    def append(self, *args, **kwds): raise TypeError("LazyList object is immutable (cannot be changed in-place)")
    def __delitem__(self, *args, **kwds): raise TypeError("LazyList object is immutable (cannot be changed in-place)")
    def __delslice__(self, *args, **kwds): raise TypeError("LazyList object is immutable (cannot be changed in-place)")
    def extend(self, *args, **kwds): raise TypeError("LazyList object is immutable (cannot be changed in-place)")
    def __iadd__(self, *args, **kwds): raise TypeError("LazyList object is immutable (cannot be changed in-place)")
    def __imul__(self, *args, **kwds): raise TypeError("LazyList object is immutable (cannot be changed in-place)")
    def insert(self, *args, **kwds): raise TypeError("LazyList object is immutable (cannot be changed in-place)")
    def pop(self, *args, **kwds): raise TypeError("LazyList object is immutable (cannot be changed in-place)")
    def remove(self, *args, **kwds): raise TypeError("LazyList object is immutable (cannot be changed in-place)")
    def reverse(self, *args, **kwds): raise TypeError("LazyList object is immutable (cannot be changed in-place)")
    def __setitem__(self, *args, **kwds): raise TypeError("LazyList object is immutable (cannot be changed in-place)")
    def __setslice__(self, *args, **kwds): raise TypeError("LazyList object is immutable (cannot be changed in-place)")
    def sort(self, *args, **kwds): raise TypeError("LazyList object is immutable (cannot be changed in-place)")

    def __add__(self, other): return list(self) + list(other)
    def __mul__(self, reps): return list(self) * reps
    def __rmul__(self, reps): return reps * list(self)
    def __reversed__(self): return self[::-1]
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

    def __eq__(self, other): return len(self) == len(other) and all(x == y for x, y in zip(self, other))
    def __ne__(self, other): return not self.__eq__(other)
    def __lt__(self, other):
        if isinstance(other, LazyList):
            return list(self) < list(other)
        else:
            return list(self) < other
        
    # __reduce__
    # __reduce_ex__

class LazyListSlice(LazyList):
    __slots__ = ["lazylist", "start", "stop", "step"]

    def __init__(self, lazylist, start, stop, step):
        self.lazylist = lazylist
        self.start = start
        self.stop = stop
        self.step = step

    def __len__(self):
        if self.step == 1:
            return self.stop - self.start
        else:
            return int(math.ceil(float(self.stop - self.start) / self.step))

    def __getitem__(self, i):
        if isinstance(i, slice):
            return self._handleslice(i)
        else:
            return self.lazylist[self.start + self.step*self._normalize(i, False, 1)]

def fromarrays(prefix, arrays, tpe=None, delimiter="-"):
    if tpe is None:
        tpe = columns2type(dict((n, a.dtype) for n, a in arrays.items()), prefix, delimiter=delimiter)

    arrays = dict((ArrayName.parse(n, prefix, delimiter=delimiter), a) for n, a in arrays.items())

    def recurse(tpe, name):
        if isinstance(tpe, Primitive):
            return lambda at: arrays[name][at]

        elif isinstance(tpe, List):
            sub = recurse(tpe.of, name.toListData())
            return lambda at: LazyList(arrays[name.toListOffset()], at, sub)

    return recurse(tpe, ArrayName(prefix, delimiter=delimiter))(0)

