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

class NewArrays(object):
    @staticmethod
    def get(oldarrays, names):
        if isinstance(oldarrays, NewArrays):
            return oldarrays
        else:
            return NewArrays(oldarrays, names)

    def __init__(self, oldarrays, names):
        self.oldarrays = oldarrays
        self.newarrays = {}
        self.schemas = {}

        nss = set()
        for n, ns in names:
            nss.add(ns)

        num = 0
        self.namespace = None
        while self.namespace is None or self.namespace in nss:
            self.namespace = "namespace-{0}".format(num)
            num += 1

    def getall(self, roles):
        out = dict((x, self.newarrays[str(x)]) for x in roles if x.namespace == self.namespace)
        if hasattr(self.oldarrays, "getall"):
            out.update(self.oldarrays.getall([x for x in roles if x.namespace != self.namespace]))
        else:
            out.update(dict((x, self.oldarrays[str(x)]) for x in roles if x.namespace != self.namespace))
        return out

    def put(self, schema, attr, value):
        name = str(len(self.newarrays))

        self.schemas[name] = schema
        schema.namespace = self.namespace
        setattr(schema, attr, name)

        self.newarrays[name] = value

    def close(self):
        if hasattr(self.oldarrays, "close"):
            self.oldarrays.close()

################################################################ filter

def filter(data, fcn, fieldname=None, numba=True):
    if not isinstance(data, oamap.proxy.ListProxy):
        raise TypeError("filter can only be applied to OAMap lists")

    if isinstance(data, oamap.proxy.PartitionedListProxy):
        raise NotImplementedError

    if fieldname is not None:
        raise NotImplementedError

    oldschema = data._generator.namedschema()
    newschema = oamap.schema.List(oamap.schema.Pointer(oldschema.content))

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
    newarrays.put(newschema, "starts", numpy.array([0], dtype=data._generator.posdtype))
    newarrays.put(newschema, "stops", numpy.array([numentries], dtype=data._generator.posdtype))
    newarrays.put(newschema.content, "positions", pointers[:numentries])

    return newschema(newarrays)

################################################################ flatten

################################################################ define

################################################################ remove

################################################################ reduce

# dataset = oamap.schema.List("int").fromdata(range(10))

