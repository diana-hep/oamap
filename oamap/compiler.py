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
    class ArrayCacheType(numba.types.Type):
        def __init__(self):
            super(ArrayCacheType, self).__init__(name="ArrayCacheType")

    arraycachetype = ArrayCacheType()

    @numba.extending.register_model(ArrayCacheType)
    class ArrayCacheModel(numba.datamodel.models.StructModel):
        def __init__(self, dmm, fe_type):
            members = [("cache", numba.types.intp),
                       ("ptr", numba.types.intp[:]),
                       ("len", numba.types.intp[:])]
            super(ArrayCacheModel, self).__init__(dmm, fe_type, members)

    def unbox_arraycache(cache_obj, c):
        entercompiled_fcn = c.pyapi.object_getattr_string(cache_obj, "entercompiled")
        c.pyapi.call_function_objargs(entercompiled_fcn, ())
        ptr_obj = c.pyapi.object_getattr_string(cache_obj, "ptr")
        len_obj = c.pyapi.object_getattr_string(cache_obj, "len")

        arraycache = numba.cgutils.create_struct_proxy(arraycachetype)(c.context, c.builder)
        arraycache.cache = c.builder.ptrtoint(cache_obj, llvmlite.llvmpy.core.Type.int(numba.types.intp.bitwidth))
        arraycache.ptr = numba.targets.boxing.unbox_array(numba.types.intp[:], ptr_obj, c).value
        arraycache.len = numba.targets.boxing.unbox_array(numba.types.intp[:], len_obj, c).value

        c.pyapi.decref(cache_obj)
        c.pyapi.decref(ptr_obj)
        c.pyapi.decref(len_obj)

        return arraycache._getvalue()

    def box_arraycache(context, builder, pyapi, arraycache_val, decref_arrays=False):
        arraycache = numba.cgutils.create_struct_proxy(arraycachetype)(context, builder, value=arraycache_val)
        cache_obj = builder.inttoptr(arraycache.cache, pyapi.pyobj)
        if decref_arrays:
            ptr_obj = pyapi.object_getattr_string(cache_obj, "ptr")
            len_obj = pyapi.object_getattr_string(cache_obj, "len")
            pyapi.decref(ptr_obj); pyapi.decref(ptr_obj)
            pyapi.decref(len_obj); pyapi.decref(len_obj)
        return cache_obj

    class ListProxyNumbaType(numba.types.Type):
        def __init__(self, proxytype):
            self.proxytype = proxytype
            super(ListProxyNumbaType, self).__init__(name=self.proxytype._uniquestr)

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
                if isinstance(idx, numba.types.Integer):
                    return typeof_proxytype(tpe.proxytype._content)(tpe, idx)

    import sys

    def getarray(arrays, name, cache, cacheidx, dtype, dims):
        print "getarray"

        array = arrays[name]
        if not isinstance(array, numpy.ndarray):
            raise TypeError("arrays[{0}] returned a {1} ({2}) instead of a Numpy array".format(repr(name), type(array), repr(array)))
        if array.dtype != dtype:
            raise TypeError("arrays[{0}] returned an array of type {1} instead of {2}".format(repr(name), array.dtype, dtype))
        if array.shape[1:] != dims:
            raise TypeError("arrays[{0}] returned an array with shape[1:] {1} instead of {2}".format(repr(name), array.shape[1:], dims))
        cache.arraylist[cacheidx] = array
        cache.ptr[cacheidx] = array.ctypes.data
        cache.len[cacheidx] = array.shape[0]

    # def new(context, builder, pyapi, proxytype, arraycache, at):
    #     if issubclass(proxytype, Masked) and issubclass(proxytype, PrimitiveProxy):
    #         raise NotImplementedError

    #     elif issubclass(proxytype, PrimitiveProxy):
    #         dataidx = llvmlite.llvmpy.core.Constant.int(llvmlite.llvmpy.core.Type.int(32), proxytype._dataidx)

    #         data = numba.cgutils.create_struct_proxy(numba.types.intp




    #     else:
    #         raise NotImplementedError

    @numba.extending.lower_builtin("getitem", ListProxyNumbaType, numba.types.Integer)
    def listproxy_getitem(context, builder, sig, args):
        listtpe, idxtpe = sig.args
        listval, idxval = args

        pyapi = context.get_python_api(builder)
        listproxy = numba.cgutils.create_struct_proxy(listtpe)(context, builder, value=listval)
        arraycache = numba.cgutils.create_struct_proxy(arraycachetype)(context, builder, value=listproxy.arraycache)
        
        cacheidx = llvmlite.llvmpy.core.Constant.int(llvmlite.llvmpy.core.Type.int(64), listtpe.proxytype._content._dataidx)

        ptr_val = numba.cgutils.create_struct_proxy(numba.types.intp[:])(context, builder, value=arraycache.ptr)
        ptr_intp = numba.targets.arrayobj.load_item(context, builder, numba.types.intp[:], numba.cgutils.get_item_pointer(builder, numba.types.intp[:], ptr_val, [cacheidx]))

        with numba.cgutils.if_unlikely(builder, builder.not_(context.is_true(builder, numba.types.int8, ptr_intp))):
            getarray_fcn = pyapi.unserialize(pyapi.serialize_object(getarray))
            arrays_obj = builder.inttoptr(listproxy.arrays, pyapi.pyobj)
            name_obj = pyapi.unserialize(pyapi.serialize_object(listtpe.proxytype._content._data))
            cache_obj = box_arraycache(context, builder, pyapi, listproxy.arraycache, decref_arrays=False)
            cacheidx_obj = pyapi.long_from_long(cacheidx)
            dtype_obj = pyapi.unserialize(pyapi.serialize_object(listtpe.proxytype._content._dtype))
            dims_obj = pyapi.unserialize(pyapi.serialize_object(listtpe.proxytype._content._dims))
            pyapi.call_function_objargs(getarray_fcn, (arrays_obj, name_obj, cache_obj, cacheidx_obj, dtype_obj, dims_obj))
            pyapi.decref(cacheidx_obj)
            pyapi.decref(dtype_obj)
            pyapi.decref(dims_obj)

        ptr_val = numba.cgutils.create_struct_proxy(numba.types.intp[:])(context, builder, value=arraycache.ptr)
        ptr_intp = numba.targets.arrayobj.load_item(context, builder, numba.types.intp[:], numba.cgutils.get_item_pointer(builder, numba.types.intp[:], ptr_val, [cacheidx]))
        len_val = numba.cgutils.create_struct_proxy(numba.types.intp[:])(context, builder, value=arraycache.len)
        len_intp = numba.targets.arrayobj.load_item(context, builder, numba.types.intp[:], numba.cgutils.get_item_pointer(builder, numba.types.intp[:], len_val, [cacheidx]))

        shifted = builder.add(ptr_intp, builder.mul(idxval, llvmlite.llvmpy.core.Constant.int(llvmlite.llvmpy.core.Type.int(64), listtpe.proxytype._content._dtype.itemsize)))
        ptr = builder.inttoptr(shifted, llvmlite.llvmpy.core.Type.pointer(llvmlite.llvmpy.core.Type.double()))
        return numba.targets.arrayobj.load_item(context, builder, numba.types.float64[:], ptr)

    @numba.extending.unbox(ListProxyNumbaType)
    def unbox_listproxy(typ, obj, c):
        class_obj = c.pyapi.object_getattr_string(obj, "__class__")
        arrays_obj = c.pyapi.object_getattr_string(obj, "_arrays")
        cache_obj = c.pyapi.object_getattr_string(obj, "_cache")
        start_obj = c.pyapi.object_getattr_string(obj, "_start")
        stop_obj = c.pyapi.object_getattr_string(obj, "_stop")
        step_obj = c.pyapi.object_getattr_string(obj, "_step")

        listproxy = numba.cgutils.create_struct_proxy(typ)(c.context, c.builder)
        listproxy.proxytype = c.builder.ptrtoint(class_obj, llvmlite.llvmpy.core.Type.int(numba.types.intp.bitwidth))
        listproxy.arrays = c.builder.ptrtoint(arrays_obj, llvmlite.llvmpy.core.Type.int(numba.types.intp.bitwidth))
        listproxy.arraycache = unbox_arraycache(cache_obj, c)
        listproxy.start = c.pyapi.number_as_ssize_t(start_obj)
        listproxy.stop = c.pyapi.number_as_ssize_t(stop_obj)
        listproxy.step = c.pyapi.number_as_ssize_t(step_obj)

        c.pyapi.decref(class_obj)
        c.pyapi.decref(arrays_obj)
        c.pyapi.decref(cache_obj)
        c.pyapi.decref(start_obj)
        c.pyapi.decref(stop_obj)
        c.pyapi.decref(step_obj)

        is_error = numba.cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
        return numba.extending.NativeValue(listproxy._getvalue(), is_error=is_error)

    @numba.extending.box(ListProxyNumbaType)
    def box_listproxy(typ, val, c):
        listproxy = numba.cgutils.create_struct_proxy(typ)(c.context, c.builder, value=val)
        class_obj = c.builder.inttoptr(listproxy.proxytype, c.pyapi.pyobj)
        arrays_obj = c.builder.inttoptr(listproxy.arrays, c.pyapi.pyobj)
        cache_obj = box_arraycache(c.context, c.builder, c.pyapi, listproxy.arraycache, decref_arrays=True)
        start_obj = c.pyapi.long_from_ssize_t(listproxy.start)
        stop_obj = c.pyapi.long_from_ssize_t(listproxy.stop)
        step_obj = c.pyapi.long_from_ssize_t(listproxy.step)

        slice_fcn = c.pyapi.object_getattr_string(class_obj, "_slice")
        out = c.pyapi.call_function_objargs(slice_fcn, (arrays_obj, cache_obj, start_obj, stop_obj, step_obj))

        c.pyapi.decref(class_obj)
        # c.pyapi.decref(arrays_obj)   # not this one
        # c.pyapi.decref(cache_obj)    # not this one
        c.pyapi.decref(start_obj)
        c.pyapi.decref(stop_obj)
        c.pyapi.decref(step_obj)
        # c.pyapi.decref(slice_fcn)    # not this one
        return out

    def exposetype(proxytype):
        if issubclass(proxytype, oamap.proxy.ListProxy):
            pass

