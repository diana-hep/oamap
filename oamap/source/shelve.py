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

import codecs
import importlib
from functools import reduce
try:
    import anydbm as dbm
except ImportError:
    import dbm
try:
    from UserDict import DictMixin as MutableMapping
except ImportError:
    from collections import MutableMapping

import numpy

import oamap.schema
import oamap.generator
import oamap.proxy
import oamap.fill
import oamap.fillable
import oamap.inference

def _asbytes(string):
    if isinstance(string, bytes):
        return string
    else:
        return codecs.utf_8_encode(string)[0]

def open(filename, flag="c", module=dbm):
    return DbfilenameShelf(filename, flag=flag, module=module)

class DbfilenameShelf(MutableMapping):
    DATASET      = "@-"
    PARTITIONING = ":-"
    ARRAY        = "#-"

    class ArrayDict(object):
        def __init__(self, dbmfile, keytrans):
            self.dbmfile = dbmfile
            self.keytrans = keytrans

        def __getitem__(self, key):
            return self.dbmfile.dbm[_asbytes(self.dbmfile.ARRAY + self.keytrans(key))]

        def __setitem__(self, key, value):
            self.dbmfile.dbm[_asbytes(self.dbmfile.ARRAY + self.keytrans(key))] = value
            
    def __init__(self, filename, flag="c", module=dbm):
        self.dbm = module.open(filename, flag)

    def __repr__(self):
        return "{" + ", ".join("{0}: <Dataset>".format(repr(n)) for n in self) + "}"

    @property
    def closed(self):
        return not self.dbm.isOpen()

    def close(self):
        self.sync()
        self.dbm.close()

    def sync(self):
        if hasattr(self.dbm, "sync"):
            self.dbm.sync()

    def __enter__(self, *args, **kwds):
        return self

    def __exit__(self, *args, **kwds):
        if not self.closed:
            self.close()

    def iterkeys(self):
        for key in self.dbm.keys():
            if key.startswith(self.DATASET):
                yield key[len(self.DATASET):]

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
        return oamap.schema.Dataset.fromjsonstring(codecs.utf_8_decode(self.dbm[_asbytes(self.DATASET + key)])[0])

    def schema(self, key):
        return self.dataset(key).schema
   
    def __contains__(self, key):
        return self.DATASET + key in self.dbm

    def has_key(self, key):
        return key in self

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
            extension = importlib.import_module("oamap.extension.common")
        elif isinstance(dataset.extension, basestring):
            extension = importlib.import_module(dataset.extension)
        else:
            extension = [importlib.import_module(x) for x in dataset.extension]

        partitioning = dataset.partitioning
        if isinstance(partitioning, oamap.schema.ExternalPartitioning):
            partitioning = oamap.schema.Partitioning.fromjsonstring(codecs.utf_8_decode(self.dbm[_asbytes(self.PARTITIONING + partitioning.lookup)])[0])

        generator = dataset.schema.generator(prefix=prefix, delimiter=delimiter, extension=extension)

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
        if schema is None:
            schema = oamap.inference.fromdata(value, limititems=limititems)

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
            extension = importlib.import_module("oamap.extension.common")
        elif isinstance(dataset.extension, basestring):
            extension = importlib.import_module(dataset.extension)
        else:
            extension = [importlib.import_module(x) for x in dataset.extension]

        generator = schema.generator(prefix=prefix, delimiter=delimiter, extension=extension)

        if isinstance(dataset.partitioning, oamap.schema.ExternalPartitioning):
            partitioning = oamap.schema.PrefixPartitioning()
            if dataset.delimiter is not None:
                partitioning.delimiter = dataset.delimiter
        else:
            partitioning = dataset.partitioning

        if limitbytes is None:
            arrays = oamap.fill.toarrays(oamap.fill.fromdata(value, generator=generator, pointer_fromequal=pointer_fromequal))

            if key in self:
                del self[key]

            if partitioning is None:
                for n, x in arrays.items():
                    self.dbm[_asbytes(self.ARRAY + n)] = x
            else:
                for n, x in arrays.items():
                    self.dbm[_asbytes(partitioning.arrayid(self.ARRAY + n, 0))] = x

        else:
            if partitioning is None:
                partitioning = dataset.partitioning = oamap.schema.PrefixPartitioning()

            iter(value)
            if key in self:
                del self[key]

            fillables = oamap.fillable.arrays(generator)
            for item in value:
                pass


                
            generator.content











        if isinstance(dataset.partitioning, oamap.schema.ExternalPartitioning):
            self.dbm[_asbytes(self.PARTITIONING + key)] = partitioning.tojsonstring()

        self.dbm[_asbytes(self.DATASET + key)] = dataset.tojsonstring()

    def __setitem__(self, key, value):
        self.set(key, value)
        
    def __delitem__(self, key):
        dataset = oamap.schema.Dataset.fromjsonstring(codecs.utf_8_decode(self.dbm.pop(self.DATASET + key))[0])

        if dataset.prefix is None:
            prefix = key
        else:
            prefix = dataset.prefix

        if dataset.delimiter is None:
            delimiter = "-"
        else:
            delimiter = dataset.delimiter

        partitioning = dataset.partitioning
        if isinstance(partitioning, oamap.schema.ExternalPartitioning):
            partitioning = oamap.schema.Partitioning.fromjsonstring(codecs.utf_8_decode(self.dbm.pop(self.PARTITIONING + key))[0])

        generator = dataset.schema.generator(prefix=prefix, delimiter=delimiter)
        names = generator.names()

        if partitioning is None:
            for name in names:
                del self.dbm[_asbytes(self.ARRAY + name)]
        else:
            for i in range(partitioning.numpartitions):
                del self.dbm[_asbytes(self.ARRAY + partitioning.arrayid(name, i))]

    def clear(self):
        for key in [x for x in self.dbm.keys() if x.startswith(self.DATASET) or x.startswith(self.PARTITIONING) or x.startswith(self.ARRAY)]:
            del self.dbm[_asbytes(key)]
