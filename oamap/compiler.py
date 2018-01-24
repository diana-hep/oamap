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

import oamap.generator
import oamap.proxy

try:
    import numba
    import llvmlite.llvmpy.core
except ImportError:
    pass
else:
    ################################################################ Baggage (tracing reference counts to reconstitute Python objects)

    class BaggageType(numba.types.Type):
        def __init__(self):
            super(BaggageType, self).__init__(name="OAMap-Baggage")

    baggagetype = BaggageType()

    @numba.extending.register_model(BaggageType)
    class BaggageModel(numba.datamodel.models.StructModel):
        def __init__(self, dmm, fe_type):
            members = [("arrays", numba.types.pyobject),
                       ("cache", numba.types.pyobject),
                       ("ptrs", numba.types.pyobject),
                       ("lens", numba.types.pyobject)]
            super(BaggageModel, self).__init__(dmm, fe_type, members)

    def unbox_baggage(context, builder, pyapi, generator_obj, arrays_obj, cache_obj):
        entercompiled_fcn = pyapi.object_getattr_string(generator_obj, "_entercompiled")
        results_obj = pyapi.call_function_objargs(entercompiled_fcn, (arrays_obj, cache_obj))
        with builder.if_then(numba.cgutils.is_not_null(builder, pyapi.err_occurred()), likely=False):
            builder.ret(llvmlite.llvmpy.core.Constant.null(pyapi.pyobj))

        baggage = numba.cgutils.create_struct_proxy(baggagetype)(context, builder)
        baggage.arrays = arrays_obj
        baggage.cache = cache_obj
        baggage.ptrs = pyapi.tuple_getitem(results_obj, 0)
        baggage.lens = pyapi.tuple_getitem(results_obj, 1)

        ptrs_obj = pyapi.tuple_getitem(results_obj, 2)
        lens_obj = pyapi.tuple_getitem(results_obj, 3)
        ptrs = pyapi.long_as_voidptr(ptrs_obj)
        lens = pyapi.long_as_voidptr(lens_obj)

        pyapi.decref(generator_obj)
        pyapi.decref(generator_obj)
        pyapi.decref(results_obj)

        return baggage._getvalue(), ptrs, lens

    def box_baggage(context, builder, pyapi, generator, baggage_val):
        generator_obj = pyapi.unserialize(pyapi.serialize_object(generator))
        new_fcn = pyapi.object_getattr_string(generator_obj, "_new")
        results_obj = pyapi.call_function_objargs(new_fcn, ())
        with builder.if_then(numba.cgutils.is_not_null(builder, pyapi.err_occurred()), likely=False):
            builder.ret(llvmlite.llvmpy.core.Constant.null(pyapi.pyobj))

        pyapi.decref(results_obj)

        baggage = numba.cgutils.create_struct_proxy(baggagetype)(context, builder, value=baggage_val)

        pyapi.decref(baggage.arrays)
        pyapi.decref(baggage.cache)

        return generator_obj, baggage.arrays, baggage.cache

    ################################################################ general routines for all types

    @numba.extending.typeof_impl.register(oamap.proxy.Proxy)
    def typeof_proxy(val, c):
        return typeof_generator(val._generator)

    def typeof_generator(generator, checkmasked=True):
        if checkmasked and isinstance(generator, oamap.generator.Masked):
            return numba.types.optional(typeof_generator(generator, checkmasked=False))

        if isinstance(generator, oamap.generator.PrimitiveGenerator):
            if generator.dims == ():
                return numba.from_dtype(generator.dtype)
            else:
                raise NotImplementedError

        elif isinstance(generator, oamap.generator.ListGenerator):
            return ListProxyNumbaType(generator)

        elif isinstance(generator, oamap.generator.UnionGenerator):
            raise NotImplementedError

        elif isinstance(generator, oamap.generator.RecordGenerator):
            return RecordProxyNumbaType(generator)

        elif isinstance(generator, oamap.generator.TupleGenerator):
            return TupleProxyNumbaType(generator)

        elif isinstance(generator, oamap.generator.PointerGenerator):
            raise NotImplementedError

        elif isinstance(generator, oamap.generator.ExtendedGenerator):
            return typeof_generator(generator.generic)

        else:
            raise AssertionError("unrecognized generator type: {0} ({1})".format(generator.__class__, repr(generator)))

    def literal_int(value, itemsize):
        return llvmlite.llvmpy.core.Constant.int(llvmlite.llvmpy.core.Type.int(itemsize * 8), value)

    def literal_int64(value):
        return llvmlite.llvmpy.core.Constant.int(llvmlite.llvmpy.core.Type.int(64), value)

    def literal_intp(value):
        return llvmlite.llvmpy.core.Constant.int(llvmlite.llvmpy.core.Type.int(numba.types.intp.bitwidth), value)

    def arrayitem(context, builder, pyapi, idx, ptrs, lens, at, dtype):
        offset = builder.mul(idx, literal_int64(numba.types.intp.bitwidth // 8))

        ptrposition = builder.inttoptr(
            builder.add(builder.ptrtoint(ptrs, llvmlite.llvmpy.core.Type.int(numba.types.intp.bitwidth)), offset),
            llvmlite.llvmpy.core.Type.pointer(context.get_value_type(numba.types.intp)))

        lenposition = builder.inttoptr(
            builder.add(builder.ptrtoint(lens, llvmlite.llvmpy.core.Type.int(numba.types.intp.bitwidth)), offset),
            llvmlite.llvmpy.core.Type.pointer(context.get_value_type(numba.types.intp)))

        ptr = numba.targets.arrayobj.load_item(context, builder, numba.types.intp[:], ptrposition)
        len = numba.targets.arrayobj.load_item(context, builder, numba.types.intp[:], lenposition)

        raise_exception(context, builder, pyapi, builder.icmp_unsigned(">=", at, len), RuntimeError("array index out of range"))

        finalptr = builder.inttoptr(
            builder.add(ptr, builder.mul(at, literal_int64(dtype.itemsize))),
            llvmlite.llvmpy.core.Type.pointer(context.get_value_type(numba.from_dtype(dtype))))

        return numba.targets.arrayobj.load_item(context, builder, numba.from_dtype(dtype)[:], finalptr)

    def raise_exception(context, builder, pyapi, case, exception):
        with builder.if_then(case, likely=False):
            exc = pyapi.serialize_object(exception)
            excptr = context.call_conv._get_excinfo_argument(builder.function)
            builder.store(exc, excptr)
            builder.ret(numba.targets.callconv.RETCODE_USEREXC)

    def generate_empty(context, builder, pyapi, generator, baggage):
        typ = typeof_generator(generator, checkmasked=False)

        if isinstance(generator, oamap.generator.PrimitiveGenerator):
            if generator.dims == ():
                return llvmlite.llvmpy.core.Constant.null(context.get_value_type(numba.from_dtype(generator.dtype)))
            else:
                raise NotImplementedError

        elif isinstance(generator, oamap.generator.ListGenerator):
            raise NotImplementedError

        elif isinstance(generator, oamap.generator.UnionGenerator):
            raise NotImplementedError

        elif isinstance(generator, oamap.generator.RecordGenerator):
            recordproxy = numba.cgutils.create_struct_proxy(typ)(context, builder)
            recordproxy.baggage = baggage
            recordproxy.ptrs = llvmlite.llvmpy.core.Constant.null(context.get_value_type(numba.types.voidptr))
            recordproxy.lens = llvmlite.llvmpy.core.Constant.null(context.get_value_type(numba.types.voidptr))
            recordproxy.index = literal_int64(0)
            return recordproxy._getvalue()

        elif isinstance(generator, oamap.generator.TupleGenerator):
            raise NotImplementedError

        elif isinstance(generator, oamap.generator.PointerGenerator):
            raise NotImplementedError

        elif isinstance(generator, oamap.generator.ExtendedGenerator):
            return generate(context, builder, pyapi, generator.generic, baggage, ptrs, lens, at)

        else:
            raise AssertionError("unrecognized generator type: {0} ({1})".format(generator.__class__, repr(generator)))

    def generate(context, builder, pyapi, generator, baggage, ptrs, lens, at, checkmasked=True):
        generator._required = True

        if checkmasked and isinstance(generator, oamap.generator.Masked):
            maskidx = literal_int64(generator.maskidx)
            maskvalue = arrayitem(context, builder, pyapi, maskidx, ptrs, lens, at, generator.maskdtype)

            outoptval = context.make_helper(builder, typeof_generator(generator))
            with builder.if_else(builder.icmp_unsigned("==", maskvalue, literal_int(generator.maskedvalue, generator.maskdtype.itemsize))) as (is_not_valid, is_valid):
                with is_valid:
                    outoptval.valid = numba.cgutils.true_bit
                    outoptval.data = generate(context, builder, pyapi, generator, baggage, ptrs, lens, at, checkmasked=False)
                with is_not_valid:
                    outoptval.valid = numba.cgutils.false_bit
                    outoptval.data = generate_empty(context, builder, pyapi, generator, baggage)
            return outoptval._getvalue()

        typ = typeof_generator(generator, checkmasked=False)

        if isinstance(generator, oamap.generator.PrimitiveGenerator):
            if generator.dims == ():
                dataidx = literal_int64(generator.dataidx)
                return arrayitem(context, builder, pyapi, dataidx, ptrs, lens, at, generator.dtype)

            else:
                raise NotImplementedError

        elif isinstance(generator, oamap.generator.ListGenerator):
            raise NotImplementedError

        elif isinstance(generator, oamap.generator.UnionGenerator):
            raise NotImplementedError

        elif isinstance(generator, oamap.generator.RecordGenerator):
            recordproxy = numba.cgutils.create_struct_proxy(typ)(context, builder)
            recordproxy.baggage = baggage
            recordproxy.ptrs = ptrs
            recordproxy.lens = lens
            recordproxy.index = at
            return recordproxy._getvalue()

        elif isinstance(generator, oamap.generator.TupleGenerator):
            raise NotImplementedError

        elif isinstance(generator, oamap.generator.PointerGenerator):
            raise NotImplementedError

        elif isinstance(generator, oamap.generator.ExtendedGenerator):
            return generate(context, builder, pyapi, generator.generic, baggage, ptrs, lens, at)

        else:
            raise AssertionError("unrecognized generator type: {0} ({1})".format(generator.__class__, repr(generator)))

    ################################################################ ListProxy

    class ListProxyNumbaType(numba.types.Type):
        def __init__(self, generator):
            self.generator = generator
            super(ListProxyNumbaType, self).__init__(name="OAMap-ListProxy-" + self.generator.id)

    @numba.extending.register_model(ListProxyNumbaType)
    class ListProxyModel(numba.datamodel.models.StructModel):
        def __init__(self, dmm, fe_type):
            members = [("baggage", baggagetype),
                       ("ptrs", numba.types.voidptr),
                       ("lens", numba.types.voidptr),
                       ("whence", numba.types.int64),
                       ("stride", numba.types.int64),
                       ("length", numba.types.int64)]
            super(ListProxyModel, self).__init__(dmm, fe_type, members)

    @numba.extending.type_callable(len)
    def listproxy_len_type(context):
        def typer(listproxy):
            if isinstance(listproxy, ListProxyNumbaType):
                return numba.types.int64   # verified len type
        return typer

    @numba.extending.lower_builtin(len, ListProxyNumbaType)
    def listproxy_len(context, builder, sig, args):
        listtpe, = sig.args
        listval, = args
        listproxy = numba.cgutils.create_struct_proxy(listtpe)(context, builder, value=listval)
        return listproxy.length

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

        normindex_ptr = numba.cgutils.alloca_once(builder, llvmlite.llvmpy.core.Type.int(64))
        builder.store(indexval, normindex_ptr)
        with builder.if_then(builder.icmp_signed("<", indexval, literal_int64(0))):
            builder.store(builder.add(indexval, listproxy.length), normindex_ptr)
        normindex = builder.load(normindex_ptr)
        
        raise_exception(context,
                        builder,
                        pyapi,
                        builder.or_(builder.icmp_signed("<", normindex, literal_int64(0)),
                                    builder.icmp_signed(">=", normindex, listproxy.length)),
                        IndexError("index out of bounds"))

        at = builder.add(listproxy.whence, builder.mul(listproxy.stride, normindex))
        return generate(context, builder, pyapi, listtpe.generator.content, listproxy.baggage, listproxy.ptrs, listproxy.lens, at)

    @numba.extending.unbox(ListProxyNumbaType)
    def unbox_listproxy(typ, obj, c):
        generator_obj = c.pyapi.object_getattr_string(obj, "_generator")
        arrays_obj = c.pyapi.object_getattr_string(obj, "_arrays")
        cache_obj = c.pyapi.object_getattr_string(obj, "_cache")
        whence_obj = c.pyapi.object_getattr_string(obj, "_whence")
        stride_obj = c.pyapi.object_getattr_string(obj, "_stride")
        length_obj = c.pyapi.object_getattr_string(obj, "_length")

        listproxy = numba.cgutils.create_struct_proxy(typ)(c.context, c.builder)
        listproxy.baggage, listproxy.ptrs, listproxy.lens = unbox_baggage(c.context, c.builder, c.pyapi, generator_obj, arrays_obj, cache_obj)
        listproxy.whence = c.pyapi.long_as_longlong(whence_obj)
        listproxy.stride = c.pyapi.long_as_longlong(stride_obj)
        listproxy.length = c.pyapi.long_as_longlong(length_obj)

        c.pyapi.decref(whence_obj)
        c.pyapi.decref(stride_obj)
        c.pyapi.decref(length_obj)

        is_error = numba.cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
        return numba.extending.NativeValue(listproxy._getvalue(), is_error=is_error)

    @numba.extending.box(ListProxyNumbaType)
    def box_listproxy(typ, val, c):
        listproxy = numba.cgutils.create_struct_proxy(typ)(c.context, c.builder, value=val)
        whence_obj = c.pyapi.long_from_longlong(listproxy.whence)
        stride_obj = c.pyapi.long_from_longlong(listproxy.stride)
        length_obj = c.pyapi.long_from_longlong(listproxy.length)

        listproxy_cls = c.pyapi.unserialize(c.pyapi.serialize_object(oamap.proxy.ListProxy))
        generator_obj, arrays_obj, cache_obj = box_baggage(c.context, c.builder, c.pyapi, typ.generator, listproxy.baggage)
        out = c.pyapi.call_function_objargs(listproxy_cls, (generator_obj, arrays_obj, cache_obj, whence_obj, stride_obj, length_obj))

        c.pyapi.decref(listproxy_cls)

        return out
        
    ################################################################ PartitionedListProxy

    ################################################################ IndexedPartitionedListProxy

    ################################################################ RecordProxy

    class RecordProxyNumbaType(numba.types.Type):
        def __init__(self, generator):
            self.generator = generator
            super(RecordProxyNumbaType, self).__init__(name="OAMap-RecordProxy-" + self.generator.id)

    @numba.extending.register_model(RecordProxyNumbaType)
    class RecordProxyModel(numba.datamodel.models.StructModel):
        def __init__(self, dmm, fe_type):
            members = [("baggage", baggagetype),
                       ("ptrs", numba.types.voidptr),
                       ("lens", numba.types.voidptr),
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
        return generate(context, builder, pyapi, typ.generator.fields[attr], recordproxy.baggage, recordproxy.ptrs, recordproxy.lens, recordproxy.index)

    @numba.extending.unbox(RecordProxyNumbaType)
    def unbox_recordproxy(typ, obj, c):
        generator_obj = c.pyapi.object_getattr_string(obj, "_generator")
        arrays_obj = c.pyapi.object_getattr_string(obj, "_arrays")
        cache_obj = c.pyapi.object_getattr_string(obj, "_cache")
        index_obj = c.pyapi.object_getattr_string(obj, "_index")

        recordproxy = numba.cgutils.create_struct_proxy(typ)(c.context, c.builder)
        recordproxy.baggage, recordproxy.ptrs, recordproxy.lens = unbox_baggage(c.context, c.builder, c.pyapi, generator_obj, arrays_obj, cache_obj)
        recordproxy.index = c.pyapi.long_as_longlong(index_obj)

        c.pyapi.decref(index_obj)

        is_error = numba.cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
        return numba.extending.NativeValue(recordproxy._getvalue(), is_error=is_error)

    @numba.extending.box(RecordProxyNumbaType)
    def box_recordproxy(typ, val, c):
        recordproxy = numba.cgutils.create_struct_proxy(typ)(c.context, c.builder, value=val)
        index_obj = c.pyapi.long_from_longlong(recordproxy.index)

        recordproxy_cls = c.pyapi.unserialize(c.pyapi.serialize_object(oamap.proxy.RecordProxy))
        generator_obj, arrays_obj, cache_obj = box_baggage(c.context, c.builder, c.pyapi, typ.generator, recordproxy.baggage)
        out = c.pyapi.call_function_objargs(recordproxy_cls, (generator_obj, arrays_obj, cache_obj, index_obj))

        c.pyapi.decref(recordproxy_cls)

        return out

    ################################################################ TupleProxy

    class TupleProxyNumbaType(numba.types.Type):
        def __init__(self, generator):
            self.generator = generator
            super(TupleProxyNumbaType, self).__init__(name="OAMap-TupleProxy-" + self.generator.id)

    @numba.extending.register_model(TupleProxyNumbaType)
    class TupleProxyModel(numba.datamodel.models.StructModel):
        def __init__(self, dmm, fe_type):
            members = [("baggage", baggagetype),
                       ("ptrs", numba.types.voidptr),
                       ("lens", numba.types.voidptr),
                       ("index", numba.types.int64)]
            super(TupleProxyModel, self).__init__(dmm, fe_type, members)

    @numba.extending.unbox(TupleProxyNumbaType)
    def unbox_tupleproxy(typ, obj, c):
        generator_obj = c.pyapi.object_getattr_string(obj, "_generator")
        arrays_obj = c.pyapi.object_getattr_string(obj, "_arrays")
        cache_obj = c.pyapi.object_getattr_string(obj, "_cache")
        index_obj = c.pyapi.object_getattr_string(obj, "_index")

        tupleproxy = numba.cgutils.create_struct_proxy(typ)(c.context, c.builder)
        tupleproxy.baggage, tupleproxy.ptrs, tupleproxy.lens = unbox_baggage(c.context, c.builder, c.pyapi, generator_obj, arrays_obj, cache_obj)
        tupleproxy.index = c.pyapi.long_as_longlong(index_obj)

        c.pyapi.decref(index_obj)

        is_error = numba.cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
        return numba.extending.NativeValue(tupleproxy._getvalue(), is_error=is_error)

    @numba.extending.box(TupleProxyNumbaType)
    def box_tupleproxy(typ, val, c):
        tupleproxy = numba.cgutils.create_struct_proxy(typ)(c.context, c.builder, value=val)
        index_obj = c.pyapi.long_from_longlong(tupleproxy.index)

        tupleproxy_cls = c.pyapi.unserialize(c.pyapi.serialize_object(oamap.proxy.TupleProxy))
        generator_obj, arrays_obj, cache_obj = box_baggage(c.context, c.builder, c.pyapi, typ.generator, tupleproxy.baggage)
        out = c.pyapi.call_function_objargs(tupleproxy_cls, (generator_obj, arrays_obj, cache_obj, index_obj))

        c.pyapi.decref(tupleproxy_cls)

        return out
