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
    def __init__(self, connection, backends={}, namespace=""):
        self._connection = connection
        self._backends = dict(backends)
        self._namespace = namespace

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

    def __getitem__(self, namespace):
        return self._backends[namespace]

    def __setitem__(self, namespace, value):
        if not isinstance(value, Backend):
            raise TypeError("can only assign Backends to Database")
        self._backends[namespace] = value

    def __delitem__(self, namespace):
        del self._backends[namespace]

    def list(self):
        return NotImplementedError("missing implementation for {0}.list".format(self.__class__))

    def get(self, dataset):
        return NotImplementedError("missing implementation for {0}.get".format(self.__class__))

    def _normalize_namespace(self, namespace):
        if namespace is None:
            namespace = self._namespace
        if namespace not in self._backends:
            raise ValueError("no backend associated with namespace {0}".format(repr(namespace)))
        return namespace

    def put(self, dataset, value, namespace=None):
        return NotImplementedError("missing implementation for {0}.put".format(self.__class__))

    def delete(self, dataset, namespace=None):
        return NotImplementedError("missing implementation for {0}.delete".format(self.__class__))

class InMemoryDatabase(Database):
    def __init__(self, backends={}, namespace="", datasets={}, refcounts={}):
        super(InMemoryDatabase, self).__init__(None, backends, namespace)
        self._datasets = dict(datasets)
        self._refcounts = dict(refcounts)

    def list(self):
        return list(self._datasets)

    def get(self, dataset):
        ds = self._datasets.get(dataset, None)
        if ds is None:
            raise KeyError("no dataset named {0}".format(repr(dataset)))

        schema = oamap.schema.Schema.fromjson(ds["schema"])
        packing = oamap.schema.Schema._packingfromjson(ds.get("packing", None))

        if isinstance(schema, oamap.schema.List):
            return oamap.dataset.Dataset(dataset,
                                         schema,
                                         dict(self._backends),
                                         ds.get("offsets", None),
                                         packing=packing,
                                         extension=ds.get("extension", None),
                                         doc=ds.get("doc", None),
                                         metadata=ds.get("metadata", None),
                                         prefix=ds.get("prefix", "object"),
                                         delimiter=ds.get("delimiter", "-"))
        else:
            return oamap.dataset.Data(dataset,
                                      schema,
                                      dict(self._backends),
                                      packing=packing,
                                      extension=ds.get("extension", None),
                                      doc=ds.get("doc", None),
                                      metadata=ds.get("metadata", None),
                                      prefix=ds.get("prefix", "object"),
                                      delimiter=ds.get("delimiter", "-"))

    def put(self, dataset, value, namespace=None):
        namespace = self._normalize_namespace(namespace)
        if not isinstance(value, oamap.dataset.Dataset):
            raise TypeError("can only put Datasets in Database")
        if namespace not in self._refcounts:
            self._refcounts[namespace] = {}
        self._datasets[dataset] = value.apply(namespace, self._backends[namespace], self._refcounts[namespace])

    def delete(self, dataset, namespace=None):
        ds = self._datasets.get(dataset, None)
        if ds is None:
            raise KeyError("no dataset named {0}".format(repr(dataset)))

        namespace = self._normalize_namespace(namespace)        
        refcounts = self._refcounts.get(namespace, {})

        def transform(schema):
            refcounts[schema.namespace] = max(refcounts.get(schema.namespace, 0) - 1, 0)
            return schema
        ds.schema.replace(transform)
        
        del self._datasets[dataset]
