from pquiver.typesystem.defs import *

import numpy

# signed integers
int8 = PrimitiveWithRepr(numpy.dtype("int8"), repr="int8")
int16 = PrimitiveWithRepr(numpy.dtype("int16"), repr="int16")
int32 = PrimitiveWithRepr(numpy.dtype("int32"), repr="int32")
int64 = PrimitiveWithRepr(numpy.dtype("int64"), repr="int64")

# unsigned integers
uint8 = PrimitiveWithRepr(numpy.dtype("uint8"), repr="uint8")
uint16 = PrimitiveWithRepr(numpy.dtype("uint16"), repr="uint16")
uint32 = PrimitiveWithRepr(numpy.dtype("uint32"), repr="uint32")
uint64 = PrimitiveWithRepr(numpy.dtype("uint64"), repr="uint64")

# floating point numbers
float32 = PrimitiveWithRepr(numpy.dtype("float32"), repr="float32")
float64 = PrimitiveWithRepr(numpy.dtype("float64"), repr="float64")
float128 = PrimitiveWithRepr(numpy.dtype("float128"), repr="float128")

# complex numbers (real float followed by imaginary float)
complex64 = PrimitiveWithRepr(numpy.dtype("complex64"), repr="complex64")
complex128 = PrimitiveWithRepr(numpy.dtype("complex128"), repr="complex128")
complex256 = PrimitiveWithRepr(numpy.dtype("complex256"), repr="complex256")

def selecttype(min, max, whole, real, nullable):
    from shredtypes.typesystem.defs import nullable as n
    if whole:
        shift = 1 if nullable else 0
        if min >= 0:
            if max <= numpy.iinfo(numpy.uint8).max - shift:
                return n(uint8) if nullable else uint8
            elif max <= numpy.iinfo(numpy.uint16).max - shift:
                return n(uint16) if nullable else uint16
            elif max <= numpy.iinfo(numpy.uint32).max - shift:
                return n(uint32) if nullable else uint32
            elif max <= numpy.iinfo(numpy.uint64).max - shift:
                return n(uint64) if nullable else uint64
            else:
                return n(float64) if nullable else float64
        else:
            if numpy.iinfo(numpy.int8).min + shift <= min and max <= numpy.iinfo(numpy.int8).max:
                return n(int8) if nullable else int8
            elif numpy.iinfo(numpy.int16).min + shift <= min and max <= numpy.iinfo(numpy.int16).max:
                return n(int16) if nullable else int16
            elif numpy.iinfo(numpy.int32).min + shift <= min and max <= numpy.iinfo(numpy.int32).max:
                return n(int32) if nullable else int32
            elif numpy.iinfo(numpy.int64).min + shift <= min and max <= numpy.iinfo(numpy.int64).max:
                return n(int64) if nullable else int64
            else:
                return n(float64) if nullable else float64
    elif real:
        return n(float64) if nullable else float64
    else:
        return n(complex128) if nullable else complex128

def identifytype(primitive):
    if primitive.generic == Primitive.generic and primitive.rtname is None:
        if primitive.dtype == int8.dtype:
            return nullable(int8) if primitive.nullable else int8
        elif primitive.dtype == int16.dtype:
            return nullable(int16) if primitive.nullable else int16
        elif primitive.dtype == int32.dtype:
            return nullable(int32) if primitive.nullable else int32
        elif primitive.dtype == int64.dtype:
            return nullable(int64) if primitive.nullable else int64
        elif primitive.dtype == uint8.dtype:
            return nullable(uint8) if primitive.nullable else uint8
        elif primitive.dtype == uint16.dtype:
            return nullable(uint16) if primitive.nullable else uint16
        elif primitive.dtype == uint32.dtype:
            return nullable(uint32) if primitive.nullable else uint32
        elif primitive.dtype == uint64.dtype:
            return nullable(uint64) if primitive.nullable else uint64
        elif primitive.dtype == float32.dtype:
            return nullable(float32) if primitive.nullable else float32
        elif primitive.dtype == float64.dtype:
            return nullable(float64) if primitive.nullable else float64
        elif primitive.dtype == float128.dtype:
            return nullable(float128) if primitive.nullable else float128
        elif primitive.dtype == complex64.dtype:
            return nullable(complex64) if primitive.nullable else complex64
        elif primitive.dtype == complex128.dtype:
            return nullable(complex128) if primitive.nullable else complex128
        elif primitive.dtype == complex256.dtype:
            return nullable(complex256) if primitive.nullable else complex256
        else:
            return primitive
    else:
        return primitive
