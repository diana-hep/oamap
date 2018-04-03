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

if sys.version_info[0] > 2:
    basestring = str
    unicode = str

################################################################ Partitions

class Partitions(object):
    dtype = numpy.dtype(numpy.int64)

    def __init__(self, backend, partitionargs):
        self.backend = backend
        self.partitionargs = partitionargs

    @property
    def numpartitions(self):
        return len(self.partitionargs)

    def __getitem__(self, id):
        normalid = id if id >= 0 else id + self.numpartitions
        if 0 <= normalid < self.numpartitions:
            return self.backend(*self.partitionargs[normalid])
        else:
            raise IndexError("partition id of {0} is out of range for numpartitions {1}".format(id, self.numpartitions))

    def __iter__(self):
        def generate(self):
            for args in self.partitionargs:
                arrays = self.backend(*args)
                yield arrays
                if hasattr(arrays, "close"):
                    arrays.close()
        return generate()

class IndexedPartitions(Partitions):
    def __init__(self, backend, partitionargs, offsets):
        if not isinstance(offsets, numpy.ndarray):
            offsets = numpy.array(offsets, dtype=self.dtype)
        assert offsets.dtype == self.dtype
        assert len(offsets.shape) == 1
        assert numpy.all(offsets[:-1] <= offsets[1:])
        assert len(partitionargs) + 1 == len(offsets)

        self.offsets = offsets
        super(IndexedPartitions, self).__init__(partitionargs)

    @property
    def numentries(self):
        return self.offsets[-1]

    def numentriesof(self, id):
        normalid = id if id >= 0 else id + self.numpartitions
        if 0 <= normalid < self.numpartitions:
            return self.offsets[normalid + 1] - self.offsets[normalid]
        else:
            raise IndexError("partition id of {0} is out of range for numpartitions {1}".format(id, self.numpartitions))

    def partitionid(self, index):
        normalindex = index if index >= 0 else index + self.numentries
        if 0 <= normalindex < self.numentries:
            return numpy.searchsorted(self.offsets, normalindex, side="right") - 1
        else:
            raise IndexError("index of {0} is out of range for numentries {1}".format(index, self.numentries))

################################################################ Namespace

class Namespace(object):
    def __init__(self, backend, partitionargs, offsets=None):
        self.backend = backend
        self.partitionargs = partitionargs
        self.offsets = offsets

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
    def offsets(self):
        return self._offsets

    @offsets.setter
    def offsets(self, value):
        if value is None:
            self._offsets = None
        else:
            try:
                value = list(value)
            except TypeError:
                raise TypeError("offsets must be None or an iterable of integers")
            if not all(isinstance(x, numbers.Integral) for x in value):
                raise TypeError("offsets must all be integers")
            self._offsets = value

    def partitions(self):
        if self._offsets is None:
            return Partitions(self._backend, self._partitionargs)
        else:
            return IndexedPartitions(self._backend, self._partitionargs, self._offsets)

################################################################ Dataset

class Dataset(object):
    def __init__(self, schema, namespaces, extension=None, doc=None, metadata=None):
        self.schema = schema
        self.namespaces = namespaces
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

    @property
    def namespaces(self):
        return self._namespaces

    @namespaces.setter
    def namespaces(self, value):
        if isinstance(value, dict) and all(isinstance(n, basestring) and isinstance(x, Namespace) for n, x in value.items()):
            self._namespaces = value
        else:
            raise TypeError("namespaces must be a dict from strings to Namespaces")

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
    def data(self):
        raise NotImplementedError

    def partition(self, id):
        raise NotImplementedError

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
