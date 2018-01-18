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

from functools import reduce
try:
    import anydbm as dbm
except ImportError:
    import dbm

import numpy

import oamap.schema
import oamap.generator
import oamap.proxy
import oamap.fill
import oamap.inference

class DBMFile(object):
    DATASET      = "@-"
    PARTITIONING = ":-"
    ARRAY        = "#-"

    class ArrayDict(object):
        def __init__(self, dbmfile, keytrans):
            self.dbmfile = dbmfile
            self.keytrans = keytrans

        def __getitem__(self, key):
            return self.dbmfile.dbm[self.dbmfile.ARRAY + self.keytrans(key)]

        def __setitem__(self, key, value):
            self.dbmfile.dbm[self.dbmfile.ARRAY + self.keytrans(key)] = value
            
    def __init__(self, filename, flag="c", module=dbm):
        self.dbm = module.open(filename, flag)

    def __enter__(self, *args, **kwds):
        return self

    def __exit__(self, *args, **kwds):
        if not self.dbm.isOpen():
            self.dbm.close()

    def close(self):
        self.dbm.close()

    def sync(self):
        self.dbm.sync()

    def iterkeys(self):
        for key in self.dbm.keys():
            if key.startswith(self.DATASET):
                yield key[self.DATASET:]

    def itervalues(self):
        for key in self.iterkeys():
            yield self[key]

    def iteritems(self):
        for key in self.iteritems():
            yield key, self[key]

    def keys(self):
        return list(self.iterkeys())

    def values(self):
        return list(self.itervalues())

    def items(self):
        return list(self.iteritems())

    def __iter__(self):
        return self.iterkeys()

    def __len__(self):
        return sum(1 for x in self.iterkeys())

    def dataset(self, key):
        return oamap.schema.Dataset.fromjsonstring(self.dbm[self.DATASET + key])

    def partitioning(self, key):
        return oamap.schema.Partitioning.fromjsonstring(self.dbm[self.PARTITIONING + key])

    def __contains__(self, key):
        return self.DATASET + key in self.dbm

    def get(self, key, default=None):
        if key in self:
            return self[key]
        else:
            return default

    def __getitem__(self, key):
        dataset = self.dataset(key)

        if dataset.prefix is None:
            prefix = key
        else:
            prefix = dataset.prefix

        partitioning = dataset.partitioning
        if isinstance(partitioning, oamap.schema.ExternalPartitioning):
            partitioning = self.partitioning(partitioning.lookup)

        generator = dataset.schema.generator(prefix=prefix, delimiter=dataset.delimiter)

        if partitioning is None:
            return generator(self.ArrayDict(self, lambda key: key))
        else:
            def makeproxy(i, size):
                arrays = self.ArrayDict(self, lambda key: partitioning.arrayid(key, i))
                cache = oamap.generator.Cache(generator._cachelen)
                return oamap.proxy.ListProxy(array, cache, 0, 1, size)

            listproxies = []
            for i in range(partitioning.numpartitions):
                listproxies.append(makeproxy(i, partitioning.offsets[i + 1] - partitioning.offsets[i]))

            return oamap.proxy.PartitionedListProxy(listproxies, offsets=partitioning.offsets)

    def set(self, key, value, schema=None, limititems=None, limitbytes=None, pointer_fromequal=False):
        if key in self:
            del self[key]
            
        if schema is None:
            schema = oamap.inference.fromdata(value, limititems=limititems)

        if isinstance(schema, oamap.schema.Dataset):
            dataset = schema
            schema = dataset.schema
        else:
            dataset = oamap.schema.Dataset(schema, prefix=key)

        if isinstance(dataset.partitioning, oamap.schema.ExternalPartitioning):
            partitioning = oamap.schema.PrefixPartitioning()
            if dataset.delimiter is not None:
                partitioning.delimiter = dataset.delimiter
        else:
            partitioning = dataset.partitioning

        if limitbytes is None:
            arrays = oamap.fill.toarrays(oamap.fill.fromdata(value, generator=schema, pointer_fromequal=pointer_fromequal))

            if partitioning is None:
                for n, x in arrays.items():
                    self.dbm[self.ARRAY + n] = x
            else:
                for n, x in arrays.items():
                    self.dbm[partitioning.arrayid(self.ARRAY + n, 0)] = x

        else:
            raise NotImplementedError

        if isinstance(dataset.partitioning, oamap.schema.ExternalPartitioning):
            self.dbm[self.PARTITIONING + key] = partitioning.tojsonstring()

        self.dbm[self.DATASET + key] = dataset.tojsonstring()

    def __setitem__(self, key, value):
        self.set(key, value)
        
    def __delitem__(self, key):
        dataset = oamap.schema.Dataset.fromjsonstring(self.dbm.pop(self.DATASET + key))

        if dataset.prefix is None:
            prefix = key
        else:
            prefix = dataset.prefix

        partitioning = dataset.partitioning
        if isinstance(partitioning, oamap.schema.ExternalPartitioning):
            partitioning = oamap.schema.Partitioning.fromjsonstring(self.dbm.pop(self.PARTITIONING + key))

        generator = dataset.schema.generator(prefix=prefix, delimiter=delimiter)
        names = generator.names()

        if partitioning is None:
            for name in names:
                del self.dbm[self.ARRAY + name]
        else:
            for i in range(partitioning.numpartitions):
                del self.dbm[self.ARRAY + partitioning.arrayid(name, i)]

    def __eq__(self, other):
        return dict(self) == dict(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return dict(self) < dict(other)

    def __le__(self, other):
        return self < other or self == other

    def __ge__(self, other):
        return not self < other

    def __gt__(self, other):
        return self >= other and not self == other

    def __cmp__(self, other):
        if self < other:
            return -1
        elif self == other:
            return 0
        else:
            return 1

    def clear(self):
        for key in [x for x in self.dbm.keys() if x.startswith(self.DATASET) or x.startswith(self.PARTITIONING) or x.startswith(self.ARRAY)]:
            del self.dbm[key]

    def has_key(self, key):
        return key in self

    def update(self, items=(), **kwds):
        if hasattr(items, "keys"):
            for key in items.keys():
                self[key] = items[key]
        else:
            for key, value in items:
                self[key] = value

        for key, value in kwds.items():
            self[key] = value
    
    def pop(self, **args):
        raise NotImplementedError

    def popitem(self, **args):
        raise NotImplementedError

    def setdefault(self, key, default=None):
        if key not in self:
            self[key] = default
        return self[key]

    def viewkeys(self, *args, **kwds):
        raise NotImplementedError

    def viewvalues(self, *args, **kwds):
        raise NotImplementedError

    def viewitems(self, *args, **kwds):
        raise NotImplementedError
