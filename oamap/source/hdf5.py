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

import numpy

import oamap.schema
import oamap.proxy
import oamap.inference
import oamap.fill
from oamap.util import import_module

try:
    import h5py
except ImportError:
    pass
else:
    h5py._hl.group.Group.oamap = property(lambda self: OAMapGroup(self._id))

    class OAMapGroup(h5py._hl.group.Group):
        class _ArrayDict(object):
            def __init__(self, group, keytrans):
                self.group = group
                self.keytrans = keytrans

            def __getitem__(self, key):
                return self.group.__getitem__(self.keytrans(key))

            def __setitem__(self, key, value):
                self.group.__setitem__(self.keytrans(key), value)

        def __init__(self, id):
            self._id = id

        def __repr__(self):
            return "<OAMap HDF5 group \"{0}\" ({1} members)>".format(self.name, len(self))

        def __str__(self):
            return __repr__(self)

        def schema(self, key):
            return self.dataset(key).schema

        def isdataset(self, key):
            value = self.attrs[key]
            try:
                oamap.schema.Dataset.fromjsonstring(value)
            except:
                return False
            else:
                return True

        def dataset(self, key):
            return oamap.schema.Dataset.fromjsonstring(self.attrs[key])
      
        def keys(self):
            for key in super(OAMapGroup, self).keys():
                if self.isdataset(key):
                    yield key
                    
        def values(self):
            return (self[n] for n in self.keys())

        def items(self):
            return ((n, self[n]) for n in self.keys())

        def __len__(self):
            return sum(1 for key in self)

        def __iter__(self):
            return self.keys()

        def __dict__(self):
            return dict(self.items())

        def __contains__(self, key):
            return super(OAMapGroup, self).__contains__(key) and self.isdataset(key)

        def __getitem__(self, key):
            dataset = self.dataset(key)

            if dataset.prefix is None:
                prefix = key
            else:
                prefix = dataset.prefix

            if dataset.delimiter is None:
                delimiter = "-"
            else:
                delimiter = dataset.delimiter

            if dataset.extension is None:
                extension = import_module("oamap.extension.common")
            elif isinstance(dataset.extension, basestring):
                extension = import_module(dataset.extension)
            else:
                extension = [import_module(x) for x in dataset.extension]

            generator = dataset.schema.generator(prefix=prefix, delimiter=delimiter, extension=extension)

            if dataset.partitioning is None:
                return generator(self._ArrayDict(super(OAMapGroup, self), lambda key: key))

            else:
                partitionlookup = dataset.partitioning.partitionlookup(super(OAMapGroup, self).__getitem__(dataset.partitioning.key), delimiter)
                def makearrays(i):
                    return self._ArrayDict(super(OAMapGroup, self), lambda key: partitionlookup.id2name(key, i))

                listofarrays = []
                for i in range(partitionlookup.numpartitions):
                    listofarrays.append(makearrays(i))

                return oamap.proxy.IndexedPartitionedListProxy(generator, listofarrays, offsets=partitionlookup.offsets)

        def fromdata(self, key, value, schema=None, inferencelimit=None, partitionlimit=None, pointer_fromequal=False):
            if schema is None:
                schema = oamap.inference.fromdata(value, limit=inferencelimit)
            if partitionlimit is not None:
                if not (isinstance(schema, oamap.schema.List) and not schema.nullable):
                    raise TypeError("if limit is not None, the schema must be a partitionable List")
                if not callable(partitionlimit):
                    raise TypeError("partitionlimit must be None or a callable function")

            if isinstance(schema, oamap.schema.Dataset):
                dataset = schema
                schema = dataset.schema
            else:
                dataset = oamap.schema.Dataset(schema, prefix=key)

            if dataset.prefix is None:
                prefix = key
            else:
                prefix = dataset.prefix

            if dataset.delimiter is None:
                delimiter = "-"
            else:
                delimiter = dataset.delimiter

            if dataset.extension is None:
                extension = import_module("oamap.extension.common")
            elif isinstance(dataset.extension, basestring):
                extension = import_module(dataset.extension)
            else:
                extension = [import_module(x) for x in dataset.extension]

            generator = schema.generator(prefix=prefix, delimiter=delimiter, extension=extension)

            if partitionlimit is None:
                arrays = oamap.fill.fromdata(value, generator=generator, pointer_fromequal=pointer_fromequal)
                for n in arrays:
                    if super(OAMapGroup, self).__contains__(n):
                        raise RuntimeError("cannot assign to {0} (dataset exists)".format(repr(n)))

                if dataset.partitioning is None:
                    for n, x in arrays.items():
                        super(OAMapGroup, self).__setitem__(n, x)

                else:
                    partitionlookup = dataset.partitioning.empty_partitionlookup(delimiter)
                    partitionlookup.append(arrays[generator.stops][0] - arrays[generator.starts][0], arrays.keys())

                    for n, x in arrays.items():
                        super(OAMapGroup, self).__setitem__(partitionlookup.id2name(n, 0), x)
                    super(OAMapGroup, self).__setitem__(dataset.partitioning.key, numpy.array(partitionlookup))

                self.attrs[key] = dataset.tojsonstring()

            else:
                dataset = dataset.copy(partitioning=dataset._get_partitioning(prefix, delimiter))

                partitionlookup = dataset.partitioning.empty_partitionlookup(delimiter)

                super(OAMapGroup, self).__setitem__(dataset.partitioning.key, numpy.array(partitionlookup))
                self.attrs[key] = dataset.tojsonstring()

                for partitionid, (numentries, arrays) in enumerate(oamap.fill.fromiterdata(value, generator=generator, limit=partitionlimit, pointer_fromequal=pointer_fromequal)):
                    partitionlookup.append(numentries, arrays.keys())

                    for n in arrays:
                        if super(OAMapGroup, self).__contains__(n):
                            raise RuntimeError("cannot assign to {0} (dataset exists)".format(repr(n)))
                    for n, x in arrays.items():
                        super(OAMapGroup, self).__setitem__(partitionlookup.id2name(n, partitionid), x)
                    super(OAMapGroup, self).__delitem__(dataset.partitioning.key)
                    super(OAMapGroup, self).__setitem__(dataset.partitioning.key, numpy.array(partitionlookup))

        def __setitem__(self, key, value):
            self.fromdata(key, value)

        def __delitem__(self, key):
            dataset = self.dataset(key)
            del self.attrs[key]

            if dataset.prefix is None:
                prefix = key
            else:
                prefix = dataset.prefix

            if dataset.delimiter is None:
                delimiter = "-"
            else:
                delimiter = dataset.delimiter

            generator = dataset.schema.generator(prefix=prefix, delimiter=delimiter)
            names = generator.names()

            if dataset.partitioning is None:
                for name in names:
                    super(OAMapGroup, self).__delitem__(name)

            else:
                partitionlookup = dataset.partitioning.partitionlookup(super(OAMapGroup, self).__getitem__(dataset.partitioning.key), delimiter)
                super(OAMapGroup, self).__delitem__(dataset.partitioning.key)

                for name in names:
                    for i in range(partitionlookup.numpartitions):
                        super(OAMapGroup, self).__delitem__(partitionlookup.id2name(name, i))

        def setdefault(self, key, default=None):
            if key not in self:
                self[key] = default
            return self[key]

        def pop(self, **args):
            return self.popitem(**args)[1]

        def popitem(self, **args):
            if len(args) == 0:
                if len(self) > 0:
                    key, = self.keys()
                else:
                    raise IndexError("pop from empty OAMapGroup")
            elif len(args) == 1:
                key, = args
            elif len(args) == 2:
                key, default = args
            else:
                raise TypeError("popitem expected at most 2 arguments, got {0}".format(len(args)))

            if key in self:
                out = (key, self[key])
                del self[key]
                return out
            elif len(args) == 2:
                return default
            else:
                raise KeyError(repr(key))

        def update(self, other):
            for n, x in other.items():
                self[n] = x
