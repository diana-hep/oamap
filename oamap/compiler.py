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

import pickle

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
    class CacheType(numba.types.Type):
        def __init__(self):
            super(CacheType, self).__init__(name="CacheType")

    cachetype = CacheType()

    @numba.extending.register_model(CacheType)
    class CacheModel(numba.datamodel.models.StructModel):
        def __init__(self, dmm, fe_type):
            members = [("cache", numba.types.intp),
                       ("ptr", numba.types.intp[:]),
                       ("len", numba.types.intp[:])]
            super(CacheModel, self).__init__(dmm, fe_type, members)

    def unbox_cache(cache_obj, c):
        entercompiled_fcn = c.pyapi.object_getattr_string(cache_obj, "entercompiled")
        c.pyapi.call_function_objargs(entercompiled_fcn, ())
        ptr_obj = c.pyapi.object_getattr_string(cache_obj, "ptr")
        len_obj = c.pyapi.object_getattr_string(cache_obj, "len")

        cache = numba.cgutils.create_struct_proxy(cachetype)(c.context, c.builder)
        cache.cache = c.builder.ptrtoint(cache_obj, llvmlite.llvmpy.core.Type.int(numba.types.intp.bitwidth))
        cache.ptr = numba.targets.boxing.unbox_array(numba.types.intp[:], ptr_obj, c).value
        cache.len = numba.targets.boxing.unbox_array(numba.types.intp[:], len_obj, c).value

        c.pyapi.decref(cache_obj)
        c.pyapi.decref(ptr_obj)
        c.pyapi.decref(len_obj)

        return cache._getvalue()

    def box_cache(context, builder, pyapi, cache_val, decref_arrays=False):
        cache = numba.cgutils.create_struct_proxy(cachetype)(context, builder, value=cache_val)
        cache_obj = builder.inttoptr(cache.cache, pyapi.pyobj)
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
                       ("cache", cachetype),
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

    def getarray(arrays, name, cache, cacheidx, dtype, dims):
        print "getarray", name, cacheidx, dtype, dims

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

        return pickle.dumps(Exception("hello"))

    def constint(value, bits=64):
        return llvmlite.llvmpy.core.Constant.int(llvmlite.llvmpy.core.Type.int(bits), value)

    def atidx(context, builder, ptrarray, idx):
        return numba.targets.arrayobj.load_item(context, builder, numba.types.intp[:], numba.cgutils.get_item_pointer(builder, numba.types.intp[:], ptrarray, [idx]))

    def ensure(context, builder, pyapi, ptr, arrays, name, cache, cacheidx, dtype, dims):
        with builder.if_then(builder.not_(context.is_true(builder, numba.types.int8, ptr)), likely=False):
            getarray_fcn = pyapi.unserialize(pyapi.serialize_object(getarray))
            arrays_obj = builder.inttoptr(arrays, pyapi.pyobj)
            name_obj = pyapi.unserialize(pyapi.serialize_object(name))
            cache_obj = box_cache(context, builder, pyapi, cache, decref_arrays=False)
            cacheidx_obj = pyapi.long_from_long(cacheidx)
            dtype_obj = pyapi.unserialize(pyapi.serialize_object(dtype))
            dims_obj = pyapi.unserialize(pyapi.serialize_object(dims))
            exception = pyapi.call_function_objargs(getarray_fcn, (arrays_obj, name_obj, cache_obj, cacheidx_obj, dtype_obj, dims_obj))
            pyapi.decref(cacheidx_obj)
            pyapi.decref(dtype_obj)
            pyapi.decref(dims_obj)

            ok, buf, len64 = pyapi.string_as_string_and_size(exception)
            len32 = builder.trunc(len64, llvmlite.llvmpy.core.Type.int(32))
            buflen = llvmlite.llvmpy.core.ir.Constant.literal_struct([buf, len32])

            # buflen = numba.cgutils.alloca_once_value(builder, llvmlite.llvmpy.core.ir.Constant.literal_struct([buf, len32]))

            # print dir(buflen)

            # buflentype = llvmlite.llvmpy.core.Type.struct([llvmlite.llvmpy.core.Type.pointer(llvmlite.llvmpy.core.Type.int(8)), llvmlite.llvmpy.core.Type.int(32)])
            # buflen = numba.cgutils.alloca_once(builder, buflentype)
            # builder.store(llvmlite.llvmpy.core.ir.Constant.literal_struct([buf, len32]), buflen)

            # context.pack_value(builder, buflentype, llvmlite.llvmpy.core.ir.Constant.literal_struct([buf, len_]), buflen)

            # help(context.pack_value)

            # buflentype = llvmlite.llvmpy.core.Type.struct([llvmlite.llvmpy.core.Type.pointer(llvmlite.llvmpy.core.Type.int(8)), llvmlite.llvmpy.core.Type.int(32)])
            # buflen = numba.cgutils.alloca_once(builder, buflentype)
            # numba.cgutils.printf(builder, "WOWIE %ld\n", buflen)
            # builder.store(ir.Constant.literal_struct([]), buflen)
            # # builder.store(buf, builder.bitcast(buflen, llvmlite.llvmpy.core.Type.pointer(buflentype.elements[0])))
            # # context.cast(builder, buflen, buflentype, buflentype.elements[0])
            # # builder.store(buf, )
            # numba.cgutils.printf(builder, "WOWIE %ld\n", buflen)
            # print "buflen.type", buflen.type

            # numba.cgutils.alloca_once(builder, HERE llvmlite.llvmpy.core.Type.int(64))

            exception2 = pyapi.serialize_object(KeyError("whatever"))
            # builder.store(llvmlite.llvmpy.core.ir.Constant.literal_struct([buf, len32]), exception2)

            print "exception2.type", exception2.type

            excptr = context.call_conv._get_excinfo_argument(builder.function)

            print "excptr.type", excptr.type
            
            builder.store(exception2, excptr)
            # builder.store(buflen, excptr)
            context.call_conv._return_errcode_raw(builder, numba.targets.callconv.RETCODE_USEREXC)


            # with builder.if_then(numba.cgutils.is_not_null(builder, pyapi.err_occurred()), likely=False):
            #     builder.ret(numba.targets.callconv.RETCODE_USEREXC)
                # context.call_conv.return_value(builder, llvmlite.llvmpy.core.Constant.real(llvmlite.llvmpy.core.Type.double(), 3.14))

                # context.call_conv.return_user_exc(builder, IndexError, ("hey",))

    def llvmptr(context, builder, pos, dtype):
        return builder.inttoptr(pos, llvmlite.llvmpy.core.Type.pointer(context.get_value_type(numba.from_dtype(dtype))))

    def new(context, builder, pyapi, arrays, cache, proxytype, at):
        cacheproxy = numba.cgutils.create_struct_proxy(cachetype)(context, builder, value=cache)
        ptrarray = numba.cgutils.create_struct_proxy(numba.types.intp[:])(context, builder, value=cacheproxy.ptr)
        lenarray = numba.cgutils.create_struct_proxy(numba.types.intp[:])(context, builder, value=cacheproxy.len)

        if issubclass(proxytype, oamap.proxy.Masked) and issubclass(proxytype, oamap.proxy.PrimitiveProxy):
            raise NotImplementedError

        elif issubclass(proxytype, oamap.proxy.PrimitiveProxy):
            dataidx = constint(proxytype._dataidx)
            dataptr = atidx(context, builder, ptrarray, dataidx)
            ensure(context, builder, pyapi, dataptr, arrays, proxytype._data, cache, dataidx, proxytype._dtype, proxytype._dims)

            dataptr = atidx(context, builder, ptrarray, dataidx)
            datalen = atidx(context, builder, lenarray, dataidx)

            pos = builder.add(dataptr, builder.mul(at, constint(proxytype._dtype.itemsize)))
            return numba.targets.arrayobj.load_item(context, builder, numba.from_dtype(proxytype._dtype)[:], llvmptr(context, builder, pos, proxytype._dtype))

        else:
            raise NotImplementedError

    @numba.extending.lower_builtin("getitem", ListProxyNumbaType, numba.types.Integer)
    def listproxy_getitem(context, builder, sig, args):
        listtpe, indextpe = sig.args
        listval, indexval = args

        pyapi = context.get_python_api(builder)
        listproxy = numba.cgutils.create_struct_proxy(listtpe)(context, builder, value=listval)

        lenself = builder.sub(listproxy.stop, listproxy.start)
        zero = constint(0)
        normptr = numba.cgutils.alloca_once(builder, llvmlite.llvmpy.core.Type.int(64))
        builder.store(indexval, normptr)
        with builder.if_then(builder.icmp_signed("<", indexval, zero)):
            builder.store(builder.add(indexval, lenself), normptr)

        normval = builder.load(normptr)
        with builder.if_then(builder.or_(builder.icmp_signed("<", normval, zero),
                                         builder.icmp_signed(">=", normval, lenself)), likely=False):
            context.call_conv.return_user_exc(builder, IndexError, ("index out of bounds",))

        at = builder.add(listproxy.start, builder.mul(listproxy.step, normval))
        return new(context, builder, pyapi, listproxy.arrays, listproxy.cache, listtpe.proxytype._content, at)

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
        listproxy.cache = unbox_cache(cache_obj, c)
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
        cache_obj = box_cache(c.context, c.builder, c.pyapi, listproxy.cache, decref_arrays=True)
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

