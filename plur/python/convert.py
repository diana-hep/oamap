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

import numpy

from plur.util import *
from plur.types import *
from plur.types.columns import type2columns
from plur.types.columns import columns2type
from plur.types.arrayname import ArrayName
from plur.python.types import infertype
from plur.python.fillmemory import FillableInMemory


class LazyList(object):
    def __init__(self, array, index, sublazy):
        self.array = array
        self.index = index
        self.sublazy = sublazy

    def __len__(self):
        if self.index == 0:
            return self.array[0]
        else:
            return self.array[self.index] - self.array[self.index - 1]

    def __normalize(self, i):
        if i < 0:
            j = len(self) + i
            if j < 0:
                raise IndexError("LazyList index out of range: {0} for length {1}".format(i, len(self)))
            else:
                return j

        elif i < len(self):
            return i

        else:
            raise IndexError("LazyList index out of range: {0} for length {1}".format(i, len(self)))

    def __getitem__(self, i):
        if isinstance(i, slice):
            if i.start is None: start = 0
            else: start = self.__normalize(i.start)

            if i.stop is None: stop = len(self)
            else: stop = self.__normalize(i.stop)

            if i.step is None: step = 1
            else: step = i.step

            if self.index == 0:
                return [self.sublazy(i) for i in range(start, stop, step)]
            else:
                return [self.sublazy(self.array[self.index - 1] + i) for i in xrange(start, stop, step)]

        else:
            i = self.__normalize(i)

            if self.index == 0:
                return self.sublazy(i)
            else:
                return self.sublazy(self.array[self.index - 1] + i)

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

def fromarrays(prefix, arrays, tpe=None, delimiter="-"):
    if tpe is None:
        tpe = columns2type(dict((n, a.dtype) for n, a in arrays.items()), prefix, delimiter=delimiter)

    arrays = dict((ArrayName.parse(n, prefix, delimiter=delimiter), a) for n, a in arrays.items())

    def recurse(tpe, name):
        if isinstance(tpe, Primitive):
            return lambda index: arrays[name][index]

        elif isinstance(tpe, List):
            sublazy = recurse(tpe.of, name.toListData())
            return lambda index: LazyList(arrays[name.toListOffset()], index, sublazy)

    return recurse(tpe, ArrayName(prefix, delimiter=delimiter))(0)


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
