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

import sys

import oamap.schema
import oamap.dataset

if sys.version_info[0] > 2:
    basestring = str
    unicode = str

class Backend(object):
    def __init__(self, args):
        self._args = args

    @property
    def args(self):
        return self._args

    def instantiate(self, partitionid):
        raise NotImplementedError("missing implementation for {0}.implementation".format(self.__class__))

class DictBackend(Backend):
    def instantiate(self, partitionid):
        out = self._args[partitionid] = self._args.get(partitionid, {})
        return out

class Database(object):
    class Data(object):
        def __init__(self, database):
            self.__dict__["_database"] = database
        def __repr__(self):
            return "<Data: {0}>".format(self._database.list())
        def __getattr__(self, name):
            return self.__dict__["_database"].get(name)
        def __setattr__(self, name, value):
            self.__dict__["_database"].put(name, value)
        def __delattr__(self, name):
            self.__dict__["_database"].delete(name)

    def __init__(self, connection, backends={}, namespace="", executor=oamap.dataset.SingleThreadExecutor()):
        self._connection = connection
        self._backends = dict(backends)
        self._namespace = namespace
        self._executor = executor

    @property
    def connection(self):
        return self._connection

    @property
    def backends(self):
        return dict(self._backends)

    @property
    def namespace(self):
        return self._namespace

    @namespace.setter
    def namespace(self, value):
        if not isinstance(value, basestring):
            raise TypeError("namespace must be a string")
        self._namespace = namespace

    # get/set backends as items
    def __getitem__(self, namespace):
        return self._backends[namespace]
    def __setitem__(self, namespace, value):
        if not isinstance(value, Backend):
            raise TypeError("can only assign Backends to Database")
        self._backends[namespace] = value
    def __delitem__(self, namespace):
        del self._backends[namespace]

    # get/set datasets as attributes of .data
    @property
    def data(self):
        return self.Data(self)
    def list(self):
        return NotImplementedError("missing implementation for {0}.list".format(self.__class__))
    def get(self, dataset):
        return NotImplementedError("missing implementation for {0}.get".format(self.__class__))
    def put(self, dataset, value, namespace=None):
        return NotImplementedError("missing implementation for {0}.put".format(self.__class__))
    def delete(self, dataset):
        return NotImplementedError("missing implementation for {0}.delete".format(self.__class__))

    def _normalize_namespace(self, namespace):
        if namespace is None:
            namespace = self._namespace
        if namespace not in self._backends:
            raise ValueError("no backend associated with namespace {0}".format(repr(namespace)))
        return namespace

    def _json2dataset(self, name, obj):
        schema = oamap.schema.Schema.fromjson(obj["schema"])
        packing = oamap.schema.Schema._packingfromjson(obj.get("packing", None))

        if isinstance(schema, oamap.schema.List):
            return oamap.dataset.Dataset(name,
                                         schema,
                                         dict(self._backends),
                                         self._executor,
                                         obj.get("offsets", None),
                                         packing=packing,
                                         extension=obj.get("extension", None),
                                         doc=obj.get("doc", None),
                                         metadata=obj.get("metadata", None),
                                         prefix=obj.get("prefix", "object"),
                                         delimiter=obj.get("delimiter", "-"))
        else:
            return oamap.dataset.Data(name,
                                      schema,
                                      dict(self._backends),
                                      self._executor,
                                      packing=packing,
                                      extension=obj.get("extension", None),
                                      doc=obj.get("doc", None),
                                      metadata=obj.get("metadata", None),
                                      prefix=obj.get("prefix", "object"),
                                      delimiter=obj.get("delimiter", "-"))

    def _dataset2json(self, data):
        obj = {"schema": data._schema.tojson()}
        if isinstance(data._schema, oamap.schema.List):
            obj["offsets"] = data._offsets.tolist()
        if data._packing is not None:
            obj["packing"] = data._packing.tojson()
        if data._extension is not None:
            obj["extension"] = data._extension
        if data._doc is not None:
            obj["doc"] = data._doc
        if data._metadata is not None:
            obj["metadata"] = data._metadata
        if data._prefix != "object":
            obj["prefix"] = data._prefix
        if data._delimiter != "-":
            obj["delimiter"] = data._delimiter
        return obj

class InMemoryDatabase(Database):
    class RefCounts(dict):
        def increment(self, n):
            self[n] = self.get(n, 0) + 1
        def decrement(self, n):
            value = self.get(n, 0) - 1
            if value <= 0 and n in self:
                del self[n]
            else:
                self[n] = value

    def __init__(self, backends={}, namespace="", datasets={}, refcounts={}):
        super(InMemoryDatabase, self).__init__(None, backends, namespace)
        self._datasets = dict(datasets)
        self._refcounts = dict((n, self.RefCounts(x)) for n, x in refcounts.items())

    def list(self):
        return list(self._datasets)

    def get(self, dataset):
        ds = self._datasets.get(dataset, None)

        if ds is None:
            raise KeyError("no dataset named {0}".format(repr(dataset)))

        elif isinstance(ds, list):
            task = ds[-1]
            if task.done():
                out = task.result()
                self._datasets[dataset] = self._dataset2json(out)
                return out
            else:
                raise NotImplementedError("deal with failed and incomplete tasks")

        else:
            return self._json2dataset(dataset, ds)

    def put(self, dataset, value, namespace=None):
        namespace = self._normalize_namespace(namespace)
        if not isinstance(value, oamap.dataset._Data):
            raise TypeError("can only put Datasets in Database")

        refcounts = self._refcounts[namespace] = self._refcounts.get(namespace, self.RefCounts())
        self._datasets[dataset] = value.transform(dataset, namespace, self._backends[namespace], refcounts, lambda name, data: data)
            
    def delete(self, dataset):
        ds = self._datasets.get(dataset, None)
        if ds is None:
            raise KeyError("no dataset named {0}".format(repr(dataset)))

        def transform(schema):
            refcounts = self._refcounts.get(schema.namespace, self.RefCounts())
            if isinstance(schema, oamap.schema.Primitive):
                refcounts.decrement(schema.data)
            elif isinstance(schema, oamap.schema.List):
                refcounts.decrement(schema.starts)
                refcounts.decrement(schema.stops)
            elif isinstance(schema, oamap.schema.Union):
                refcounts.decrement(schema.tags)
                refcounts.decrement(schema.offsets)
            elif isinstance(schema, oamap.schema.Pointer):
                refcounts.decrement(schema.positions)
            else:
                raise AssertionError(schema)
            if schema.nullable:
                refcounts.decrement(schema.mask)
            return schema
        
        ds.schema.replace(transform)
        del self._datasets[dataset]
