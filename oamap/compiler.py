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
    import llvmlite.llvmpy.core
except ImportError:
    numba = None

import oamap.proxy

if numba is None:
    def exposetype(proxytype):
        pass

else:
    class ArrayCache(object):
        @staticmethod
        def empty(cachelen):
            arrayobjs = [None] * cachelen
            arraydata = numpy.zeros(cachelen, dtype=numpy.intp)
            arraysize = numpy.zeros(cachelen, dtype=numpy.intp)
            return ArrayCache(arrayobjs, arraydata, arraysize)

        def __init__(self, arrayobjs, arraydata, arraysize):
            self.arrayobjs = arrayobjs
            self.arraydata = arraydata
            self.arraysize = arraysize

    def ArrayCache_fromcache(cache):
        arraydata = numpy.zeros(len(cache), dtype=numpy.intp)
        arraysize = numpy.zeros(len(cache), dtype=numpy.intp)
        for i, x in enumerate(cache):
            if x is not None:
                if not isinstance(x, numpy.ndarray):
                    raise TypeError("all arrays must have numpy.ndarray type for use in compiled code")
                arraydata[i] = x.ctypes.data
                arraysize[i] = x.shape[0]
        return ArrayCache(cache, arraydata, arraysize)

    class ArrayCacheNumbaType(numba.types.Type):
        def __init__(self):
            super(ArrayCacheNumbaType, self).__init__(name="ArrayCache")

    arraycachetype = ArrayCacheNumbaType()

    @numba.extending.typeof_impl.register(ArrayCache)
    def typeof_arraycache(val, c):
        return arraycachetype

    @numba.extending.register_model(ArrayCacheNumbaType)
    class ArrayCacheModel(numba.datamodel.models.StructModel):
        def __init__(self, dmm, fe_type):
            members = [("arrayobjs", numba.types.intp),
                       ("arraydata", numba.types.intp[:]),
                       ("arraysize", numba.types.intp[:]),
                       ("cachelen", numba.types.int32)]
            super(ArrayCacheModel, self).__init__(dmm, fe_type, members)

    @numba.extending.unbox(ArrayCacheNumbaType)
    def unbox_arraycache(typ, obj, c):
        arrayobjs = c.pyapi.object_getattr_string(obj, "arrayobjs")
        arraydata = c.pyapi.object_getattr_string(obj, "arraydata")
        arraysize = c.pyapi.object_getattr_string(obj, "arraysize")

        arraycache = numba.cgutils.create_struct_proxy(typ)(c.context, c.builder)
        arraycache.arrayobjs = c.builder.ptrtoint(arrayobjs, llvmlite.llvmpy.core.Type.int(numba.types.intp.bitwidth))
        arraycache.arraydata = numba.targets.boxing.unbox_array(numba.types.intp[:], arraydata, c).value
        arraycache.arraysize = numba.targets.boxing.unbox_array(numba.types.intp[:], arraysize, c).value

        c.pyapi.decref(arraydata)
        c.pyapi.decref(arraysize)

        is_error = numba.cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
        return numba.extending.NativeValue(arraycache._getvalue(), is_error=is_error)

    @numba.extending.box(ArrayCacheNumbaType)
    def box_arraycache(typ, val, c):
        arraycache = numba.cgutils.create_struct_proxy(typ)(c.context, c.builder, value=val)
        arrayobjs = c.builder.inttoptr(arraycache.arrayobjs, c.pyapi.pyobj)
        arraydata = numba.targets.boxing.box_array(numba.types.intp[:], arraycache.arraydata, c)
        arraysize = numba.targets.boxing.box_array(numba.types.intp[:], arraycache.arraysize, c)

        arraycache_cls = c.pyapi.unserialize(c.pyapi.serialize_object(ArrayCache))
        out = c.pyapi.call_function_objargs(arraycache_cls, (arrayobjs, arraydata, arraysize))

        c.pyapi.decref(arrayobjs)
        c.pyapi.decref(arraydata)
        c.pyapi.decref(arraysize)
        c.pyapi.decref(arraycache_cls)
        return out

    def getarray(arrays, name, arraycache, cacheidx, dtype, dims):
        array = arrays[name]
        if not isinstance(array, numpy.ndarray):
            raise TypeError("arrays[{0}] returned a {1} ({2}) instead of a Numpy array".format(repr(name), type(array), repr(array)))
        if array.dtype != dtype:
            raise TypeError("arrays[{0}] returned an array of type {1} instead of {2}".format(repr(name), array.dtype, dtype))
        if array.shape[1:] != dims:
            raise TypeError("arrays[{0}] returned an array with shape[1:] {1} instead of {2}".format(repr(name), array.shape[1:], dims))
        arraycache.arrayobjs[cacheidx] = array
        arraycache.arraydata[cacheidx] = array.ctypes.data
        arraycache.arraysize[cacheidx] = array.shape[0]

    class ListProxyNumbaType(numba.types.Type):
        def __init__(self, proxytype):
            self.proxytype = proxytype
            super(ListProxyNumbaType, self).__init__(name="ListProxy")

    def typeof_proxytype(proxytype):
        if issubclass(proxytype, oamap.proxy.PrimitiveProxy):
            if proxytype._dims == ():
                return numba.from_dtype(proxytype._dtype)
            else:
                raise NotImplementedError(proxytype._dims)
        elif issubclass(proxytype, oamap.proxy.ListProxy):
            return ListProxyNumbaType(proxytype)
        else:
            raise NotImplementedError(proxytype.__bases__)

    @numba.extending.typeof_impl.register(oamap.proxy.Proxy)
    def typeof_proxy(val, c):
        return typeof_proxytype(val.__class__)

    @numba.extending.register_model(ListProxyNumbaType)
    class ListProxyModel(numba.datamodel.models.StructModel):
        def __init__(self, dmm, fe_type):
            members = [("proxytype", numba.types.intp),
                       ("arrays", numba.types.intp),
                       ("arraycache", arraycachetype),
                       ("start", numba.types.intp),
                       ("stop", numba.types.intp),
                       ("step", numba.types.intp)]
            super(ListProxyModel, self).__init__(dmm, fe_type, members)

    @numba.typing.templates.infer
    class ListProxyGetItem(numba.typing.templates.AbstractTemplate):
        key = "getitem"

        def generic(self, args, kwds):
            tpe, idx = args
            if isinstance(tpe, ListProxyNumbaType):
                # idx = numba.typing.builtins.normalize_1d_index(idx)
                if isinstance(idx, numba.types.Integer):
                    return typeof_proxytype(tpe.proxytype._content)(tpe, idx)

    @numba.extending.lower_builtin("getitem", ListProxyNumbaType, numba.types.Integer)
    def listproxy_getitem(context, builder, sig, args):
        return llvmlite.llvmpy.core.Constant.real(llvmlite.llvmpy.core.Type.double(), 3.14)
                    
    @numba.extending.unbox(ListProxyNumbaType)
    def unbox_listproxy(typ, obj, c):
        class_obj = c.pyapi.object_getattr_string(obj, "__class__")
        arrays_obj = c.pyapi.object_getattr_string(obj, "_arrays")
        cache_obj = c.pyapi.object_getattr_string(obj, "_cache")
        start_obj = c.pyapi.object_getattr_string(obj, "_start")
        stop_obj = c.pyapi.object_getattr_string(obj, "_stop")
        step_obj = c.pyapi.object_getattr_string(obj, "_step")

        fromcache_fcn = c.pyapi.unserialize(c.pyapi.serialize_object(ArrayCache_fromcache))
        arraycache_obj = c.pyapi.call_function_objargs(fromcache_fcn, (cache_obj,))

        arraycache = unbox_arraycache(arraycachetype, arraycache_obj, c)

        listproxy = numba.cgutils.create_struct_proxy(typ)(c.context, c.builder)
        listproxy.proxytype = c.builder.ptrtoint(class_obj, llvmlite.llvmpy.core.Type.int(numba.types.intp.bitwidth))
        listproxy.arrays = c.builder.ptrtoint(arrays_obj, llvmlite.llvmpy.core.Type.int(numba.types.intp.bitwidth))
        listproxy.arraycache = arraycache.value
        listproxy.start = c.pyapi.number_as_ssize_t(start_obj)
        listproxy.stop = c.pyapi.number_as_ssize_t(stop_obj)
        listproxy.step = c.pyapi.number_as_ssize_t(step_obj)

        c.pyapi.decref(class_obj)
        c.pyapi.decref(cache_obj)
        c.pyapi.decref(start_obj)
        c.pyapi.decref(stop_obj)
        c.pyapi.decref(step_obj)
        c.pyapi.decref(fromcache_fcn)
        c.pyapi.decref(arraycache_obj)

        is_error = numba.cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
        return numba.extending.NativeValue(listproxy._getvalue(), is_error=is_error)

    @numba.extending.box(ListProxyNumbaType)
    def box_listproxy(typ, val, c):
        listproxy = numba.cgutils.create_struct_proxy(typ)(c.context, c.builder, value=val)
        class_obj = c.builder.inttoptr(listproxy.proxytype, c.pyapi.pyobj)
        arrays_obj = c.builder.inttoptr(listproxy.arrays, c.pyapi.pyobj)

        arraycache = numba.cgutils.create_struct_proxy(arraycachetype)(c.context, c.builder, value=listproxy.arraycache)
        cache_obj = c.builder.inttoptr(arraycache.arrayobjs, c.pyapi.pyobj)

        start_obj = c.pyapi.long_from_ssize_t(listproxy.start)
        stop_obj = c.pyapi.long_from_ssize_t(listproxy.stop)
        step_obj = c.pyapi.long_from_ssize_t(listproxy.step)

        slice_fcn = c.pyapi.object_getattr_string(class_obj, "_slice")
        out = c.pyapi.call_function_objargs(slice_fcn, (arrays_obj, cache_obj, start_obj, stop_obj, step_obj))

        c.pyapi.decref(class_obj)
        c.pyapi.decref(arrays_obj)
        c.pyapi.decref(cache_obj)
        c.pyapi.decref(start_obj)
        c.pyapi.decref(stop_obj)
        c.pyapi.decref(step_obj)
        return out

    def exposetype(proxytype):
        if issubclass(proxytype, oamap.proxy.ListProxy):
            pass

