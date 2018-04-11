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

def compile(numba):
    if numba is not None and numba is not False:
        if numba is True:
            numbaopts = {}
        else:
            numbaopts = numba
        import numba as nb
        return lambda fcn: fcn if isinstance(fcn, nb.dispatcher.Dispatcher) else nb.jit(**numbaopts)(fcn)
    else:
        return lambda fcn: fcn

class DualSource(object):
    def __init__(self, old, oldns):
        self.old = old
        self.new = {}

        i = 0
        self.namespace = None
        while self.namespace is None or self.namespace in oldns:
            self.namespace = "namespace-" + str(i)
            i += 1

        self._arraynum = 0

    def arrayname(self):
        trial = None
        while trial is None or trial in self.new:
            trial = "array-" + str(self._arraynum)
            self._arraynum += 1
        return trial

    def getall(self, roles):
        out = {}

        if hasattr(self.old, "getall"):
            out.update(self.old.getall([x for x in roles if x.namespace != self.namespace]))
        else:
            for x in roles:
                if x.namespace != self.namespace:
                    out[x] = self.old[str(x)]

        if hasattr(self.new, "getall"):
            out.update(self.new.getall([x for x in roles if x.namespace == self.namespace]))
        else:
            for x in roles:
                if x.namespace == self.namespace:
                    out[x] = self.new[str(x)]

        return out

    def put(self, schemanode, *arrays):
        if isinstance(schemanode, oamap.schema.Primitive):
            datarole = oamap.generator.DataRole(self.arrayname(), self.namespace)
            roles2arrays = {datarole: arrays[0]}
            schemanode.data = str(datarole)

        elif isinstance(schemanode, oamap.schema.List):
            startsrole = oamap.generator.StartsRole(self.arrayname(), self.namespace, None)
            stopsrole = oamap.generator.StopsRole(self.arrayname(), self.namespace, None)
            startsrole.stops = stopsrole
            stopsrole.starts = startsrole
            roles2arrays = {startsrole: arrays[0], stopsrole: arrays[1]}
            schemanode.starts = str(startsrole)
            schemanode.stops = str(stopsrole)
                
        else:
            raise NotImplementedError(schemanode)

        if schemanode.nullable:
            maskrole = oamap.generator.MaskRole(self.arrayname(), self.namespace, roles2arrays)
            roles2arrays = dict(list(roles2arrays.items()) + [(maskrole, arrays[-1])])
            schemanode.mask = str(maskrole)

        schemanode.namespace = self.namespace
        self.putall(roles2arrays)

    def putall(self, roles2arrays):
        if hasattr(self.new, "putall"):
            self.new.putall(roles2arrays)
        else:
            for n, x in roles2arrays.items():
                self.new[str(n)] = x

    def close(self):
        if hasattr(self.old, "close"):
            self.old.close()
        if hasattr(self.new, "close"):
            self.new.close()

################################################################ project

################################################################ flatten

def flatten(data):
    if isinstance(data, oamap.proxy.ListProxy) and data._whence == 0 and data._stride == 1 and isinstance(data._generator.content, oamap.generator.ListGenerator):
        if isinstance(data._generator, oamap.generator.Masked) or isinstance(data._generator.content, oamap.generator.Masked):
            raise NotImplementedError("nullable lists; need to merge masks")

        schema = data._generator.namedschema()
        schema.content = schema.content.content
        arrays = DualSource(data._arrays, data._generator.namespaces())

        starts, stops = data._generator.content._getstartsstops(data._arrays, data._cache)

        if numpy.array_equal(starts[1:], stops[:-1]):
            # important special case: contiguous
            arrays.put(schema, starts[:1], stops[-1:])
            return schema(arrays)
        else:
            raise NotImplementedError("non-contiguous arrays: have to do some sort of concatenation")

    else:
        raise TypeError("flatten can only be applied to List(List(...))")

################################################################ filter

################################################################ quick test

# from oamap.schema import *

# dataset = List(Record(dict(x=List("int"), y=List("double")))).fromdata([{"x": [1, 2, 3], "y": [1.1, 2.2]}, {"x": [], "y": []}, {"x": [4, 5], "y": [3.3]}])

# dataset = List(List("int")).fromdata([[1, 2, 3], [], [4, 5]])

# dataset = List(List(List("int"))).fromdata([[[1, 2, 3], [4, 5], []], [], [[6], [7, 8]]])
