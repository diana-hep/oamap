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
        self._active = {}
        self._partitionid = None

    def _toplevel(self, out, filtered):
        return filtered

    def getall(self, roles):
        out = {}
        for namespace, backend in self._backends.items():
            filtered = self._toplevel(out, [x for x in roles if x.namespace == namespace])

            if len(filtered) > 0:
                active = self._active.get(namespace, None)
                if active is None:
                    active = self._active[namespace] = backend.instantiate(self._partitionid)

                if hasattr(active, "getall"):
                    out.update(active.getall(filtered))
                else:
                    for x in roles:
                        out[x] = active[str(x)]

        return out

    def close(self):
        for namespace, active in self._active.items():
            if hasattr(active, "close"):
                active.close()
            self._active[namespace] = None
                
class Dataset(Data):
    def __init__(self, name, schema, backends, offsets=None, packing=None, extension=None, doc=None, metadata=None, prefix="object", delimiter="-"):
        if not isinstance(schema, oamap.schema.List):
            raise TypeError("Dataset must have a list schema, not\n\n    {0}".format(schema.__repr__(indent="    ")))

        super(Dataset, self).__init__(name, schema, backends, packing=packing, extension=extension, doc=doc, metadata=metadata, prefix=prefix, delimiter=delimiter)

        if not isinstance(offsets, numpy.ndarray):
            try:
                if not all(isinstnace(x, numbers.Integral) and x >= 0 for x in offests):
                    raise TypeError
            except TypeError:
                raise TypeError("offsets must be an iterable of non-negative integers")
            offsets = numpy.array(offsets, dtype=numpy.int64)
        if len(offsets.shape) != 1:
            raise ValueError("offsets must be one-dimensional")
        if len(offsets) < 2 or offsets[0] != 0:
            raise ValueError("offsets must have at least two items, and the first one must be zero")
        if not numpy.all(offsets[:-1] <= offsets[1:]):
            raise ValueError("offsets must be monotonically increasing")

    def __repr__(self):
        return "<Dataset {0} {1} partitions {2} entries>".format(repr(self._name), self.numpartitions, self.numentries)

    @property
    def numpartitions(self):
        return len(self._offsets) - 1

    @property
    def numentries(self):
        return int(self._offsets[-1])

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
        return DatasetArrays(normid, startsrole, stopsrole, self._offsets[normid + 1] - self._offsets[normid], self._backends)

class DatasetArrays(DataArrays):
    def __init__(self, partitionid, startsrole, stopsrole, numentries, backends):
        super(DatasetArrays, self).__init__(backends)
        self._partitionid = partitionid
        self._startsrole = startsrole
        self._stopsrole = stopsrole
        self._numentries = numentries

    def _toplevel(self, out, filtered):
        try:
            index = filtered.index(self._startsrole)
        except ValueError:
            pass
        else:
            del filtered[index]
            out[self._startsrole] = numpy.array([0], dtype=oamap.generator.ListGenerator.posdtype)

        try:
            index = filtered.index(self._stopsrole)
        except ValueError:
            pass
        else:
            del filtered[index]
            out[self._stopsrole] = numpy.array([self._numentries], dtype=oamap.generator.ListGenerator.posdtype)

        return filtered
