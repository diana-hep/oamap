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
        self.dbm.close()

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
        return iterkeys()

    def dataset(self, key):
        return oamap.schema.Dataset.fromjsonstring(self.dbm[self.DATASET + key])

    def partitioning(self, key):
        return oamap.schema.Partitioning.fromjsonstring(self.dbm[self.PARTITIONING + key])

    def __getitem__(self, key):
        dataset = self.dataset(key)

        partitioning = dataset.partitioning
        if isinstance(partitioning, oamap.schema.ExternalPartitioning):
            partitioning = self.partitioning(partitioning.lookup)

        if partitioning is None:
            return dataset.schema(self.ArrayDict(self, lambda key: key))

        else:
            def makeproxy(i, size):
                generator = dataset.schema.generator()
                arrays = self.ArrayDict(self, lambda key: partitioning.arrayid(key, i))
                cache = oamap.generator.Cache(generator._cachelen)
                return oamap.proxy.ListProxy(array, cache, 0, 1, size)

            listproxies = []
            for i in range(len(partitioning.offsets) - 1):
                listproxies.append(makeproxy(i, partitioning.offsets[i + 1] - partitioning.offsets[i]))

            return oamap.proxy.PartitionedListProxy(listproxies, offsets=partitioning.offsets)

    def __setitem__(self, key, value):
        raise NotImplementedError
