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
import numbers

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

class _Multisource(object):
    def __init__(self):
        self.namespaces = {}

    def add(self, arrays, generator):
        for n, ns in generator.iternames(namespace=True):
            if ns in self.namespaces and self.namespaces[ns] is not arrays:
                raise ValueError("multiple sources would satisfy namespace {0}".format(repr(ns)))
            self.namespaces[ns] = arrays

    def getall(self, roles):
        if any(x.namespace not in self.namespaces for x in roles):
            raise KeyError("request for namespace not in Multisource")
        out = {}
        for namespace, arrays in self.namespaces.items():
            if hasattr(arrays, "getall"):
                out.update(arrays.getall([x for x in roles if x.namespace == namespace]))
            else:
                out.update(dict((x, arrays[str(x)]) for x in roles if x.namespace == namespace))
        return out

    def close(self):
        for arrays in self.namespaces.values():
            if "close" in arrays:
                arrays.close()

class _NewArrays(_Multisource):
    @staticmethod
    def instance(arrays, generator):
        if isinstance(arrays, _NewArrays):
            return arrays
        else:
            return _NewArrays(arrays, generator)

    def __init__(self, arrays, generator):
        super(_NewArrays, self).__init__()
        self.add(arrays, generator)

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

    def merge(self, other, generator):
        if not isinstance(other, _NewArrays):
            self.add(other, generator)

        else:
            for n, a in other.namespaces.items():
                if n != other.namespace:
                    self.namespaces[n] = a

            del self.namespaces[self.namespace]
            del other.namespaces[other.namespace]

            while self.namespace in self.namespaces:
                self.namespace = str(int(self.namespace) + 1)
            other.namespace = self.namespace

            self.namespaces[self.namespace] = self.arrays
            other.namespaces[other.namespace] = other.arrays

            for n, s in other.schemas.items():
                if isinstance(s, oamap.schema.Primitive):
                    self.put(s, "data", n)
                elif isinstance(s, oamap.schema.List):
                    self.put(s, "starts", n)
                    self.put(s, "stops", n)
                elif isinstance(s, oamap.schema.Union):
                    self.put(s, "tags", n)
                    self.put(s, "offsets", n)
                elif isinstance(s, oamap.schema.Record):
                    pass
                elif isinstance(s, oamap.schema.Tuple):
                    pass
                elif isinstance(s, oamap.schema.Pointer):
                    self.put(s, "positions", n)
                else:
                    raise AssertionError(s)
                if s.nullable:
                    self.put(s, "mask", n)

################################################################ project

def project(data, fieldname):
    if isinstance(data, oamap.proxy.RecordProxy) and fieldname in data._generator.schema.fields:
        if data._generator.schema.nullable:
            raise NotImplementedError("the Record is nullable; need to merge masks")
        schema = data._generator.fields[fieldname].namedschema()
        out = schema(data._arrays)
        out._index = data._index
        return out

    elif isinstance(data, oamap.proxy.ListProxy) and isinstance(data._generator.schema.content, oamap.schema.Record) and fieldname in data._generator.schema.content.fields:
        if data._generator.schema.content.nullable:
            raise NotImplementedError("the inner Record is nullable; need to merge masks")
        schema = data._generator.namedschema()
        schema.content = schema.content.fields[fieldname]
        out = schema(data._arrays)
        out._whence, out._stride, out._length = data._whence, data._stride, data._length
        return out

    else:
        raise TypeError("project can only be applied to a Record({{{0}: ...}}) or a List(Record({{{0}: ...}}))".format(repr(fieldname)))

################################################################ attach

def attach(data, fieldname, newfield):
    if not isinstance(fieldname, basestring):
        raise TypeError("fieldname must be a string")

    if data._generator.schema.nullable:
        raise NotImplementedError("data is nullable; need to merge masks")

    if isinstance(data, oamap.proxy.RecordProxy) and data._index == 0:
        newarrays = _NewArrays.instance(data._arrays, data._generator)
        if isinstance(newfield, oamap.proxy.Proxy):
            newarrays.merge(data._arrays, data._generator)
            fieldschema = data._generator.namedschema()

        elif isinstance(newfield, numbers.Integral):
            fieldschema = oamap.schema.Primitive(numpy.int64)
            newarrays.put(fieldschema, "data", numpy.array([newfield], dtype=fieldschema.dtype))

        elif isinstance(newfield, numbers.Real):
            fieldschema = oamap.schema.Primitive(numpy.float64)
            newarrays.put(fieldschema, "data", numpy.array([newfield], dtype=fieldschema.dtype))

        else:
            raise TypeError("if data is a Record, newfield must be a Proxy (e.g. List or Record) or a number (e.g. int or float)")

        schema = data._generator.namedschema()
        schema[fieldname] = fieldschema
        return schema(newarrays)

    elif isinstance(data, oamap.proxy.ListProxy) and data._whence == 0 and data._stride == 1 and isinstance(data._generator.schema.content, oamap.schema.Record):
        newarrays = _NewArrays.instance(data._arrays, data._generator)
        if isinstance(newfield, oamap.proxy.ListProxy) and len(data) == len(newfield):
            newarrays.merge(data._arrays, data._generator)
            fieldschema = data._generator.namedschema().content

        elif len(data) == len(newfield):
            if not isinstance(newfield, numpy.ndarray):
                newfield = numpy.array(newfield)
            fieldschema = oamap.schema.Primitive(newfield.dtype)
            newarrays.put(fieldschema, "data", newfield)

        else:
            raise TypeError("if data is a List, newfield must be a ListProxy or Numpy array of the right length ({0} elements)".format(len(data)))

        schema = data._generator.namedschema()
        schema.content[fieldname] = fieldschema
        return schema(newarrays)

    else:
        raise TypeError("attach can only be applied to a top-level Record(...) or List(Record(...))")

################################################################ detach

def detach(data, fieldname):
    if isinstance(data, oamap.proxy.RecordProxy) and fieldname in data._generator.schema.fields:
        schema = data._generator.namedschema()
        del schema[fieldname]
        out = schema(data._arrays)
        out._index = data._index
        return out

    elif isinstance(data, oamap.proxy.ListProxy) and isinstance(data._generator.schema.content, oamap.schema.Record) and fieldname in data._generator.schema.content.fields:
        schema = data._generator.namedschema()
        del schema.content[fieldname]
        out = schema(data._arrays)
        out._whence, out._stride, out._length = data._whence, data._stride, data._length
        return out

    else:
        raise TypeError("detach can only be applied to Record({{{0}: ...}}) or List(Record({{{0}: ...}}))".format(repr(fieldname)))

################################################################ flatten

def flatten(data):
    if isinstance(data, oamap.proxy.ListProxy) and data._whence == 0 and data._stride == 1 and isinstance(data._generator.schema.content, oamap.schema.List):
        if data._generator.schema.content.nullable:
            raise NotImplementedError("the inner List is nullable; need to merge masks")

        schema = data._generator.namedschema()
        schema.content = schema.content.content

        starts, stops = data._generator.content._getstartsstops(data._arrays, data._cache)

        if numpy.array_equal(starts[1:], stops[:-1]):
            # important special case: contiguous
            newarrays = _NewArrays.instance(data._arrays, data._generator)
            newarrays.put(schema, "starts", starts[:1])
            newarrays.put(schema, "stops", stops[-1:])
            return schema(newarrays)

        else:
            raise NotImplementedError("non-contiguous arrays: have to do some sort of concatenate")

    else:
        raise TypeError("flatten can only be applied to List(List(...))")

################################################################ filter

def filter(data, fcn, fieldname=None, numba=True):
    if fieldname is None and isinstance(data, oamap.proxy.ListProxy):
        if data._generator.schema.nullable:
            raise NotImplementedError("data is nullable; need to merge masks")

        schema = oamap.schema.List(oamap.schema.Pointer(data._generator.namedschema().content))

        fcn = maybecompile(numba)(fcn)
        whence = data._whence
        stride = data._stride

        @maybecompile(numba)
        def setpointers(data, pointers):
            i = whence
            j = 0
            for datum in data:
                if fcn(datum):
                    pointers[j] = i
                    j += 1
                i += stride
            return j

        pointers = numpy.empty(data._length, dtype=oamap.generator.PointerGenerator.posdtype)
        numentries = setpointers(data, pointers)

        arrays = _NewArrays.instance(data._arrays, data._generator)
        arrays.put(schema, "starts", numpy.array([0], dtype=data._generator.posdtype))
        arrays.put(schema, "stops", numpy.array([numentries], dtype=data._generator.posdtype))
        arrays.put(schema.content, "positions", pointers[:numentries])

        return schema(arrays)

    elif fieldname is not None and isinstance(data, oamap.proxy.ListProxy) and isinstance(data._generator.schema.content, oamap.schema.Record) and fieldname in data._generator.schema.content.fields:
        raise NotImplementedError

    elif fieldname is None:
        raise TypeError("filter without fieldname can only be applied to a List(...)")

    else:
        raise TypeError("filter with fieldname can only be applied to a List(Record({{{0}: ...}}))".format(repr(fieldname)))

################################################################ reduce

from oamap.schema import *

dataset = List("int").fromdata(range(10))

one = List(Record(dict(x=List("int"), y=List("double")))).fromdata([{"x": [1, 2, 3], "y": [1.1, 2.2]}, {"x": [], "y": []}, {"x": [4, 5], "y": [3.3]}])
two = List(Record(dict(x=List("int"), y=List("double")))).fromdata([{"x": [1, 2, 3], "y": [1.1, 2.2]}, {"x": [], "y": []}, {"x": [4, 5], "y": [3.3]}])
