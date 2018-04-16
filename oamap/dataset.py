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

import numbers

import numpy

import oamap.schema
import oamap.generator

class Data(object):
    def __init__(self, name, schema, backends, packing=None, extension=None, doc=None, metadata=None, prefix="object", delimiter="-"):
        self._name = name
        self._schema = schema
        self._backends = backends
        self._packing = packing
        self._extension = spec["extension"]
        self._doc = spec["doc"]
        self._metadata = spec["metadata"]
        self._prefix = prefix
        self._delimiter = delimiter

    def __repr__(self):
        return "<Data {0}>".format(repr(self._name))

    @property
    def name(self):
        return self._name

    @property
    def schema(self):
        return self._schema.deepcopy()

    @property
    def packing(self):
        return self._packing

    @property
    def extension(self):
        return self._extension

    @property
    def doc(self):
        return self._doc

    @property
    def metadata(self):
        return self._metadata

    def __call__(self):
        return self._schema(self.arrays())

    def arrays(self):
        return DataArrays(self._backends)

class DataArrays(object):
    def __init__(self, backends):
        self._backends = backends

    def getall(self, roles):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError

class Dataset(Data):
    def __init__(self, name, schema, backends, starts=None, stops=None, packing=None, extension=None, doc=None, metadata=None, prefix="object", delimiter="-"):
        if not isinstance(schema, oamap.schema.List):
            raise TypeError("Dataset must have a list schema, not\n\n    {0}".format(schema.__repr__(indent="    ")))

        super(Dataset, self).__init__(name, schema, backends, packing=packing, extension=extension, doc=doc, metadata=metadata, prefix=prefix, delimiter=delimiter)

        if not isinstance(starts, numpy.ndarray):
            try:
                if len(x) == 0 or not all(isinstance(x, numbers.Integral) and x >= 0 for x in starts):
                    raise TypeError
            except TypeError:
                raise TypeError("starts must be a non-empty iterable of non-negative integers")
            starts = numpy.array(starts, dtype=numpy.int64)
        if not isinstance(stops, numpy.ndarray):
            try:
                if len(x) == 0 or not all(isinstance(x, numbers.Integral) and x >= 0 for x in stops):
                    raise TypeError
            except TypeError:
                raise TypeError("stops must be a non-empty iterable of non-negative integers")
            stops = numpy.array(stops, dtype=numpy.int64)
        if len(starts.shape) != 1 or len(stops.shape) != 1:
            raise ValueError("starts and stops must be one-dimensional")
        if len(starts) != len(stops) or not numpy.all(starts <= stops):
            raise ValueError("starts have the same length as stops and must all be less than or equal to stops")
        self._starts = starts
        self._stops = stops

    def __repr__(self):
        return "<Dataset {0} {1} partitions {2} entries>".format(repr(self._name), self.numpartitions, self.numentries)

    @property
    def numpartitions(self):
        return len(self._starts)

    @property
    def numentries(self):
        return int((self._stops - self._starts).sum())

    def partition(self, partitionid):
        return self._schema(self.arrays(partitionid))
        
    def __getitem__(self, index):
        if isinstance(index, numbers.Integral):
            raise NotImplementedError("return an entry (global indexing)")

        elif isinstance(index, slice):
            raise NotImplementedError("return a ListProxy if it fits within one partition (global indexing)")

    def arrays(self, partitionid):
        normid = partitionid if partitionid >= 0 else partitionid + self.numpartitions
        if not 0 <= normid < self.numpartitions:
            raise IndexError("partitionid {0} out of range for {1} partitions".format(partitionid, self.numpartitions))

        startsrole = oamap.generator.StartsRole(self._schema._get_starts(self._prefix, self._delimiter), self._schema.namespace, None)
        stopsrole = oamap.generator.StopsRole(self._schema._get_stops(self._prefix, self._delimiter), self._schema.namespace, None)
        startsrole.stops = stopsrole
        stopsrole.starts = startsrole
        return DatasetArrays(normid, startsrole, stopsrole, self._starts[normid], self._stops[normid], self._backends)

class DatasetArrays(DataArrays):
    def __init__(self, partitionid, startsrole, stopsrole, start, stop, backends):
        super(DatasetArrays, self).__init__(backends)
        self._partitionid = partitionid
        self._startsrole = startsrole
        self._stopsrole = stopsrole
        self._start = start
        self._stop = stop

    def getall(self, roles):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError
