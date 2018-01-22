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
    ################################################################ Cache

    ################################################################ general routines for all types

    def typeof_generator(generator):
        if isinstance(generator, oamap.generator.MaskedPrimitiveGenerator):
            raise NotImplementedError

        elif isinstance(generator, oamap.generator.PrimitiveGenerator):
            raise NotImplementedError

        elif isinstance(generator, oamap.generator.MaskedListGenerator):
            raise NotImplementedError

        elif isinstance(generator, oamap.generator.ListGenerator):
            raise NotImplementedError

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

    ################################################################ ListProxy

    ################################################################ RecordProxy

    class RecordProxyNumbaType(numba.types.Type):
        def __init__(self, generator):
            self.generator = generator
            super(RecordProxyNumbaType, self).__init__(name="RecordProxy-" + str(self.generator.id))

    @numba.extending.register_model(RecordProxyNumbaType)
    class RecordProxyModel(numba.datamodel.models.StructModel):
        def __init__(self, dmm, fe_type):
            members = [("arrays", numba.types.pyobject),
                       ("cache", numba.types.pyobject),
                       ("index", numba.types.int64)]
            super(RecordProxyModel, self).__init__(dmm, fe_type, members)

    @numba.extending.unbox(RecordProxyNumbaType)
    def unbox_recordproxy(typ, obj, c):
        arrays_obj = c.pyapi.object_getattr_string(obj, "_arrays")
        cache_obj = c.pyapi.object_getattr_string(obj, "_cache")
        index_obj = c.pyapi.object_getattr_string(obj, "_index")

        recordproxy = numba.cgutils.create_struct_proxy(typ)(c.context, c.builder)
        recordproxy.arrays = arrays_obj
        recordproxy.cache = cache_obj
        recordproxy.index = c.pyapi.long_as_longlong(index_obj)

        c.pyapi.decref(arrays_obj)
        c.pyapi.decref(cache_obj)
        c.pyapi.decref(index_obj)

        is_error = numba.cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
        return numba.extending.NativeValue(recordproxy._getvalue(), is_error=is_error)

    @numba.extending.box(RecordProxyNumbaType)
    def box_recordproxy(typ, val, c):
        recordproxy = numba.cgutils.create_struct_proxy(typ)(c.context, c.builder, value=val)
        arrays_obj = recordproxy.arrays
        cache_obj = recordproxy.cache
        index_obj = c.pyapi.long_from_longlong(recordproxy.index)

        recordproxy_cls = c.pyapi.unserialize(c.pyapi.serialize_object(oamap.proxy.RecordProxy))
        generator_obj = c.pyapi.unserialize(c.pyapi.serialize_object(typ.generator))

        out = c.pyapi.call_function_objargs(recordproxy_cls, (generator_obj, arrays_obj, cache_obj, index_obj))

        c.pyapi.decref(recordproxy_cls)
        return out
