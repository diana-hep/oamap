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
import numbers
import os
import sys

import numpy

import oamap.schema
import oamap.proxy

if sys.version_info[0] > 2:
    basestring = str
    unicode = str

################################################################ Namespace

class Namespace(object):
    def __init__(self, backend, partitionargs):
        self.backend = backend
        self.partitionargs = partitionargs

    @property
    def backend(self):
        return self._backend

    @backend.setter
    def backend(self, value):
        if isinstance(value, basestring):
            try:
                i = value.rindex(".")
            except ValueError:
                self._backend = getattr(sys.modules["__main__"], value)
            else:
                self._backend = getattr(importlib.import_module(value[:i]), value[i+1:])

        elif callable(value):
            self._backend = value

        else:
            raise TypeError("backend must be a class or a fully qualified class name")

    @property
    def partitionargs(self):
        return self._partitionargs

    @partitionargs.setter
    def partitionargs(self, value):
        value = list(value)
        if not all(isinstance(x, tuple) for x in value):
            raise TypeError("partitionargs must be an iterable of tuples")
        self._partitionargs = value

    @property
    def numpartitions(self):
        return len(self._partitionargs)

################################################################ Dataset

class Dataset(object):
    def __init__(self, schema, namespace, offsets=None, extension=None, doc=None, metadata=None):
        self.schema = schema
        self.namespace = namespace
        self.offsets = offsets
        self.extension = extension
        self.doc = doc
        self.metadata = metadata

    @property
    def schema(self):
        return self._schema

    @schema.setter
    def schema(self, value):
        if isinstance(value, oamap.schema.Schema):
            self._schema = value
        else:
            raise TypeError("schema must be a Schema")
        self._generator = self._schema.generator(extension=self._extension)

    @property
    def namespace(self):
        return dict(self._namespace)

    @namespace.setter
    def namespace(self, value):
        if isinstance(value, Namespace):
            value = {"": value}
        if not isinstance(value, dict) or not all(isinstance(n, basestring) and isinstance(x, Namespace) for n, x in value.items()) or len(value) == 0:
            raise TypeError("namespace must be a non-empty dict from strings to Namespaces")

        numpartitions = None
        out = {}
        for n, x in value.items():
            if numpartitions is None:
                numpartitions = x.numpartitions
            elif numpartitions != x.numpartitions:
                raise ValueError("one namespace has {0} partitions, another has {1}".format(numpartitions, x.numpartitions))
            out[n] = x

        self._namespace = out

    offsetsdtype = numpy.dtype(numpy.int64)

    @property
    def offsets(self):
        return self._offsets

    @offsets.setter
    def offsets(self, value):
        if value is None:
            self._offsets = None
        else:
            if not isinstance(value, numpy.ndarray):
                value = numpy.array(value, dtype=self.offsetsdtype)
            if value.dtype != self.offsetsdtype:
                raise ValueError("offsets array must have {0}".format(repr(self.offsetsdtype)))
            if len(value.shape) != 1:
                raise ValueError("offsets array must be one-dimensional")
            if len(value) < 2:
                raise ValueError("offsets array must have at least 2 items")
            if value[0] != 0:
                raise ValueError("offsets array must begin with 0")
            if not numpy.all(value[:-1] <= value[1:])
                raise ValueError("offsets array must be monotonically increasing")
            self._offsets = value

    @property
    def extension(self):
        return self._extension

    @extension.setter
    def extension(self, value):
        if value is None:
            self._extension = None
        elif isinstance(value, basestring):
            self._extension = value
        else:
            try:
                modules = []
                for x in value:
                    if not isinstance(x, basestring):
                        raise TypeError
                    modules.append(x)
            except TypeError:
                raise ValueError("extension must be None, a string, or a list of strings, not {0}".format(repr(value)))
            else:
                self._extension = modules
        self._generator = self._schema.generator(extension=self._extension)

    @property
    def doc(self):
        return self._doc

    @doc.setter
    def doc(self, value):
        if not (value is None or isinstance(value, basestring)):
            raise TypeError("doc must be None or a string, not {0}".format(repr(value)))
        self._doc = value

    @property
    def metadata(self):
        return self._metadata

    @metadata.setter
    def metadata(self, value):
        self._metadata = value

    @property
    def numpartitions(self):
        for x in self._namespace.values():
            break
        return x.numpartitions

    @property
    def numentries(self):
        if not isinstance(self._schema, oamap.schema.List):
            raise TypeError("only Lists have a numentries")
        if self._offsets is not None:
            return self._offsets[-1]
        else:
            return sum(len(self.partition(i)) for i in self.numpartitions)

    class _Arrays(object):
        def __init__(self, namespace):
            self.backend = dict((n, x.backend) for n, x in namespace.items())
            self.partitionargs = dict((n, x.partitionargs) for n, x in namespace.items())
            self.arrays = dict((n, None) for n in namespace)

        def getall(self, roles):
            out = {}
            for n in self.arrays:
                filtered = [x for x in roles if x.namespace == n]
                if len(filtered) > 0:
                    if self.arrays[n] is None:
                        self.arrays[n] = self.backend[n](*self.partitionargs[n])
                    out.update(self.arrays[n].getall(filtered))
            return out

        def close(self):
            for n in self.arrays:
                if hasattr(self.arrays[n], "close"):
                    self.arrays[n].close()
                self.arrays[n] = None

    def _arrays(self, id):
        return self._Arrays(self._namespace)

    def __call__(self, id=None):
        if not isinstance(self._schema, oamap.schema.List) and self.numpartitions != 1:
            raise TypeError("only Lists can have numpartitions != 1")

        if id is not None:
            normid = id if id >= 0 else id + self.numpartitions
            if 0 <= normid < self.numpartitions:
                return self._generator(self._arrays(id))
            else:
                raise IndexError("partition id {0} out of range for {1} partitions".format(id, self.numpartitions))

        elif self.numpartitions == 1:
            return self(0)

        else:
            listofarrays = [self._arrays(id) for id in range(self.numpartitions)]
            if self._offsets is None:
                return oamap.proxy.PartitionedListProxy(self._generator, listofarrays)
            else:
                if self.numpartitions + 1 != len(self._offsets):
                    raise ValueError("offsets array must have a length one greater than numpartitions")
                return oamap.proxy.IndexedPartitionedListProxy(self._generator, listofarrays, self._offsets)

################################################################ Database

class Database(object):
    class Datasets(object):
        def __init__(self, database):
            self._database = database
        def __getattr__(self, name):
            return self._database.getdataset(name)
        def __setattr__(self, name, value):
            self._database.setdataset(name, value)
            
    def __init__(self, connection):
        self._connection = connection

    @property
    def connection(self):
        return self._connection

    def getdataset(self, name):
        raise NotImplementedError

    def setdataset(self, name, value):
        raise NotImplementedError

class InMemoryDatabase(Database):
    def __init__(self, **datasets):
        self._datasets = datasets
        super(InMemoryDatabase, self).__init__(None)

    def getdataset(self, name):
        return self._datasets[name]

    def setdataset(self, name, value):
        self._datasets[name] = value
