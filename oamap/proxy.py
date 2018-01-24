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

import bisect
import json
import numbers
import sys
import math

import numpy

import oamap.util

if sys.version_info[0] > 2:
    xrange = range

# base class of all runtime types that require proxies: List, Record, and Tuple
class Proxy(object): pass

def tojson(value):
    if isinstance(value, ListProxy):
        return [tojson(x) for x in value]
    elif isinstance(value, RecordProxy):
        return dict((n, tojson(getattr(value, n))) for n in value._fields)
    elif isinstance(value, TupleProxy):
        return [tojson(x) for x in value]
    elif isinstance(value, numbers.Integral):
        return int(value)
    elif isinstance(value, numbers.Real):
        if math.isnan(value):
            return "nan"
        elif value == float("-inf"):
            return "-inf"
        elif value == float("inf"):
            return "inf"
        else:
            return float(value)
    elif isinstance(value, numbers.Complex):
        return {"real": tojson(value.real), "imag": tojson(value.imag)}
    elif isinstance(value, numpy.ndarray):
        return value.tolist()
    else:
        return value

def tojsonstring(value, *args, **kwds):
    return json.dumps(tojson(value), *args, **kwds)

def tojsonfile(file, value, *args, **kwds):
    json.dump(file, tojson(value), *args, **kwds)

################################################################ Lists

class ListProxy(Proxy):
    __slots__ = ["_generator", "_arrays", "_cache", "_whence", "_stride", "_length"]

    def __init__(self, generator, arrays, cache, whence, stride, length):
        assert stride != 0
        assert length >= 0
        self._generator = generator
        self._arrays = arrays
        self._cache = cache
        self._whence = whence
        self._stride = stride
        self._length = length

    def __repr__(self, memo=None):
        if memo is None:
            memo = set()
        key = (id(self._generator), self._whence, self._stride, self._length)
        if key in memo:
            return "[...]"
        memo = memo.union(set([key]))
        if len(self) > 10:
            before = self[:5]
            after = self[-5:]
            return "[{0}, ..., {1}]".format(", ".join(x.__repr__(memo) if isinstance(x, (ListProxy, TupleProxy)) else repr(x) for x in before),
                                            ", ".join(x.__repr__(memo) if isinstance(x, (ListProxy, TupleProxy)) else repr(x) for x in after))
        else:
            return "[{0}]".format(", ".join(x.__repr__(memo) if isinstance(x, (ListProxy, TupleProxy)) else repr(x) for x in self))

    def __str__(self):
        return repr(self)

    def indexed(self):
        return self

    def __len__(self):
        return self._length

    def __getslice__(self, start, stop):
        return self.__getitem__(slice(start, stop))

    def __getitem__(self, index):
        if isinstance(index, slice):
            start, stop, step = oamap.util.slice2sss(index, self._length)

            whence = self._whence + self._stride*start
            stride = self._stride*step

            # length = int(math.ceil(float(abs(stop - start)) / abs(step)))
            d, m = divmod(abs(start - stop), abs(step))
            length = d + (1 if m != 0 else 0)

            return ListProxy(self._generator, self._arrays, self._cache, whence, stride, length)

        else:
            normalindex = index if index >= 0 else index + self._length
            if not 0 <= normalindex < self._length:
                raise IndexError("index {0} is out of bounds for size {1}".format(index, self._length))
            return self._generator.content._generate(self._arrays, self._whence + self._stride*normalindex, self._cache)

    def __iter__(self):
        return (self._generator.content._generate(self._arrays, i, self._cache) for i in xrange(self._whence, self._whence + self._stride*self._length, self._stride))

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

class PartitionedListProxy(ListProxy):
    def __init__(self, makepartitions):
        self._makepartitions = makepartitions

    def __repr__(self):
        out = []
        for x in self:
            if len(out) == 5:
                return "[{0}, ...]".format(", ".join(repr(y) for y in out))
            out.append(x)
        return "[{0}]".format(", ".join(repr(y) for y in out))

    def indexed(self):
        return IndexedPartitionedListProxy([x() for x in self._makepartitions])

    def __iter__(self):
        for makepartition in self._makepartitions:
            partition = makepartition()
            for x in partition:
                yield x

    def __len__(self):
        # could be slow because it has to load all of those partitions
        return len(self.indexed())

    def __getitem__(self, index):
        # could be slow because it has to load all of those partitions
        return self.indexed()[index]

class IndexedPartitionedListProxy(PartitionedListProxy):
    def __init__(self, partitions, offsets=None):
        self._partitions = partitions

        if offsets is None:
            self._offsets = []
            partitionindex = 0
            for partition in partitions:
                self._offsets.append(partitionindex)
                partitionindex += len(partition)
            self._offsets.append(partitionindex)
        else:
            self._offsets = offsets

        assert len(self._partitions) + 1 == len(self._offsets)

    def __repr__(self):
        if len(self) > 10:
            return "[{0}, ..., {1}]".format(", ".join(repr(x) for x in self[:5]), ", ".join(repr(x) for x in self[-5:]))
        else:
            return "[{0}]".format(", ".join(repr(x) for x in self))

    def indexed(self):
        return self

    def __iter__(self):
        for partition in self._partitions:
            # copy the partition's cache so that arrays loaded during iteration don't persist (but any already-loaded arrays do)
            copy = ListProxy(partition._generator, partition._arrays, list(partition._cache), partition._whence, partition._stride, partition._length)
            for x in copy:
                yield x

    def __len__(self):
        return self._offsets[-1]

    def __getitem__(self, index):
        if isinstance(index, slice):
            start, stop, step = oamap.util.slice2sss(index, self._offsets[-1])

            if start == self._offsets[-1]:
                assert step > 0
                assert stop == self._offsets[-1]
                return IndexedPartitionedListProxy([])

            elif start == -1:
                assert step < 0
                assert stop == -1
                return IndexedPartitionedListProxy([])

            else:
                partitions = []
                if step > 0:
                    firstid = bisect.bisect_right(self._offsets, start) - 1
                    lastid = bisect.bisect_right(self._offsets, stop) - 1
                    includelast = 1 if stop > self._offsets[lastid] else 0
                    skip = 0
                    for partitionid in range(firstid, lastid + includelast):
                        partition = self._partitions[partitionid]

                        if partitionid == firstid:
                            localstart = start - self._offsets[partitionid]
                        else:
                            localstart = skip

                        if partitionid == lastid:
                            localstop = stop - self._offsets[partitionid]
                        else:
                            localstop = len(partition)
                            
                        skip = (step - (len(partition) - localstart)) % step
                        partitions.append(partition[localstart:localstop:step])

                else:
                    posstep = -step   # avoid negative modulo
                    firstid = bisect.bisect_right(self._offsets, start) - 1
                    lastid = bisect.bisect_right(self._offsets, stop) - 1
                    skip = 1
                    for partitionid in range(firstid, max(-1, lastid - 1), -1):
                        partition = self._partitions[partitionid]

                        if partitionid == firstid:
                            localstart = start - self._offsets[partitionid]
                        else:
                            localstart = len(partition) - skip

                        if partitionid == lastid:
                            localstop = stop - self._offsets[partitionid]
                        else:
                            localstop = -1

                        skip = (((posstep - 1) - localstart) % posstep) + 1
                        if localstart >= 0:
                            if localstop >= 0:
                                partitions.append(partition[localstart:localstop:step])
                            else:
                                partitions.append(partition[localstart::step])

                return IndexedPartitionedListProxy(partitions)

        else:
            normalindex = index if index >= 0 else index + self._offsets[-1]
            if not 0 <= normalindex < self._offsets[-1]:
                raise IndexError("index {0} is out of bounds for size {1}".format(index, self._offsets[-1]))

            partitionid = bisect.bisect_right(self._offsets, normalindex) - 1
            assert 0 <= partitionid < len(self._partitions)

            localindex = normalindex - self._offsets[partitionid]
            return self._partitions[partitionid][localindex]

################################################################ Records

class RecordProxy(Proxy):
    __slots__ = ["_generator", "_arrays", "_cache", "_index"]

    def __init__(self, generator, arrays, cache, index):
        self._generator = generator
        self._arrays = arrays
        self._cache = cache
        self._index = index

    def __repr__(self):
        return "<{0} at index {1}>".format("Record" if self._generator.name is None else self._generator.name, self._index)

    def __str__(self):
        return repr(self)

    @property
    def _fields(self):
        return list(self._generator.fields)

    def __dir__(self):
        return dir(super(RecordProxy, self)) + list(str(x) for x in self._fields)

    def __getattr__(self, field):
        if field.startswith("_"):
            return self.__dict__[field]
        else:
            try:
                generator = self._generator.fields[field]
            except KeyError:
                raise AttributeError("{0} object has no attribute {1}".format(repr("Record" if self._generator.name is None else self._generator.name), repr(field)))
            else:
                return generator._generate(self._arrays, self._index, self._cache)

    def __hash__(self):
        return hash((RecordProxy, self._generator.name) + tuple(self._generator.fields.items()))

    def __eq__(self, other):
        return isinstance(other, RecordProxy) and self._generator.name == other._generator.name and set(self._generator.fields) == set(other._generator.fields) and all(self.__getattr__(n) == other.__getattr__(n) for n in self._generator.fields)

    def __lt__(self, other):
        if isinstance(other, RecordProxy) and self._generator.name == other._generator.name and set(self._generator.fields) == set(other._generator.fields):
            return [self.__getattr__(n) for n in self._generator.fields] < [other.__getattr__(n) for n in self._generator.fields]
        else:
            raise TypeError("unorderable types: {0}() < {1}()".format("<type 'Record'>" if self._generator.name is None else "<type {0}>".format(repr(self._generator.name)), other.__class__))

    def __ne__(self, other): return not self.__eq__(other)
    def __le__(self, other): return self.__lt__(other) or self.__eq__(other)
    def __gt__(self, other): return not self.__lt__(other) and not self.__eq__(other)
    def __ge__(self, other): return not self.__lt__(other)

################################################################ Tuples

class TupleProxy(Proxy):
    __slots__ = ["_generator", "_arrays", "_cache", "_index"]

    def __init__(self, generator, arrays, cache, index):
        self._generator = generator
        self._arrays = arrays
        self._cache = cache
        self._index = index

    def __repr__(self, memo=None):
        if memo is None:
            memo = set()
        key = (self._index,) + tuple(id(x) for x in self._generator.types)
        if key in memo:
            return "(...)"
        memo = memo.union(set([key]))
        return "({0}{1})".format(", ".join(x.__repr__(memo) if isinstance(x, (ListProxy, TupleProxy)) else repr(x) for x in self), "," if len(self) == 1 else "")

    def __str__(self):
        return repr(self)

    def __len__(self):
        return len(self._generator.types)

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
            return self._generator.types[index]._generate(self._arrays, self._index, self._cache)

    def __iter__(self):
        return (t._generate(self._arrays, self._index, self._cache) for t in self._generator.types)

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
