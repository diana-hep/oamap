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
import json
from collections import namedtuple

import numpy

from plur.util import *
from plur.types import *
from plur.types.columns import type2columns
from plur.types.columns import columns2type
from plur.types.arrayname import ArrayName
from plur.python.types import infertype
from plur.python.fillmemory import FillableInMemory

##################################################################### toarrays

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
            
            length = 0
            for x in obj:
                recurse(x, tpe.of, namedata)
                length += 1

            if nameoffset not in last_list_offset:
                last_list_offset[nameoffset] = 0
            last_list_offset[nameoffset] += length

            fillables[nameoffset].fill(last_list_offset[nameoffset])

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

##################################################################### lazy objects

class Lazy(object):
    def toJsonString(self):
        return json.dumps(self.toJson())

    def toJson(self):
        raise NotImplementedError

class LazyList(list, Lazy):
    __slots__ = ["array", "at", "sub"]

    def __init__(self, array, at, sub):
        self._array = array
        self._at = at
        self._sub = sub

    def __repr__(self):
        dots = ", ..." if len(self) > 4 else ""
        return "[{0}{1}]".format(", ".join(map(repr, self[:4])), dots)

    def __len__(self):
        if self._at == 0:
            return self._array[0]
        else:
            return self._array[self._at] - self._array[self._at - 1]

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
            if self._at == 0:
                return self._sub(i)
            else:
                return self._sub(self._array[self._at - 1] + i)

    def __getslice__(self, i, j):
        # for old-Python compatibility
        return self.__getitem__(slice(i, j))

    class Iterator(object):
        def __init__(self, lazylist):
            self._lazylist = lazylist
            self._i = 0
            self._length = len(lazylist)

        def __next__(self):
            if self._i >= self._length:
                raise StopIteration
            out = self._lazylist[self._i]
            self._i += 1
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

    def __eq__(self, other):
        return isinstance(other, list) and len(self) == len(other) and all(x == y for x, y in zip(self, other))

    def __lt__(self, other):
        if isinstance(other, LazyList):
            return list(self) < list(other)
        elif isinstance(other, list):
            return list(self) < other
        else:
            raise TypeError("unorderable types: {0} < {1}".format(self.__class__, other.__class__))

    def __ne__(self, other): return not self.__eq__(other)
    def __le__(self, other): return self.__lt__(other) or self.__eq__(other)
    def __gt__(self, other):
        if isinstance(other, LazyList):
            return list(self) > list(other)
        else:
            return list(self) > other
    def __ge__(self, other): return self.__gt__(other) or self.__eq__(other)

    def toJson(self):
        return [toJson(x) for x in self]

class LazyListSlice(LazyList):
    __slots__ = ["lazylist", "start", "stop", "step"]

    def __init__(self, lazylist, start, stop, step):
        self._lazylist = lazylist
        self._start = start
        self._stop = stop
        self._step = step

    def __len__(self):
        if self._step == 1:
            return self._stop - self._start
        else:
            return int(math.ceil(float(self._stop - self._start) / self._step))

    def __getitem__(self, i):
        if isinstance(i, slice):
            return self._handleslice(i)
        else:
            return self._lazylist[self._start + self._step*self._normalize(i, False, 1)]

class LazyRecord(Lazy):
    def __repr__(self):
        return repr(detach(self))

    def __eq__(self, other):
        return isinstance(other, LazyRecord) and self._fields == other._fields and all(getattr(self, fn) == getattr(other, fn) for fn in self._fields)

    def __lt__(self, other):
        if isinstance(other, LazyRecord):
            if len(self._fields) > len(other._fields):
                return True

            elif len(self._fields) < len(other._fields):
                return False

            elif self._fields == other._fields:
                return tuple(getattr(self, n) for n in self._fields) < tuple(getattr(other, n) for n in self._fields)

            else:
                return self._fields < other._fields

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

    def toJson(self):
        return dict((fn, toJson(getattr(self, fn))) for fn in self._fields)

##################################################################### detach lazy -> persistent

def detach(obj):
    if isinstance(obj, numpy.bool_):
        return True if obj else False
    elif isinstance(obj, numpy.integer):
        return int(obj)
    elif isinstance(obj, numpy.floating):
        return float(obj)
    elif isinstance(obj, numpy.complexfloating):
        return complex(obj)
    elif isinstance(obj, LazyList):
        return [detach(x) for x in obj]
    elif isinstance(obj, LazyRecord):
        return obj._namedtuple(*[getattr(obj, fn) for fn in obj._fields])
    else:
        return obj

def toJson(obj):
    if isinstance(obj, Lazy):
        return obj.toJson()
    else:
        return detach(obj)

##################################################################### fromarrays

def fromarrays(prefix, arrays, tpe=None, delimiter="-"):
    if tpe is None:
        tpe = columns2type(dict((n, a.dtype) for n, a in arrays.items()), prefix, delimiter=delimiter)

    arrays = dict((ArrayName.parse(n, prefix, delimiter=delimiter), a) for n, a in arrays.items())

    def recurse(tpe, name, lastgoodname):
        # P
        if isinstance(tpe, Primitive):
            array = arrays[name]
            return lambda at: array[at]

        # L
        elif isinstance(tpe, List):
            sub = recurse(tpe.of, name.toListData(), lastgoodname)
            return lambda at: LazyList(arrays[name.toListOffset()], at, sub)

        # U
        elif isinstance(tpe, Union):
            tagarray = arrays[name.toUnionTag()]
            offsetarray = arrays[name.toUnionOffset()]
            subs = [recurse(x, name.toUnionData(i), lastgoodname) for i, x in enumerate(tpe.of)]
            return lambda at: subs[tagarray[at]](offsetarray[at])
            
        # R
        elif isinstance(tpe, Record):
            fieldnames = [fn for fn, ft in tpe.of]
            subs = dict((fn, recurse(ft, name.toRecord(fn), fn)) for fn, ft in tpe.of)

            class SpecificLazyRecord(LazyRecord):
                __slots__ = ["__at"]
                _fields = fieldnames
                _namedtuple = namedtuple(lastgoodname, fieldnames)

                def __init__(self, at):
                    self.__at = at

                def __getattr__(self, name):
                    try:
                        f = subs[name]
                    except KeyError:
                        raise AttributeError("LazyRecord has no attribute \"{0}\"".format(name))
                    else:
                        return f(self.__at)

            return SpecificLazyRecord
                
        else:
            assert False, "unexpected type object: {0}".format(tpe)
            
    return recurse(tpe, ArrayName(prefix, delimiter=delimiter), prefix)(0)
