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

import numpy

import oamap.schema
import oamap.generator
import oamap.proxy

if sys.version_info[0] < 3:
    range = xrange

################################################################ utilities

def maybecompile(numba):
    if numba is not None and numba is not False:
        if numba is True:
            numbaopts = {}
        else:
            numbaopts = numba
        import numba as nb
        return nb.jit(**numbaopts)
    else:
        return lambda fcn: fcn

class Multisource(object):
    def __init__(self):
        self.namespaces = {}

    def add(self, arrays, generator):
        for n, ns in generator.iternames(namespace=True):
            if ns in self.namespaces and self.namespaces[ns] is not arrays:
                raise ValueError("multiple sources would satisfy namespace {0}".format(repr(ns)))
            self.namespaces[ns] = arrays

    def getall(self, roles):
        if any(x.namespace not in self.namespaces for x in roles):
            raise ValueError("request for namespace not in Multisource")
        out = {}
        for namespace, arrays in self.namespaces.items():
            if hasattr(arrays, "getall"):
                out.update(arrays.getall([x for x in roles if x.namespace == namespace]))
            else:
                out.update(dict((x, arrays[x]) for x in roles if x.namespace == namespace))
        return out

    def close(self):
        for arrays in self.namespaces.values():
            if "close" in arrays:
                arrays.close()

class NewArrays(Multisource):
    @staticmethod
    def get(oldarrays, names):
        if isinstance(oldarrays, NewArrays):
            return oldarrays
        else:
            return NewArrays(oldarrays, names)

    def __init__(self, oldarrays, generator):
        super(NewArrays, self).__init__()
        super(NewArrays, self).add(oldarrays, generator)

        self.schemas = {}
        self.arrays = {}
        self.namespace = "0"
        while self.namespace in self.namespaces:
            self.namespace = str(int(self.namespace) + 1)
        self.namespaces[self.namespace] = self.arrays

    def put(self, schema, attr, value):
        name = str(len(self.arrays))

        self.schemas[name] = schema
        schema.namespace = self.namespace
        setattr(schema, attr, name)

        self.arrays[name] = value

################################################################ project

def project(data, fieldname):
    if isinstance(data, oamap.proxy.ListProxy) and isinstance(data._generator.schema.content, oamap.schema.Record) and fieldname in data._generator.schema.content.fields:
        if data._generator.schema.content.nullable:
            raise NotImplementedError("the inner Record is nullable; need to merge masks")
        schema = data._generator.namedschema()
        schema.content = schema.content.fields[fieldname]
        out = schema(data._arrays)
        out._whence, out._stride, out._length = data._whence, data._stride, data._length
        return out

    elif isinstance(data, oamap.proxy.RecordProxy) and fieldname in data._generator.schema.fields:
        if data._generator.schema.nullable:
            raise NotImplementedError("the Record is nullable; need to merge masks")
        schema = data._generator.fields[fieldname].namedschema()
        return schema(data._arrays)

    else:
        raise TypeError("project can only be applied to List(Record({{{0}: ...}}))".format(repr(fieldname)))

################################################################ attach

def attach(data, fieldname, newfield):
    if not isinstance(data, (oamap.proxy.ListProxy, oamap.proxy.RecordProxy)):
        raise TypeError("attach can only be applied to Record(...) or List(Record(...))")

    if isinstance(newfield, oampa.proxy.Proxy):
        if isinstance(data._arrays, NewArrays):
            





    if isinstance(data, oamap.proxy.RecordProxy):
        schema = data._generator.namedschema()



    elif isinstance(data, oamap.proxy.ListProxy) and isinstance(data._generator.schema.content, oamap.schema.Record):
        raise NotImplementedError

    else:
        raise TypeError("attach can only be applied to Record(...) or List(Record(...))")

################################################################ detach

def detach(data, fieldname):
    if isinstance(data, oamap.proxy.RecordProxy):
        raise NotImplementedError

    elif isinstance(data, oamap.proxy.ListProxy) and isinstance(data._generator.schema.content, oamap.schema.Record):
        raise NotImplementedError

    else:
        raise TypeError("detach can only be applied to Record(...) or List(Record(...))")

################################################################ flatten

def flatten(data):
    if isinstance(data, oamap.proxy.ListProxy) and isinstance(data._generator.schema.content, oamap.schema.List):
        if data._generator.schema.content.nullable:
            raise NotImplementedError("the inner List is nullable; need to merge masks")

        schema = oamap.schema.List(data._generator.namedschema().content.content)

        starts, stops = data._generator.content._getstartsstops(data._arrays, data._cache)
        starts = starts[data._whence : data._whence + data._stride*data._length]
        stops  =  stops[data._whence : data._whence + data._stride*data._length]

        if numpy.array_equal(starts[1:], stops[:-1]):
            # important special case: contiguous
            newarrays = NewArrays.get(data._arrays, data._generator.iternames(namespace=True))
            newarrays.put(schema, "starts", starts[:1])
            newarrays.put(schema, "stops", stops[-1:])
            return schema(newarrays)

        else:
            raise NotImplementedError("non-contiguous arrays: have to do some sort of concatenate")

    else:
        raise TypeError("flatten can only be applied to List(List(...))")

################################################################ filter

def filter(data, fcn, numba=True):
    if isinstance(data, oamap.proxy.ListProxy):
        schema = data._generator.namedschema()
        schema.content = oamap.schema.Pointer(schema.content)

        fcn = maybecompile(numba)(fcn)

        @maybecompile(numba)
        def setpointers(data, pointers):
            j = 0
            for i in range(len(data)):
                if fcn(data[i]):
                    pointers[j] = i
                    j += 1
            return j

        pointers = numpy.empty(len(data), dtype=oamap.generator.PointerGenerator.posdtype)
        numentries = setpointers(data, pointers)

        newarrays = NewArrays.get(data._arrays, data._generator.iternames(namespace=True))
        newarrays.put(schema, "starts", numpy.array([0], dtype=data._generator.posdtype))
        newarrays.put(schema, "stops", numpy.array([numentries], dtype=data._generator.posdtype))
        newarrays.put(schema.content, "positions", pointers[:numentries])

        return schema(newarrays)

    else:
        raise TypeError("filter can only be applied to List(...)")

################################################################ define

################################################################ reduce

# dataset = oamap.schema.List("int").fromdata(range(10))

# from oamap.schema import *
# dataset = List(Record(dict(x=List("int"), y=List("double")))).fromdata([{"x": [1, 2, 3], "y": [1.1, 2.2]}, {"x": [], "y": []}, {"x": [4, 5], "y": [3.3]}])
