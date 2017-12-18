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

import numpy

try:
    import numba
except ImportError:
    numba = None

import oamap.proxy

if numba is None:
    def exposetype(proxytype):
        pass

else:
    class ArrayCache(object):
        @classmethod
        def empty(cls, cachelen):
            arrayobjs = numpy.zeros(cachelen, dtype=numpy.intp)
            arraydata = numpy.zeros(cachelen, dtype=numpy.intp)
            arraysize = numpy.zeros(cachelen, dtype=numpy.intp)
            return cls(arrayobjs, arraydata, arraysize)

        def __init__(self, arrayobjs, arraydata, arraysize):
            self.arrayobjs = arrayobjs
            self.arraydata = arraydata
            self.arraysize = arraysize

    class ArrayCacheNumbaType(numba.types.Type):
        def __init__(self, cachelen):
            self.cachelen = cachelen
            super(ArrayCacheNumbaType, self).__init__(name="ArrayCache")

    @numba.extending.typeof_impl.register(ArrayCache)
    def typeof_arraycache(val, c):
        return ArrayCacheNumbaType(len(val.arrayobjs))

    @numba.extending.register_model(ArrayCacheNumbaType)
    class ArrayCacheModel(numba.datamodel.models.StructModel):
        def __init__(self, dmm, fe_type):
            members = [("arrayobjs", numba.types.intp[:]),
                       ("arraydata", numba.types.intp[:]),
                       ("arraysize", numba.types.intp[:]),
                       ("cachelen", numba.types.int32)]
            super(ArrayCacheModel, self).__init__(dmm, fe_type, members)

    class GetIt(Exception):
        def __init__(self, stuff):
            self.stuff = stuff

    @numba.extending.unbox(ArrayCacheNumbaType)
    def unbox_arraycache(typ, obj, c):
        arrayobjs = c.pyapi.object_getattr_string(obj, "arrayobjs")
        arraydata = c.pyapi.object_getattr_string(obj, "arraydata")
        arraysize = c.pyapi.object_getattr_string(obj, "arraysize")

        arraycache = numba.cgutils.create_struct_proxy(typ)(c.context, c.builder)
        arraycache.arrayobjs = numba.targets.boxing.unbox_array(numba.types.intp[:], arrayobjs, c).value
        arraycache.arraydata = numba.targets.boxing.unbox_array(numba.types.intp[:], arraydata, c).value
        arraycache.arraysize = numba.targets.boxing.unbox_array(numba.types.intp[:], arraysize, c).value

        # decref

        is_error = numba.cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
        return numba.extending.NativeValue(arraycache._getvalue(), is_error=is_error)

    @numba.extending.box(ArrayCacheNumbaType)
    def box_arraycache(typ, val, c):
        arraycache = numba.cgutils.create_struct_proxy(typ)(c.context, c.builder, value=val)
        arrayobjs = numba.targets.boxing.box_array(numba.types.intp[:], arraycache.arrayobjs, c)
        arraydata = numba.targets.boxing.box_array(numba.types.intp[:], arraycache.arraydata, c)
        arraysize = numba.targets.boxing.box_array(numba.types.intp[:], arraycache.arraysize, c)

        arraycache_cls = c.pyapi.unserialize(c.pyapi.serialize_object(ArrayCache))
        out = c.pyapi.call_function_objargs(arraycache_cls, (arrayobjs, arraydata, arraysize))

        # decref

        return out

    arraycache = ArrayCache.empty(5)
    arraycache.arrayobjs[2] = 999

    print id(arraycache), arraycache.__dict__

    @numba.njit
    def inandout(x):
        return x

    arraycache2 = inandout(arraycache)

    arraycache.arrayobjs[3] = 888

    print id(arraycache2), arraycache2.__dict__



    def exposetype(proxytype):
        if issubclass(proxytype, oamap.proxy.ListProxy):
            pass

