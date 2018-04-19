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
import oamap.extension.common

if sys.version_info[0] > 2:
    basestring = str
    unicode = str

class Backend(object):
    def __init__(self, *args):
        self._args = args

    @property
    def args(self):
        return self._args

    def instantiate(self, partitionid):
        raise NotImplementedError("missing implementation for {0}.instantiate".format(self.__class__))

class WritableBackend(Backend):
    def incref(self, dataset, partitionid, arrayname):
        raise NotImplementedError("missing implementation for {0}.incref".format(self.__class__))

    def decref(self, dataset, partitionid, arrayname):
        raise NotImplementedError("missing implementation for {0}.decref".format(self.__class__))

class DictBackend(WritableBackend):
    def __init__(self, arrays=None, refcounts=None):
        if arrays is None:
            arrays = {}
        if refcounts is None:
            refcounts = {}
        self._arrays = arrays
        self._refcounts = refcounts
        super(DictBackend, self).__init__(arrays, refcounts)

    def instantiate(self, partitionid):
        out = self._arrays[partitionid] = self._arrays.get(partitionid, {})
        return out

    def incref(self, dataset, partitionid, arrayname):
        out = self._refcounts[partitionid] = self._refcounts.get(partitionid, {})
        out[arrayname] = out.get(arrayname, 0) + 1

    def decref(self, dataset, partitionid, arrayname):
        out = self._refcounts[partitionid]
        out[arrayname] -= 1
        if out[arrayname] <= 0:
            del out[arrayname]
            try:
                del self._arrays[partitionid][arrayname]
            except KeyError:
                pass

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
        if data._delimiter != "-":
            obj["delimiter"] = data._delimiter
        return obj

class InMemoryDatabase(Database):
    @staticmethod
    def fromdata(name, schema, *partitions, **opts):
        try:
            pointer_fromequal = opts.pop("pointer_fromequal", False)
        except KeyError:
            pass
        try:
            namespace = opts.pop("namespace", "")
        except KeyError:
            pass
        try:
            delimiter = opts.pop("delimiter", "-")
        except KeyError:
            pass
        try:
            extension = opts.pop("extension", oamap.extension.common)
        except KeyError:
            pass
        try:
            packing = opts.pop("packing", None)
        except KeyError:
            pass
        if len(opts) > 0:
            raise TypeError("unrecognized options: {0}".format(" ".join(opts)))

        generator = schema.generator(prefix=name, delimiter=delimiter, extension=extension, packing=packing)

        if isinstance(schema, (oamap.schema.Record, oamap.schema.Tuple)):
            if len(partitions) != 1:
                raise TypeError("only lists can have more or less than one partition")
            arrays = {None: generator.fromdata(partitions[0])._arrays}
            refcounts = {None: dict((n, 1) for n in arrays)}
            return InMemoryDatabase(
                backends={namespace: DictBackend(arrays=arrays, refcounts=refcounts)},
                namespace=namespace,
                datasets={name: {"schema": schema.tojson()}})

        elif isinstance(schema, oamap.schema.List):
            arrays = {}
            refcounts = {}
            offsets = [0]
            for i, x in enumerate(partitions):
                arrays[i] = generator.fromdata(x)._arrays
                refcounts[i] = dict((n, 1) for n in arrays[i])
                offsets.append(offsets[-1] + len(x))
            return InMemoryDatabase(
                backends={namespace: DictBackend(arrays=arrays, refcounts=refcounts)},
                namespace=namespace,
                datasets={name: {"schema": schema.tojson(), "offsets": offsets}})

        else:
            raise TypeError("can only create datasets from proxy types (list, records, tuples)")

    def __init__(self, backends={}, namespace="", datasets={}):
        super(InMemoryDatabase, self).__init__(None, backends, namespace)
        self._datasets = dict(datasets)

    def list(self):
        return list(self._datasets)

    def get(self, dataset):
        ds = self._datasets.get(dataset, None)

        if ds is None:
            raise KeyError("no dataset named {0}".format(repr(dataset)))

        elif isinstance(ds, list):
            task = ds[-1]
            if task.done():
                ds = task.result()
                self._datasets[dataset] = self._dataset2json(ds)
                self._incref(ds)
                return ds
            else:
                raise NotImplementedError("FIXME: deal with failed and incomplete tasks")

        else:
            return self._json2dataset(dataset, ds)

    def put(self, dataset, value, namespace=None):
        namespace = self._normalize_namespace(namespace)
        if namespace not in self._backends or not isinstance(self._backends[namespace], WritableBackend):
            raise ValueError("namespace {0} does not point to a writable backend".format(repr(namespace)))
        if not isinstance(value, oamap.dataset._Data):
            raise TypeError("can only put Datasets in Database")

        self._datasets[dataset] = value.transform(dataset, namespace, self._backends[namespace], lambda data: data)
        
    def delete(self, dataset):
        ds = self.get(dataset)
        self._decref(ds)
        del self._datasets[dataset]

    def _incref(self, ds):
        if isinstance(ds, oamap.dataset.Dataset):
            partitions = range(ds.numpartitions)
            startingpoint = ds.schema.generator().namedschema().content
        else:
            partitions = [None]
            startingpoint = ds.schema.generator().namedschema()

        def transform(schema):
            if schema.namespace in self._backends and isinstance(self._backends[schema.namespace], WritableBackend):
                backend = self._backends[schema.namespace]
                if isinstance(schema, oamap.schema.Primitive):
                    for partitionid in partitions:
                        backend.incref(ds.name, partitionid, schema.data)
                elif isinstance(schema, oamap.schema.List):
                    for partitionid in partitions:
                        backend.incref(ds.name, partitionid, schema.starts)
                        backend.incref(ds.name, partitionid, schema.stops)
                elif isinstance(schema, oamap.schema.Union):
                    for partitionid in partitions:
                        backend.incref(ds.name, partitionid, schema.tags)
                        backend.incref(ds.name, partitionid, schema.offsets)
                elif isinstance(schema, oamap.schema.Pointer):
                    for partitionid in partitions:
                        backend.incref(ds.name, partitionid, schema.positions)
                if schema.nullable:
                    for partitionid in partitions:
                        backend.incref(ds.name, partitionid, schema.mask)
                return schema
        startingpoint.replace(transform)

    def _decref(self, ds):
        if isinstance(ds, oamap.dataset.Dataset):
            partitions = range(ds.numpartitions)
            startingpoint = ds.schema.generator().namedschema().content
        else:
            partitions = [None]
            startingpoint = ds.schema.generator().namedschema()

        def transform(schema):
            if schema.namespace in self._backends and isinstance(self._backends[schema.namespace], WritableBackend):
                backend = self._backends[schema.namespace]
                if isinstance(schema, oamap.schema.Primitive):
                    for partitionid in partitions:
                        backend.decref(ds.name, partitionid, schema.data)
                elif isinstance(schema, oamap.schema.List):
                    for partitionid in partitions:
                        backend.decref(ds.name, partitionid, schema.starts)
                        backend.decref(ds.name, partitionid, schema.stops)
                elif isinstance(schema, oamap.schema.Union):
                    for partitionid in partitions:
                        backend.decref(ds.name, partitionid, schema.tags)
                        backend.decref(ds.name, partitionid, schema.offsets)
                elif isinstance(schema, oamap.schema.Pointer):
                    for partitionid in partitions:
                        backend.decref(ds.name, partitionid, schema.positions)
                if schema.nullable:
                    for partitionid in partitions:
                        backend.decref(ds.name, partitionid, schema.mask)
                return schema
        startingpoint.replace(transform)
