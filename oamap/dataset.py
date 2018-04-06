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
import collections

import numpy

import oamap.schema
import oamap.generator
import oamap.proxy
import oamap.extension.common

if sys.version_info[0] > 2:
    basestring = str
    unicode = str

################################################################ Namespace

class Namespace(object):
    def __init__(self, backend, args, partargs):
        self.backend = backend
        self.args = args
        self.partargs = partargs

    def __repr__(self):
        p = " {0} partition".format(self.numpartitions)
        if self.numpartitions != 1:
            p = p + "s"
        return "<Namespace of {0}({1}, ...){2}>".format(self._backend.__name__, ", ".join(repr(x) for x in self.args), p)

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
    def args(self):
        return self._args

    @args.setter
    def args(self, value):
        if not isinstance(value, tuple):
            raise TypeError("args mut be a tuple")
        self._args = value

    @property
    def partargs(self):
        return self._partargs

    @partargs.setter
    def partargs(self, value):
        value = list(value)
        if not all(isinstance(x, tuple) for x in value):
            raise TypeError("partargs must be an iterable of tuples")
        if len(value) == 0:
            raise ValueError("partargs must have at least one partition")
        self._partargs = value
    
    @property
    def numpartitions(self):
        return len(self._partargs)

    def __eq__(self, other):
        return isinstance(other, Namespace) and self.backend == other.backend and self.args == other.args and self.partargs == other.partargs

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((Namespace, self.backend, self.args, tuple(self.partargs)))

################################################################ Dataset

class Dataset(object):
    def __init__(self, name, schema, namespace, offsets=None, extension=None, doc=None, metadata=None):
        self._extension = oamap.extension.common
        self._name = name
        self.schema = schema
        self.namespace = namespace
        self.offsets = offsets
        if extension is not None:
            self.extension = extension
        self.doc = doc
        self.metadata = metadata

    def __repr__(self):
        if self._name is None:
            n = ""
        else:
            n = repr(self._name) + " "
        p = "{0} partition".format(self.numpartitions)
        if self.numpartitions != 1:
            p = p + "s"
        if self._offsets is None:
            e = ""
        else:
            e = " {0} entries".format(self.numentries)
        return "<Dataset {0}{1}{2}>".format(n, p, e)

    @property
    def name(self):
        return self._name

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

    class _DictOfNamespaces(collections.MutableMapping):
        def __init__(self, numpartitions, namespace):
            self._numpartitions = numpartitions
            self._namespace = namespace
        def __getitem__(self, key):
            return self._namespace[key]
        def __setitem__(self, key, value):
            if not isinstance(key, basestring) or not isinstance(value, Namespace):
                raise TypeError("namespace dict keys must be strings and values must be Namespaces")
            if self._numpartitions != value.numpartitions:
                raise ValueError("one namespace has {0} partitions, another has {1}".format(self._numpartitions, value.numpartitions))
            self._namespace[key] = value
        def __delitem__(self, key):
            if len(self._namespace) == 1:
                raise ValueError("namespace dict must not be empty")
            del self._namespace[key]
        def __iter__(self):
            return iter(self._namespace)
        def __len__(self):
            return len(self._namespace)
        def __repr__(self):
            return repr(self._namespace)
        def __str__(self):
            return str(self._namespace)
        
    @property
    def namespace(self):
        return self._DictOfNamespaces(self.numpartitions, self._namespace)

    @namespace.setter
    def namespace(self, value):
        if isinstance(value, Namespace):
            value = {"": value}
        if not isinstance(value, dict) or not all(isinstance(n, basestring) and isinstance(x, Namespace) for n, x in value.items()) or len(value) == 0:
            raise TypeError("namespace must be a non-empty dict from strings to Namespaces")

        numpartitions = None
        for n, x in value.items():
            if numpartitions is None:
                numpartitions = x.numpartitions
            elif numpartitions != x.numpartitions:
                raise ValueError("one namespace has {0} partitions, another has {1}".format(numpartitions, x.numpartitions))
        self._namespace = value

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
            if not numpy.all(value[:-1] <= value[1:]):
                raise ValueError("offsets array must be monotonically increasing")
            self._offsets = value

    @property
    def extension(self):
        return self._extension

    @extension.setter
    def extension(self, value):
        if isinstance(value, basestring):
            self._extension = value
        else:
            try:
                modules = []
                for x in value:
                    if not isinstance(x, basestring):
                        raise TypeError
                    modules.append(x)
            except TypeError:
                raise ValueError("extension must be a string or a list of strings, not {0}".format(repr(value)))
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

    def copy(self, **replacements):
        if "name" not in replacements:
            replacements["name"] = self._name
        if "schema" not in replacements:
            replacements["schema"] = self._schema
        if "namespace" not in replacements:
            replacements["namespace"] = self._namespace
        if "offsets" not in replacements:
            replacements["offsets"] = self._offsets
        if "extension" not in replacements:
            replacements["extension"] = None if self._extension is oamap.extension.common else self._extension
        if "doc" not in replacements:
            replacements["doc"] = self._doc
        if "metadata" not in replacements:
            replacements["metadata"] = self._metadata
        return Dataset(**replacements)

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
            return sum(len(self(i)) for i in range(self.numpartitions))

    class _Arrays(object):
        def __init__(self, partitionid, namespace, startsrole, stopsrole, numentries):
            self.partitionid = partitionid
            self.backend = dict((n, x.backend) for n, x in namespace.items())
            self.args = dict((n, x.args) for n, x in namespace.items())
            self.partargs = dict((n, list(x.partargs)) for n, x in namespace.items())
            self.arrays = dict((n, None) for n in namespace)
            self.startsrole = startsrole
            self.stopsrole = stopsrole
            self.numentries = numentries

        def getall(self, roles):
            out = {}
            for n in self.arrays:
                filtered = [x for x in roles if x.namespace == n]

                if self.numentries is not None:
                    try:
                        startsindex = filtered.index(self.startsrole)
                    except ValueError:
                        pass
                    else:
                        starts = filtered[startsindex]
                        out[starts] = numpy.array([0], dtype=oamap.generator.ListGenerator.posdtype)
                        del filtered[startsindex]
                    try:
                        stopsindex = filtered.index(self.stopsrole)
                    except ValueError:
                        pass
                    else:
                        stops = filtered[stopsindex]
                        out[stops] = numpy.array([self.numentries], dtype=oamap.generator.ListGenerator.posdtype)
                        del filtered[stopsindex]

                if len(filtered) > 0:
                    if self.arrays[n] is None:
                        self.arrays[n] = self.backend[n](*(self.args[n] + self.partargs[n][self.partitionid]))
                    arrays = self.arrays[n]

                    if hasattr(arrays, "getall"):
                        out.update(arrays.getall(filtered))     # pass on the roles to a source that knows about getall
                    else:
                        for x in roles:
                            out[x] = arrays[str(x)]             # drop the roles; it's a plain-dict interface

            return out

        def close(self):
            for n in self.arrays:
                if hasattr(self.arrays[n], "close"):
                    self.arrays[n].close()
                self.arrays[n] = None

    def _arrays(self, partitionid):
        if self._offsets is not None and isinstance(self._schema, oamap.schema.List) and self._schema.starts is None and self._schema.stops is None:
            numentries = self._offsets[partitionid + 1] - self._offsets[partitionid]
            startsrole = oamap.generator.StartsRole("object-B", self._schema.namespace, None)
            stopsrole = oamap.generator.StopsRole("object-E", self._schema.namespace, None)
        else:
            numentries = None
            startsrole = None
            stopsrole = None
        return self._Arrays(partitionid, self._namespace, startsrole, stopsrole, numentries)

    def __call__(self, partitionid=None):
        if not isinstance(self._schema, oamap.schema.List) and self.numpartitions != 1:
            raise TypeError("only Lists can have numpartitions != 1")

        if partitionid is not None:
            normid = partitionid if partitionid >= 0 else partitionid + self.numpartitions
            if 0 <= normid < self.numpartitions:
                return self._generator(self._arrays(normid))
            else:
                raise IndexError("partition id {0} out of range for {1} partitions".format(partitionid, self.numpartitions))

        elif self.numpartitions == 1:
            return self(0)

        else:
            listofarrays = [self._arrays(partitionid) for partitionid in range(self.numpartitions)]
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
            self.__dict__["_database"] = database
        def __repr__(self):
            return "<Datasets: {0}>".format(self._database.list())
        def __getattr__(self, name):
            return self.__dict__["_database"].get(name)
        def __setattr__(self, name, value):
            self.__dict__["_database"].set(name, value)
            
    def __init__(self, connection):
        self._connection = connection
        self._namespace = set()

    @property
    def connection(self):
        return self._connection

    @property
    def namespace(self):
        return frozenset(self._namespace)

    @property
    def datasets(self):
        return self.Datasets(self)

    def list(self):
        raise NotImplementedError

    def get(self, name):
        raise NotImplementedError

    def set(self, name, value):
        raise NotImplementedError

class InMemoryDatabase(Database):
    def __init__(self, **datasets):
        super(InMemoryDatabase, self).__init__(None)
        self._datasets = {}
        for n, x in datasets.items():
            self.set(n, x)

    def list(self):
        return list(self._datasets)

    def get(self, name):
        return self._datasets[name].copy(name=name)

    def set(self, name, value):
        if not isinstance(value, Dataset):
            raise TypeError("datasets must have type Dataset")
        self._namespace.update(value.namespace.values())
        self._datasets[name] = value

################################################################ quick test

# import oamap.backend.numpyfile

# ns1 = Namespace(oamap.backend.numpyfile.NumpyFile, ("/home/pivarski/diana/oamap",), [("part1",), ("part2",)])
# ns2 = Namespace(oamap.backend.numpyfile.NumpyFile, ("/home/pivarski/diana/oamap",), [("part1",), ("part2",)])
# ns3 = Namespace(oamap.backend.numpyfile.NumpyFile, ("/home/pivarski/diana/oamap",), [("part1",), ("part2",)])

# sch = oamap.schema.List(oamap.schema.List(oamap.schema.Primitive(float, data="data.npy", namespace="DATA"), starts="starts.npy", stops="stops.npy"))   # , starts="starts0.npy", stops="stops0.npy"

# test = Dataset(None, sch, {"": ns1, "DATA": ns2}, [0, 3, 6])

# db = InMemoryDatabase(test=test)
