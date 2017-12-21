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

import oamap.generator
import oamap.proxy

if numba is not None:
    ################################################################ Cache

    class CacheType(numba.types.Type):
        def __init__(self):
            super(CacheType, self).__init__(name="CacheType")

    cachetype = CacheType()

    @numba.extending.register_model(CacheType)
    class CacheModel(numba.datamodel.models.StructModel):
        def __init__(self, dmm, fe_type):
            members = [("cache", numba.types.intp),
                       ("ptr", numba.types.intp),
                       ("len", numba.types.intp)]
            super(CacheModel, self).__init__(dmm, fe_type, members)

    def unbox_cache(cache_obj, c):
        entercompiled_fcn = c.pyapi.object_getattr_string(cache_obj, "entercompiled")
        pair_obj = c.pyapi.call_function_objargs(entercompiled_fcn, ())
        ptr_obj = c.pyapi.tuple_getitem(pair_obj, 0)
        len_obj = c.pyapi.tuple_getitem(pair_obj, 1)
        ptr_val = c.pyapi.number_as_ssize_t(ptr_obj)
        len_val = c.pyapi.number_as_ssize_t(len_obj)

        cache = numba.cgutils.create_struct_proxy(cachetype)(c.context, c.builder)
        cache.cache = c.builder.ptrtoint(cache_obj, llvmlite.llvmpy.core.Type.int(numba.types.intp.bitwidth))
        cache.ptr = c.builder.ptrtoint(ptr_val, llvmlite.llvmpy.core.Type.int(numba.types.intp.bitwidth))
        cache.len = c.builder.ptrtoint(len_val, llvmlite.llvmpy.core.Type.int(numba.types.intp.bitwidth))

        c.pyapi.decref(cache_obj)       # not this one: this one is decrefed by the calling function
        c.pyapi.decref(pair_obj)
        c.pyapi.decref(ptr_obj)
        c.pyapi.decref(len_obj)
        
        return cache._getvalue()

    def box_cache(context, builder, pyapi, cache_val):
        cache = numba.cgutils.create_struct_proxy(cachetype)(context, builder, value=cache_val)
        return builder.inttoptr(cache.cache, pyapi.pyobj)

    ################################################################ general routines for all types

    def typeof_generator(generator):
        if isinstance(generator, oamap.generator.MaskedPrimitiveGenerator):
            raise NotImplementedError

        elif isinstance(generator, oamap.generator.PrimitiveGenerator):
            if generator.dims == ():
                return numba.from_dtype(generator.dtype)
            else:
                raise NotImplementedError

        elif isinstance(generator, oamap.generator.MaskedListGenerator):
            raise NotImplementedError

        elif isinstance(generator, oamap.generator.ListGenerator):
            return ListProxyNumbaType(generator)

        elif isinstance(generator, oamap.generator.MaskedUnionGenerator):
            raise NotImplementedError

        elif isinstance(generator, oamap.generator.UnionGenerator):
            raise NotImplementedError

        elif isinstance(generator, oamap.generator.MaskedRecordGenerator):
            raise NotImplementedError

        elif isinstance(generator, oamap.generator.RecordGenerator):
            return RecordProxyNumbaType(generator)

        elif isinstance(generator, oamap.generator.MaskedTupleGenerator):
            raise NotImplementedError

        elif isinstance(generator, oamap.generator.TupleGenerator):
            raise NotImplementedError

        elif isinstance(generator, oamap.generator.MaskedPointerGenerator):
            raise NotImplementedError

        elif isinstance(generator, oamap.generator.PointerGenerator):
            raise NotImplementedError

        else:
            raise AssertionError("unrecognized generator type: {0} ({1})".format(generator.__class__, repr(generator)))

    @numba.extending.typeof_impl.register(oamap.proxy.Proxy)
    def typeof_proxy(val, c):
        return typeof_generator(val._generator)

    def getarray(arrays, name, cache, cacheidx, dtype, dims):
        try:
            array = arrays[name]
            if not isinstance(array, numpy.ndarray):
                raise TypeError("arrays[{0}] returned a {1} ({2}) instead of a Numpy array".format(repr(name), type(array), repr(array)))
            if dtype is not None and array.dtype != dtype:
                raise TypeError("arrays[{0}] returned an array of type {1} instead of {2}".format(repr(name), array.dtype, dtype))
            if dims is not None and array.shape[1:] != dims:
                raise TypeError("arrays[{0}] returned an array with shape[1:] {1} instead of {2}".format(repr(name), array.shape[1:], dims))
            cache.arraylist[cacheidx] = array
            cache.ptr[cacheidx] = array.ctypes.data
            cache.len[cacheidx] = array.shape[0]
        except:
            return False
        else:
            return True

    def constint(value, bits=64):
        return llvmlite.llvmpy.core.Constant.int(llvmlite.llvmpy.core.Type.int(bits), value)

    def atidx(context, builder, ptr, idx):
        pos = builder.add(ptr, builder.mul(idx, constint(numba.types.intp.bitwidth // 8)))
        posptr = builder.inttoptr(pos, llvmlite.llvmpy.core.Type.pointer(context.get_value_type(numba.types.intp)))
        return numba.targets.arrayobj.load_item(context, builder, numba.types.intp[:], posptr)

    def runtimeerror(context, builder, pyapi, case, message):
        with builder.if_then(case, likely=False):
            exc = pyapi.serialize_object(RuntimeError(message))
            excptr = context.call_conv._get_excinfo_argument(builder.function)
            builder.store(exc, excptr)
            builder.ret(numba.targets.callconv.RETCODE_USEREXC)

    def ensure(context, builder, pyapi, ptr, arrays, name, cache, cacheidx, dtype, dims):
        with builder.if_then(builder.not_(context.is_true(builder, numba.types.int8, ptr)), likely=False):
            getarray_fcn = pyapi.unserialize(pyapi.serialize_object(getarray))
            arrays_obj = builder.inttoptr(arrays, pyapi.pyobj)
            name_obj = pyapi.unserialize(pyapi.serialize_object(name))
            cache_obj = box_cache(context, builder, pyapi, cache)
            cacheidx_obj = pyapi.long_from_long(cacheidx)
            dtype_obj = pyapi.unserialize(pyapi.serialize_object(dtype))
            dims_obj = pyapi.unserialize(pyapi.serialize_object(dims))
            ok_obj = pyapi.call_function_objargs(getarray_fcn, (arrays_obj, name_obj, cache_obj, cacheidx_obj, dtype_obj, dims_obj))
            ok = pyapi.object_istrue(ok_obj)
            pyapi.decref(cacheidx_obj)
            pyapi.decref(dtype_obj)
            pyapi.decref(dims_obj)
            pyapi.decref(ok_obj)
            runtimeerror(context, builder, pyapi, builder.not_(context.is_true(builder, numba.types.intc, ok)), "an exception occurred while trying to load an array")

    def arrayitem(context, builder, ptr, at, dtype):
        pos = builder.add(ptr, builder.mul(at, constint(dtype.itemsize)))
        posptr = builder.inttoptr(pos, llvmlite.llvmpy.core.Type.pointer(context.get_value_type(numba.from_dtype(dtype))))
        return numba.targets.arrayobj.load_item(context, builder, numba.from_dtype(dtype)[:], posptr)

    def castint(builder, val, bits=64):
        if val.type.width < bits:
            return builder.zext(val, llvmlite.llvmpy.core.Type.int(bits))
        elif val.type.width > bits:
            return builder.trunc(val, llvmlite.llvmpy.core.Type.int(bits))
        else:
            return builder.bitcast(val, llvmlite.llvmpy.core.Type.int(bits))

    def generate(context, builder, pyapi, arrays, cache, generator, at):
        cachestruct = numba.cgutils.create_struct_proxy(cachetype)(context, builder, value=cache)

        if isinstance(generator, oamap.generator.MaskedPrimitiveGenerator):
            raise NotImplementedError

        elif isinstance(generator, oamap.generator.PrimitiveGenerator):
            dataidx = constint(generator.dataidx)
            dataptr = atidx(context, builder, cachestruct.ptr, dataidx)
            ensure(context, builder, pyapi, dataptr, arrays, generator.data, cache, dataidx, generator.dtype, generator.dims)

            dataptr = atidx(context, builder, cachestruct.ptr, dataidx)
            datalen = atidx(context, builder, cachestruct.len, dataidx)
            runtimeerror(context, builder, pyapi, builder.icmp_unsigned(">=", at, datalen), "PrimitiveProxy data array index out of range")

            return arrayitem(context, builder, dataptr, at, generator.dtype)

        elif isinstance(generator, oamap.generator.MaskedListGenerator):
            raise NotImplementedError

        elif isinstance(generator, oamap.generator.ListGenerator):
            startsidx = constint(generator.startsidx)
            startsptr = atidx(context, builder, cachestruct.ptr, startsidx)
            ensure(context, builder, pyapi, startsptr, arrays, generator.starts, cache, startsidx, generator.dtype, ())

            stopsidx = constint(generator.stopsidx)
            stopsptr = atidx(context, builder, cachestruct.ptr, stopsidx)
            ensure(context, builder, pyapi, stopsptr, arrays, generator.stops, cache, stopsidx, generator.dtype, ())

            startsptr = atidx(context, builder, cachestruct.ptr, startsidx)
            startslen = atidx(context, builder, cachestruct.len, startsidx)
            runtimeerror(context, builder, pyapi, builder.icmp_unsigned(">=", at, startslen), "ListProxy starts array index out of range")

            stopsptr = atidx(context, builder, cachestruct.ptr, stopsidx)
            stopslen = atidx(context, builder, cachestruct.len, stopsidx)
            runtimeerror(context, builder, pyapi, builder.icmp_unsigned(">=", at, stopslen), "ListProxy stops array index out of range")

            listproxy = numba.cgutils.create_struct_proxy(typeof_generator(generator))(context, builder)
            listproxy.arrays = arrays
            listproxy.cache = cache
            listproxy.start = castint(builder, arrayitem(context, builder, startsptr, at, generator.dtype))
            listproxy.stop = castint(builder, arrayitem(context, builder, stopsptr,  at, generator.dtype))
            listproxy.step = constint(1)
            return listproxy._getvalue()

        elif isinstance(generator, oamap.generator.MaskedUnionGenerator):
            raise NotImplementedError

        elif isinstance(generator, oamap.generator.UnionGenerator):
            raise NotImplementedError

        elif isinstance(generator, oamap.generator.MaskedRecordGenerator):
            raise NotImplementedError

        elif isinstance(generator, oamap.generator.RecordGenerator):
            recordproxy = numba.cgutils.create_struct_proxy(typeof_generator(generator))(context, builder)
            recordproxy.arrays = arrays
            recordproxy.cache = cache
            recordproxy.index = at
            return recordproxy._getvalue()

        elif isinstance(generator, oamap.generator.MaskedTupleGenerator):
            raise NotImplementedError

        elif isinstance(generator, oamap.generator.TupleGenerator):
            raise NotImplementedError

        elif isinstance(generator, oamap.generator.MaskedPointerGenerator):
            raise NotImplementedError

        elif isinstance(generator, oamap.generator.PointerGenerator):
            raise NotImplementedError

        else:
            raise NotImplementedError

    ################################################################ ListProxy

    class ListProxyNumbaType(numba.types.Type):
        def __init__(self, generator):
            self.generator = generator
            super(ListProxyNumbaType, self).__init__(name=self.generator._uniquestr)

    @numba.extending.register_model(ListProxyNumbaType)
    class ListProxyModel(numba.datamodel.models.StructModel):
        def __init__(self, dmm, fe_type):
            members = [("arrays", numba.types.intp),
                       ("cache", cachetype),
                       ("start", numba.types.int64),
                       ("stop", numba.types.int64),
                       ("step", numba.types.int64)]
            super(ListProxyModel, self).__init__(dmm, fe_type, members)

    @numba.typing.templates.infer
    class ListProxyGetItem(numba.typing.templates.AbstractTemplate):
        key = "getitem"
        def generic(self, args, kwds):
            tpe, idx = args
            if isinstance(tpe, ListProxyNumbaType):
                if isinstance(idx, numba.types.Integer):
                    return typeof_generator(tpe.generator.content)(tpe, idx)

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
        return generate(context, builder, pyapi, listproxy.arrays, listproxy.cache, listtpe.generator.content, at)

    @numba.extending.unbox(ListProxyNumbaType)
    def unbox_listproxy(typ, obj, c):
        arrays_obj = c.pyapi.object_getattr_string(obj, "_arrays")
        cache_obj = c.pyapi.object_getattr_string(obj, "_cache")
        start_obj = c.pyapi.object_getattr_string(obj, "_start")
        stop_obj = c.pyapi.object_getattr_string(obj, "_stop")
        step_obj = c.pyapi.object_getattr_string(obj, "_step")

        listproxy = numba.cgutils.create_struct_proxy(typ)(c.context, c.builder)
        listproxy.arrays = c.builder.ptrtoint(arrays_obj, llvmlite.llvmpy.core.Type.int(numba.types.intp.bitwidth))
        listproxy.cache = unbox_cache(cache_obj, c)
        listproxy.start = c.pyapi.long_as_longlong(start_obj)
        listproxy.stop = c.pyapi.long_as_longlong(stop_obj)
        listproxy.step = c.pyapi.long_as_longlong(step_obj)

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
        arrays_obj = c.builder.inttoptr(listproxy.arrays, c.pyapi.pyobj)
        cache_obj = box_cache(c.context, c.builder, c.pyapi, listproxy.cache)
        start_obj = c.pyapi.long_from_longlong(listproxy.start)
        stop_obj = c.pyapi.long_from_longlong(listproxy.stop)
        step_obj = c.pyapi.long_from_longlong(listproxy.step)

        listproxy_cls = c.pyapi.unserialize(c.pyapi.serialize_object(oamap.proxy.ListProxy))
        generator_obj = c.pyapi.unserialize(c.pyapi.serialize_object(typ.generator))

        out = c.pyapi.call_function_objargs(listproxy_cls, (generator_obj, arrays_obj, cache_obj, start_obj, stop_obj, step_obj))

        # c.pyapi.decref(arrays_obj)      # this reference is exported
        # c.pyapi.decref(cache_obj)       # this reference is exported
        c.pyapi.decref(start_obj)
        c.pyapi.decref(stop_obj)
        c.pyapi.decref(step_obj)
        c.pyapi.decref(listproxy_cls)
        # c.pyapi.decref(generator_obj)   # this reference is exported
        return out

    ################################################################ RecordProxy

    class RecordProxyNumbaType(numba.types.Type):
        def __init__(self, generator):
            self.generator = generator
            super(RecordProxyNumbaType, self).__init__(name=self.generator._uniquestr)

    @numba.extending.register_model(RecordProxyNumbaType)
    class RecordProxyModel(numba.datamodel.models.StructModel):
        def __init__(self, dmm, fe_type):
            members = [("arrays", numba.types.intp),
                       ("cache", cachetype),
                       ("index", numba.types.int64)]
            super(RecordProxyModel, self).__init__(dmm, fe_type, members)

    @numba.extending.infer_getattr
    class StructAttribute(numba.typing.templates.AttributeTemplate):
        key = RecordProxyNumbaType
        def generic_resolve(self, typ, attr):
            fieldgenerator = typ.generator.fields.get(attr, None)
            if fieldgenerator is not None:
                return typeof_generator(fieldgenerator)
            else:
                raise AttributeError("{0} object has no attribute {1}".format(repr("Record" if typ.generator.name is None else typ.generator.name), repr(attr)))

    @numba.extending.lower_getattr_generic(RecordProxyNumbaType)
    def recordproxy_getattr(context, builder, typ, val, attr):
        pyapi = context.get_python_api(builder)
        recordproxy = numba.cgutils.create_struct_proxy(typ)(context, builder, value=val)
        return generate(context, builder, pyapi, recordproxy.arrays, recordproxy.cache, typ.generator.fields[attr], recordproxy.index)

    @numba.extending.unbox(RecordProxyNumbaType)
    def unbox_recordproxy(typ, obj, c):
        arrays_obj = c.pyapi.object_getattr_string(obj, "_arrays")
        cache_obj = c.pyapi.object_getattr_string(obj, "_cache")
        index_obj = c.pyapi.object_getattr_string(obj, "_index")

        recordproxy = numba.cgutils.create_struct_proxy(typ)(c.context, c.builder)
        recordproxy.arrays = c.builder.ptrtoint(arrays_obj, llvmlite.llvmpy.core.Type.int(numba.types.intp.bitwidth))
        recordproxy.cache = unbox_cache(cache_obj, c)
        recordproxy.index = c.pyapi.long_as_longlong(index_obj)

        c.pyapi.decref(arrays_obj)
        c.pyapi.decref(cache_obj)
        c.pyapi.decref(index_obj)

        is_error = numba.cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
        return numba.extending.NativeValue(recordproxy._getvalue(), is_error=is_error)

    @numba.extending.box(RecordProxyNumbaType)
    def box_recordproxy(typ, val, c):
        recordproxy = numba.cgutils.create_struct_proxy(typ)(c.context, c.builder, value=val)
        arrays_obj = c.builder.inttoptr(recordproxy.arrays, c.pyapi.pyobj)
        cache_obj = box_cache(c.context, c.builder, c.pyapi, recordproxy.cache)
        index_obj = c.pyapi.long_from_longlong(recordproxy.index)

        recordproxy_cls = c.pyapi.unserialize(c.pyapi.serialize_object(oamap.proxy.RecordProxy))
        generator_obj = c.pyapi.unserialize(c.pyapi.serialize_object(typ.generator))

        out = c.pyapi.call_function_objargs(recordproxy_cls, (generator_obj, arrays_obj, cache_obj, index_obj))

        # c.pyapi.decref(arrays_obj)      # this reference is exported
        # c.pyapi.decref(cache_obj)       # this reference is exported
        c.pyapi.decref(index_obj)
        c.pyapi.decref(recordproxy_cls)
        # c.pyapi.decref(generator_obj)   # this reference is exported
        return out
