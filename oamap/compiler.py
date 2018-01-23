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
            members = [("generator", numba.types.pyobject),
                       ("arrays", numba.types.pyobject),
                       ("cache", numba.types.pyobject),
                       ("ptr", numba.types.pyobject),
                       ("len", numba.types.pyobject)]
            super(BaggageModel, self).__init__(dmm, fe_type, members)

    def unbox_baggage(context, builder, pyapi, generator_obj, arrays_obj, cache_obj):
        entercompiled_fcn = pyapi.object_getattr_string(generator_obj, "_entercompiled")
        results_obj = pyapi.call_function_objargs(entercompiled_fcn, (arrays_obj, cache_obj))
        with builder.if_then(numba.cgutils.is_not_null(builder, pyapi.err_occurred()), likely=False):
            builder.ret(llvmlite.llvmpy.core.Constant.null(pyapi.pyobj))

        baggage = numba.cgutils.create_struct_proxy(baggagetype)(context, builder)
        baggage.generator = generator_obj
        baggage.arrays = arrays_obj
        baggage.cache = cache_obj
        baggage.ptr = pyapi.tuple_getitem(results_obj, 0)
        baggage.len = pyapi.tuple_getitem(results_obj, 1)

        ptr_obj = pyapi.tuple_getitem(results_obj, 2)
        len_obj = pyapi.tuple_getitem(results_obj, 3)
        ptr = pyapi.long_as_voidptr(ptr_obj)
        len = pyapi.long_as_voidptr(len_obj)

        pyapi.decref(generator_obj)
        pyapi.decref(results_obj)

        return baggage._getvalue(), ptr, len

    def box_baggage(context, builder, pyapi, baggage_val):
        baggage = numba.cgutils.create_struct_proxy(baggagetype)(context, builder, value=baggage_val)

        pyapi.decref(baggage.generator)
        pyapi.decref(baggage.arrays)
        pyapi.decref(baggage.cache)

        return baggage.generator, baggage.arrays, baggage.cache

    ################################################################ general routines for all types

    def typeof_generator(generator):
        if isinstance(generator, oamap.generator.MaskedPrimitiveGenerator):
            raise NotImplementedError

        elif isinstance(generator, oamap.generator.PrimitiveGenerator):
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
            return TupleProxyNumbaType(generator)

        elif isinstance(generator, oamap.generator.MaskedPointerGenerator):
            raise NotImplementedError

        elif isinstance(generator, oamap.generator.PointerGenerator):
            raise NotImplementedError

        else:
            raise AssertionError("unrecognized generator type: {0} ({1})".format(generator.__class__, repr(generator)))

    @numba.extending.typeof_impl.register(oamap.proxy.Proxy)
    def typeof_proxy(val, c):
        return typeof_generator(val._generator)

    ################################################################ ListProxy

    class ListProxyNumbaType(numba.types.Type):
        def __init__(self, generator):
            self.generator = generator
            super(ListProxyNumbaType, self).__init__(name="OAMap-ListProxy-" + self.generator.id)

    @numba.extending.register_model(ListProxyNumbaType)
    class ListProxyModel(numba.datamodel.models.StructModel):
        def __init__(self, dmm, fe_type):
            members = [("baggage", baggagetype),
                       ("ptr", numba.types.voidptr),
                       ("len", numba.types.voidptr),
                       ("whence", numba.types.int64),
                       ("stride", numba.types.int64),
                       ("length", numba.types.int64)]
            super(ListProxyModel, self).__init__(dmm, fe_type, members)

    @numba.extending.unbox(ListProxyNumbaType)
    def unbox_listproxy(typ, obj, c):
        generator_obj = c.pyapi.object_getattr_string(obj, "_generator")
        arrays_obj = c.pyapi.object_getattr_string(obj, "_arrays")
        cache_obj = c.pyapi.object_getattr_string(obj, "_cache")
        whence_obj = c.pyapi.object_getattr_string(obj, "_whence")
        stride_obj = c.pyapi.object_getattr_string(obj, "_stride")
        length_obj = c.pyapi.object_getattr_string(obj, "_length")

        listproxy = numba.cgutils.create_struct_proxy(typ)(c.context, c.builder)
        listproxy.baggage, listproxy.ptr, listproxy.len = unbox_baggage(c.context, c.builder, c.pyapi, generator_obj, arrays_obj, cache_obj)
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
        generator_obj, arrays_obj, cache_obj = box_baggage(c.context, c.builder, c.pyapi, listproxy.baggage)
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
                       ("ptr", numba.types.voidptr),
                       ("len", numba.types.voidptr),
                       ("index", numba.types.int64)]
            super(RecordProxyModel, self).__init__(dmm, fe_type, members)

    @numba.extending.unbox(RecordProxyNumbaType)
    def unbox_recordproxy(typ, obj, c):
        generator_obj = c.pyapi.object_getattr_string(obj, "_generator")
        arrays_obj = c.pyapi.object_getattr_string(obj, "_arrays")
        cache_obj = c.pyapi.object_getattr_string(obj, "_cache")
        index_obj = c.pyapi.object_getattr_string(obj, "_index")

        recordproxy = numba.cgutils.create_struct_proxy(typ)(c.context, c.builder)
        recordproxy.baggage, recordproxy.ptr, recordproxy.len = unbox_baggage(c.context, c.builder, c.pyapi, generator_obj, arrays_obj, cache_obj)
        recordproxy.index = c.pyapi.long_as_longlong(index_obj)

        c.pyapi.decref(index_obj)

        is_error = numba.cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
        return numba.extending.NativeValue(recordproxy._getvalue(), is_error=is_error)

    @numba.extending.box(RecordProxyNumbaType)
    def box_recordproxy(typ, val, c):
        recordproxy = numba.cgutils.create_struct_proxy(typ)(c.context, c.builder, value=val)
        index_obj = c.pyapi.long_from_longlong(recordproxy.index)

        recordproxy_cls = c.pyapi.unserialize(c.pyapi.serialize_object(oamap.proxy.RecordProxy))
        generator_obj, arrays_obj, cache_obj = box_baggage(c.context, c.builder, c.pyapi, recordproxy.baggage)
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
                       ("ptr", numba.types.voidptr),
                       ("len", numba.types.voidptr),
                       ("index", numba.types.int64)]
            super(TupleProxyModel, self).__init__(dmm, fe_type, members)

    @numba.extending.unbox(TupleProxyNumbaType)
    def unbox_tupleproxy(typ, obj, c):
        generator_obj = c.pyapi.object_getattr_string(obj, "_generator")
        arrays_obj = c.pyapi.object_getattr_string(obj, "_arrays")
        cache_obj = c.pyapi.object_getattr_string(obj, "_cache")
        index_obj = c.pyapi.object_getattr_string(obj, "_index")

        tupleproxy = numba.cgutils.create_struct_proxy(typ)(c.context, c.builder)
        tupleproxy.baggage, tupleproxy.ptr, tupleproxy.len = unbox_baggage(c.context, c.builder, c.pyapi, generator_obj, arrays_obj, cache_obj)
        tupleproxy.index = c.pyapi.long_as_longlong(index_obj)

        c.pyapi.decref(index_obj)

        is_error = numba.cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
        return numba.extending.NativeValue(tupleproxy._getvalue(), is_error=is_error)

    @numba.extending.box(TupleProxyNumbaType)
    def box_tupleproxy(typ, val, c):
        tupleproxy = numba.cgutils.create_struct_proxy(typ)(c.context, c.builder, value=val)
        index_obj = c.pyapi.long_from_longlong(tupleproxy.index)

        tupleproxy_cls = c.pyapi.unserialize(c.pyapi.serialize_object(oamap.proxy.TupleProxy))
        generator_obj, arrays_obj, cache_obj = box_baggage(c.context, c.builder, c.pyapi, tupleproxy.baggage)
        out = c.pyapi.call_function_objargs(tupleproxy_cls, (generator_obj, arrays_obj, cache_obj, index_obj))

        c.pyapi.decref(tupleproxy_cls)

        return out
