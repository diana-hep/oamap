#!/usr/bin/env python

# Copyright 2017 DIANA-HEP
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
os.chdir("../..")

import numba

from plur.types import *
from plur.python import toarrays

arrays = toarrays("prefix", [1.1, 2.2, 3.3], List(float64))



class Lazy(object): pass

class LazyPrimitive(Lazy):
    _array = arrays["prefix-Ld"]

    def __init__(self, at):
        self._at = at

    def get(self):
        return self._array[self._at]

class LazyPrimitiveType(numba.types.Type):
    def __init__(self):
        super(LazyPrimitiveType, self).__init__(name="LazyPrimitive")

lazyPrimitiveType = LazyPrimitiveType()

@numba.extending.typeof_impl.register(LazyPrimitive)
def typeof_index(val, c):
    return lazyPrimitiveType

@numba.extending.type_callable(LazyPrimitive)
def type_lazyPrimitive(context):
    def typer(at):
        if isinstance(at, numba.types.Integer):
            return lazyPrimitiveType
    return typer

@numba.extending.register_model(LazyPrimitiveType)
class LazyPrimitiveModel(numba.extending.models.StructModel):
    def __init__(self, dmm, fe_type):
        members = [("_at", numba.types.int64)]
        super(LazyPrimitiveModel, self).__init__(dmm, fe_type, members)

numba.extending.make_attribute_wrapper(LazyPrimitiveType, "_at", "_at")

@numba.extending.overload_method(LazyPrimitiveType, "get")
def lazyPrimitiveType_get(lazyPrimitive):
    def get_impl(lazyPrimitive):
        LazyPrimitive.array[lazyPrimitive._at]














class LazyList(Lazy):
    array = arrays["prefix-Lo"]
    sub = LazyPrimitive

    def __init__(self, at):
        self.at = at

    def len(self):
        if self.at == 0:
            return self.array[0]
        else:
            return self.array[self.at] - self.array[self.at - 1]

    def get(self, i):
        if self.at == 0:
            return self.sub(i)
        else:
            return self.sub(self.array[self.at - 1] + i)

class LazyListType(numba.types.Type):
    def __init__(self):
        super(LazyListType, self).__init__(name="LazyList")

lazyListType = LazyListType()
@numba.extending.typeof_impl.register(LazyList)
def typeof_index(val, c):
    return lazyListType






# class Interval(object):
#     def __init__(self, lo, hi):
#         self.lo = lo
#         self.hi = hi

#     def __repr__(self):
#         return "Interval({}, {})".format(self.lo, self.hi)

# class IntervalType(numba.types.Type):
#     def __init__(self):
#         super(IntervalType, self).__init__(name="Interval")

# intervaltype = IntervalType()

# @numba.extending.typeof_impl.register(Interval)
# def typeof_index(val, c):
#     return intervaltype

# @numba.extending.type_callable(Interval)
# def type_interval(context):
#     def typer(lo, hi):
#         if isinstance(lo, numba.types.Float) and isinstance(hi, numba.types.Float):
#             return intervaltype
#     return typer

# @numba.extending.register_model(IntervalType)
# class IntervalModel(numba.extending.models.StructModel):
#     def __init__(self, dmm, fe_type):
#         members = [("lo", numba.types.float64), ("hi", numba.types.float64)]
#         super(IntervalModel, self).__init__(dmm, fe_type, members)

# numba.extending.make_attribute_wrapper(IntervalType, "lo", "lo")
# numba.extending.make_attribute_wrapper(IntervalType, "hi", "hi")

# @numba.extending.lower_builtin(Interval, numba.types.Float, numba.types.Float)
# def impl_interval(context, builder, sig, args):
#     typ = sig.return_type
#     lo, hi = args
#     interval = numba.cgutils.create_struct_proxy(typ)(context, builder)
#     interval.lo = lo
#     interval.hi = hi
#     return interval._getvalue()

# @numba.extending.unbox(IntervalType)
# def unbox_interval(typ, obj, c):
#     lo_obj = c.pyapi.object_getattr_string(obj, "lo")
#     hi_obj = c.pyapi.object_getattr_string(obj, "hi")
#     interval = numba.cgutils.create_struct_proxy(typ)(c.context, c.builder)
#     interval.lo = c.pyapi.float_as_double(lo_obj)
#     interval.hi = c.pyapi.float_as_double(hi_obj)
#     c.pyapi.decref(lo_obj)
#     c.pyapi.decref(hi_obj)
#     is_error = numba.cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
#     return numba.extending.NativeValue(interval._getvalue(), is_error=is_error)

# @numba.extending.box(IntervalType)
# def box_interval(typ, val, c):
#     interval = numba.cgutils.create_struct_proxy(typ)(c.context, c.builder, value=val)
#     lo_obj = c.pyapi.float_from_double(interval.lo)
#     hi_obj = c.pyapi.float_from_double(interval.hi)
#     class_obj = c.pyapi.unserialize(c.pyapi.serialize_object(Interval))
#     res = c.pyapi.call_function_objargs(class_obj, (lo_obj, hi_obj))
#     c.pyapi.decref(lo_obj)
#     c.pyapi.decref(hi_obj)
#     c.pyapi.decref(class_obj)
#     return res

# @numba.njit
# def test1():
#     interval = Interval(4.4, 6.4)
#     return interval.hi
# print(test1())

# @numba.njit
# def test2():
#     interval = Interval(4.4, 6.4)
#     interval.hi = 99.999
#     return interval.hi
# print(test2())

# @numba.extending.overload_method(IntervalType, "onlyget")
# def interval_onlyget(interval, arg):
#     if isinstance(arg, numba.types.Float):
#         def onlyget_impl(interval, arg):
#             return interval.hi + arg
#         return onlyget_impl

# @numba.njit
# def test3():
#     interval = Interval(4.4, 6.4)
#     return interval.onlyget(3.14)
# print(test3())

# @numba.extending.overload_method(IntervalType, "alsoset")
# def interval_alsoset(interval, arg):
#     if isinstance(arg, numba.types.Float):
#         def alsoset_impl(interval, arg):
#             interval.hi = interval.hi + arg
#             return interval.hi
#         return alsoset_impl

# @numba.njit
# def test4():
#     interval = Interval(4.4, 6.4)
#     return interval.alsoset(3.14)
# print(test4())
