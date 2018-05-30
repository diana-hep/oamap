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

import collections
import glob
import json
import os
import re
import shutil
import sys
import time

import oamap.dataset
import oamap.extension.common
import oamap.operations
import oamap.proxy
import oamap.schema
import oamap.util

if sys.version_info[0] > 2:
    basestring = str
    unicode = str

################################################################ Backend, WritableBackend, FilesystemBackend (abstract)

class Backend(object):
    def __repr__(self):
        return "{0}({1})".format(self.__class__.__name__, ", ".join(repr(x) for x in self.args))

    def instantiate(self, partitionid):
        raise NotImplementedError("missing implementation for {0}.instantiate".format(self.__class__))

    def prefix(self, dataset):
        return dataset

    def delimiter(self):
        return "-"

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.args == other.args

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.__class__, self.args))

    @staticmethod
    def fromjson(obj, namespace):
        assert isinstance(obj, dict)
        assert "class" in obj
        mod = obj["class"][:obj["class"].rindex(".")]
        cls = obj["class"][obj["class"].rindex(".") + 1:]
        return getattr(oamap.util.import_module(mod), cls).fromjson(obj, namespace)

class WritableBackend(Backend):
    def incref(self, dataset, partitionid, arrayname):
        raise NotImplementedError("missing implementation for {0}.incref".format(self.__class__))

    def decref(self, dataset, partitionid, arrayname):
        raise NotImplementedError("missing implementation for {0}.decref".format(self.__class__))

class FilesystemBackend(WritableBackend):
    def __init__(self, directory, arrayprefix="obj", arraysuffix=""):
        if not os.path.exists(directory):
            os.mkdir(directory)
        if not os.path.exists(os.path.join(directory, "data")):
            os.mkdir(os.path.join(directory, "data"))
        self._directory = directory
        self._arrayprefix = arrayprefix
        self._arraysuffix = arraysuffix

    @property
    def args(self):
        return (self._directory, self._arrayprefix, self._arraysuffix)

    def tojson(self):
        return {"class": self.__class__.__module__ + "." + self.__class__.__name__,
                "directory": self._directory,
                "arrayprefix": self._arrayprefix,
                "arraysuffix": self._arraysuffix}

    @staticmethod
    def fromjson(obj, namespace):
        return FilesystemBackend(obj["directory"], obj["arrayprefix"], obj["arraysuffix"])

    @property
    def directory(self):
        return self._directory

    @property
    def arrayprefix(self):
        return self._arrayprefix

    @property
    def arraysuffix(self):
        return self._arraysuffix

    def prefix(self, dataset):
        return os.path.join(dataset, "PART", self._arrayprefix)

    def incref(self, dataset, partitionid, arrayname):
        otherdataset_part, array = os.path.split(arrayname)
        otherdataset, part = os.path.split(otherdataset_part)
        if otherdataset != dataset:
            src = os.path.join(self._directory, "data", otherdataset, str(partitionid), array) + self._arraysuffix
            dst = os.path.join(self._directory, "data", dataset, str(partitionid), array) + self._arraysuffix
            if not os.path.exists(dst):
                os.link(src, dst)

    def decref(self, dataset, partitionid, arrayname):
        otherdataset_part, array = os.path.split(arrayname)
        path = os.path.join(self._directory, "data", dataset, str(partitionid), array) + self._arraysuffix
        os.unlink(path)
        try:
            os.rmdir(os.path.join(self._directory, "data", dataset, str(partitionid)))
        except OSError:
            pass
        else:
            try:
                os.rmdir(os.path.join(self._directory, "data", dataset))
            except OSError:
                pass

    def fullname(self, partitionid, arrayname, create=False):
        dataset_part, array = os.path.split(arrayname)
        dataset, part = os.path.split(dataset_part)
        if create:
            if not os.path.exists(os.path.join(self._directory, "data", dataset)):
                os.mkdir(os.path.join(self._directory, "data", dataset))
            if not os.path.exists(os.path.join(self._directory, "data", dataset, str(partitionid))):
                os.mkdir(os.path.join(self._directory, "data", dataset, str(partitionid)))
        return os.path.join(self._directory, "data", dataset, str(partitionid), array) + self._arraysuffix

################################################################ DictBackend (concrete)

class DictBackend(WritableBackend):
    def __init__(self, arrays=None, refcounts=None):
        if arrays is None:
            arrays = {}
        if refcounts is None:
            refcounts = {}
        self._arrays = arrays
        self._refcounts = refcounts

    @property
    def args(self):
        return (self._arrays, self._refcounts)

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

################################################################ Database (abstract)

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

    @classmethod
    def writable(cls, backend, namespace="", *args, **kwargs):
        out = cls(*args, **kwargs)
        out[namespace] = backend
        return out

    def __init__(self, connection, backends={}, namespace="", executor=oamap.dataset.SingleThreadExecutor()):
        self._connection = connection
        if isinstance(backends, Backend):
            backends = {namespace: backends}
        self._backends = {}
        for n, x in backends.items():
            self[n] = x
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
    def get(self, dataset, timeout=None):
        return NotImplementedError("missing implementation for {0}.get".format(self.__class__))
    def put(self, dataset, value, namespace=None):
        return NotImplementedError("missing implementation for {0}.put".format(self.__class__))
    def delete(self, dataset):
        return NotImplementedError("missing implementation for {0}.delete".format(self.__class__))

    def _proxy2data(self, name, result, namespace):
        namespace = self._normalize_namespace(namespace)
        backend = self._backends[namespace]

        backends = getattr(result._arrays, "backends", {})
        schema = result._generator.namedschema()

        schema, roles2arrays = oamap.operations._DualSource.collect(schema, result._arrays, namespace, backend.prefix(name), backend.delimiter())

        active = backend.instantiate(0)
        if hasattr(active, "putall"):
            active.putall(roles2arrays)
        else:
            for n, x in roles2arrays.items():
                active[str(n)] = x

        if isinstance(result, oamap.proxy.ListProxy):
            return oamap.dataset.Dataset(name, schema, backends, self._executor, [0, len(result)])
        else:
            return oamap.dataset.Data(name, schema, backends, self._executor)
        
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
                                         metadata=obj.get("metadata", None))
        else:
            return oamap.dataset.Data(name,
                                      schema,
                                      dict(self._backends),
                                      self._executor,
                                      packing=packing,
                                      extension=obj.get("extension", None),
                                      doc=obj.get("doc", None),
                                      metadata=obj.get("metadata", None))

    @staticmethod
    def _dataset2json(data):
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
        return obj

    def fromdata(self, name, schema, *partitions, **opts):
        try:
            pointer_fromequal = opts.pop("pointer_fromequal", False)
        except KeyError:
            pass
        try:
            namespace = opts.pop("namespace", self._namespace)
        except KeyError:
            pass
        try:
            extension = opts.pop("extension", None)
        except KeyError:
            pass
        try:
            packing = opts.pop("packing", None)
        except KeyError:
            pass
        try:
            doc = opts.pop("doc", None)
        except KeyError:
            pass
        try:
            metadata = opts.pop("metadata", None)
        except KeyError:
            pass
        if len(opts) > 0:
            raise TypeError("unrecognized options: {0}".format(" ".join(opts)))

        if namespace not in self._backends:
            self[namespace] = DictBackend()
        backend = self[namespace]

        def setnamespace(node):
            node.namespace = namespace
            return node
        schema = schema.replace(setnamespace)

        generator = schema.generator(prefix=backend.prefix(name), delimiter=backend.delimiter(), packing=packing)
        generator._requireall()
        roles = generator._togetall({}, generator._newcache(), True, set())

        if isinstance(schema, (oamap.schema.Record, oamap.schema.Tuple)):
            if len(partitions) != 1:
                raise TypeError("only lists can have more or less than one partition")
            data = generator.fromdata(partitions[0])
            roles2arrays = dict((x, data._arrays[str(x)]) for x in roles)

            active = backend.instantiate(0)
            if hasattr(active, "putall"):
                active.putall(roles2arrays)
            else:
                for n, x in roles2arrays.items():
                    active[str(n)] = x

            out = oamap.dataset.Data(name, generator.namedschema(), self._backends, self._executor, extension=extension, packing=packing, doc=doc, metadata=metadata)

        elif isinstance(schema, oamap.schema.List):
            offsets = [0]
            for partitionid, partition in enumerate(partitions):
                data = generator.fromdata(partition)
                roles2arrays = dict((x, data._arrays[str(x)]) for x in roles)
                startsrole = oamap.generator.StartsRole(generator.starts, generator.namespace, None)
                stopsrole = oamap.generator.StopsRole(generator.stops, generator.namespace, None)
                startsrole.stops = stopsrole
                stopsrole.starts = startsrole
                if schema.nullable:
                    maskrole = oamap.generator.MaskRole(generator.mask, generator.namespace, {startsrole: roles2arrays[startsrole], stopsrole: roles2arrays[stopsrole]})
                del roles2arrays[startsrole]
                del roles2arrays[stopsrole]
                if schema.nullable:
                    del roles2arrays[maskrole]

                active = backend.instantiate(partitionid)
                if hasattr(active, "putall"):
                    active.putall(roles2arrays)
                else:
                    for n, x in roles2arrays.items():
                        active[str(n)] = x

                offsets.append(offsets[-1] + len(data))

            out = oamap.dataset.Dataset(name, generator.namedschema(), self._backends, self._executor, offsets, extension=extension, packing=packing, doc=doc, metadata=metadata)

        else:
            raise TypeError("can only create datasets from proxy types (list, records, tuples)")

        self.put(name, out, namespace=namespace)

################################################################ InMemoryDatabase (concrete)

class InMemoryDatabase(Database):
    def __init__(self, backends={}, namespace="", datasets={}):
        super(InMemoryDatabase, self).__init__(None, backends, namespace)

        if isinstance(datasets, oamap.dataset.Data):
            datasets = {datasets.name: datasets}

        self._datasets = {}
        for n, x in datasets.items():
            self.put(n, x)

    def list(self):
        return list(self._datasets)

    def get(self, dataset, timeout=None):
        ds = self._datasets.get(dataset, None)
        if ds is None:
            raise KeyError("no dataset named {0}".format(repr(dataset)))

        elif isinstance(ds, list):
            oldds = ds[0]
            task = ds[-1]

            ds = task.result()
            self._datasets[dataset] = self._dataset2json(ds)
            self._incref(ds)
            if oldds is not None:
                self._decref(oldds)
            return ds

        else:
            return self._json2dataset(dataset, ds)

    def put(self, dataset, value, namespace=None):
        if isinstance(value, oamap.proxy.Proxy):
            value = self._proxy2data(dataset, value, namespace)
        if not isinstance(value, oamap.dataset._Data):
            raise TypeError("can only put Datasets in Database")
        if not value._notransformations():
            namespace = self._normalize_namespace(namespace)
            if namespace not in self._backends or not isinstance(self._backends[namespace], WritableBackend):
                raise ValueError("namespace {0} does not point to a WritableBackend".format(repr(namespace)))
            value._backends[namespace] = self._backends[namespace]

        if dataset in self._datasets:
            ds = self.get(dataset)
        else:
            ds = None

        for ns, backend in value._backends.items():
            if ns not in self._backends:
                self[ns] = backend

        self._datasets[dataset] = [ds] + value.transform(dataset, namespace, lambda data: data)

    def delete(self, dataset):
        ds = self.get(dataset)
        self._decref(ds)
        del self._datasets[dataset]

    def _incref(self, ds):
        if isinstance(ds, oamap.dataset.Dataset):
            partitions = range(ds.numpartitions)
            startingpoint = ds.schema.generator().namedschema().content
        else:
            partitions = [0]
            startingpoint = ds.schema.generator().namedschema()

        for node in startingpoint.nodes():
            if node.namespace in self._backends and isinstance(self._backends[node.namespace], WritableBackend):
                backend = self._backends[node.namespace]
                if isinstance(node, oamap.schema.Primitive):
                    for partitionid in partitions:
                        backend.incref(ds.name, partitionid, node.data)
                elif isinstance(node, oamap.schema.List):
                    for partitionid in partitions:
                        backend.incref(ds.name, partitionid, node.starts)
                        backend.incref(ds.name, partitionid, node.stops)
                elif isinstance(node, oamap.schema.Union):
                    for partitionid in partitions:
                        backend.incref(ds.name, partitionid, node.tags)
                        backend.incref(ds.name, partitionid, node.offsets)
                elif isinstance(node, oamap.schema.Pointer):
                    for partitionid in partitions:
                        backend.incref(ds.name, partitionid, node.positions)
                if node.nullable:
                    for partitionid in partitions:
                        backend.incref(ds.name, partitionid, node.mask)

    def _decref(self, ds):
        if isinstance(ds, oamap.dataset.Dataset):
            partitions = range(ds.numpartitions)
            startingpoint = ds.schema.generator().namedschema().content
        else:
            partitions = [0]
            startingpoint = ds.schema.generator().namedschema()

        for node in startingpoint.nodes():
            if node.namespace in self._backends and isinstance(self._backends[node.namespace], WritableBackend):
                backend = self._backends[node.namespace]
                if isinstance(node, oamap.schema.Primitive):
                    for partitionid in partitions:
                        backend.decref(ds.name, partitionid, node.data)
                elif isinstance(node, oamap.schema.List):
                    for partitionid in partitions:
                        backend.decref(ds.name, partitionid, node.starts)
                        backend.decref(ds.name, partitionid, node.stops)
                elif isinstance(node, oamap.schema.Union):
                    for partitionid in partitions:
                        backend.decref(ds.name, partitionid, node.tags)
                        backend.decref(ds.name, partitionid, node.offsets)
                elif isinstance(node, oamap.schema.Pointer):
                    for partitionid in partitions:
                        backend.decref(ds.name, partitionid, node.positions)
                if node.nullable:
                    for partitionid in partitions:
                        backend.decref(ds.name, partitionid, node.mask)

################################################################ FilesystemDatabase (concrete)

class FilesystemDatabase(Database):
    class BackendDict(collections.MutableMapping):
        def __init__(self, backenddir):
            self._backenddir = backenddir

        @staticmethod
        def _mangle(name):
            return "_" + FilesystemDatabase.BackendDict._manglepattern.sub(lambda bad: "_" + "".join("{0:02x}".format(ord(x)) for x in bad.group(0)) + "_", name) + ".json"
        _manglepattern = re.compile("[^a-zA-Z0-9]+")

        @staticmethod
        def _demangle(name):
            return FilesystemDatabase.BackendDict._demanglepattern.sub(lambda bad: "".join(chr(int(x + y, 16)) for x, y in zip(bad.group(1)[::2], bad.group(1)[1::2])), name[1:-5])
        _demanglepattern = re.compile("_([a-f0-9]+)_")
            
        def __iter__(self):
            for x in os.listdir(self._backenddir):
                if x.startswith("_"):
                    yield self._demangle(x)

        def __len__(self):
            return sum(1 for x in self)

        def __contains__(self, namespace):
            return os.path.exists(os.path.join(self._backenddir, self._mangle(namespace)))

        def __getitem__(self, namespace):
            with open(os.path.join(self._backenddir, self._mangle(namespace))) as f:
                return Backend.fromjson(json.load(f), namespace)

        def __setitem__(self, namespace, value):
            if not isinstance(value, Backend):
                raise TypeError("can only assign Backends to Database")
            with open(os.path.join(self._backenddir, self._mangle(namespace)), "w") as f:
                return json.dump(value.tojson(), f)

        def __delitem__(self, namespace):
            os.unlink(os.path.join(self._backenddir, self._mangle(namespace)))

    def __init__(self, directory, backends={}, namespace=""):
        super(FilesystemDatabase, self).__init__(None, {}, namespace)
        self._directory = directory
        self._backends = FilesystemDatabase.BackendDict(self._backenddir())
        for n, x in backends.items():
            self._backends[n] = x

    def _datadir(self):
        name = os.path.join(self._directory, "data")
        if not os.path.exists(name):
            os.mkdir(name)
        return name

    def _datasetdir(self, dataset):
        name = os.path.join(self._datadir(), dataset)
        if not os.path.exists(name):
            os.mkdir(name)
        return name

    def _backenddir(self):
        name = os.path.join(self._directory, "backends")
        if not os.path.exists(name):
            os.mkdir(name)
        return name

    def list(self):
        out = []
        for x in glob.glob(os.path.join(self._datadir(), "*", "dataset.json")):
            directory_dataset, _ = os.path.split(x)
            _, dataset = os.path.split(directory_dataset)
            out.append(dataset)
        return out

    def get(self, dataset, timeout=None):
        dsjson = os.path.join(self._datasetdir(dataset), "dataset.json")
        while not os.path.exists(dsjson):
            time.sleep(0)
        with open(dsjson) as ds:
            return self._json2dataset(dataset, json.load(ds))

    def put(self, dataset, value, namespace=None):
        if isinstance(value, oamap.proxy.Proxy):
            value = self._proxy2data(dataset, value, namespace)
        if not isinstance(value, oamap.dataset._Data):
            raise TypeError("can only put Datasets in Database")
        if not value._notransformations():
            namespace = self._normalize_namespace(namespace)
            if namespace not in self._backends or not isinstance(self._backends[namespace], FilesystemBackend):
                raise ValueError("namespace {0} does not point to a FilesystemBackend".format(repr(namespace)))
            value._backends[namespace] = self._backends[namespace]

        dsjson = os.path.join(self._datasetdir(dataset), "dataset.json")
        if os.path.exists(dsjson):
            os.unlink(dsjson)

        for ns, backend in value._backends.items():
            if ns not in self._backends:
                self[ns] = backend

        def update(data):
            with open(dsjson, "w") as ds:
                json.dump(Database._dataset2json(data), ds)
                return data

        value.transform(dataset, namespace, update)

    def delete(self, dataset):
        try:
            shutil.rmtree(self._datasetdir(dataset))
        except OSError as err:
            raise KeyError(str(err))
