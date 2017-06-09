import numpy

from pquiver.typesystem.defs import Nullable
from pquiver.typesystem.defs import Primitive
from pquiver.typesystem.defs import PrimitiveWithRepr

# logical
boolean = PrimitiveWithRepr(numpy.dtype("bool"), repr="boolean")

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

def identifytype(primitive):
    if primitive.generic == "Primitive" and primitive.rtname is None:
        if primitive.dtype == boolean.dtype:
            return Nullable(boolean) if primitive.nullable else boolean
        elif primitive.dtype == int8.dtype:
            return Nullable(int8) if primitive.nullable else int8
        elif primitive.dtype == int16.dtype:
            return Nullable(int16) if primitive.nullable else int16
        elif primitive.dtype == int32.dtype:
            return Nullable(int32) if primitive.nullable else int32
        elif primitive.dtype == int64.dtype:
            return Nullable(int64) if primitive.nullable else int64
        elif primitive.dtype == uint8.dtype:
            return Nullable(uint8) if primitive.nullable else uint8
        elif primitive.dtype == uint16.dtype:
            return Nullable(uint16) if primitive.nullable else uint16
        elif primitive.dtype == uint32.dtype:
            return Nullable(uint32) if primitive.nullable else uint32
        elif primitive.dtype == uint64.dtype:
            return Nullable(uint64) if primitive.nullable else uint64
        elif primitive.dtype == float32.dtype:
            return Nullable(float32) if primitive.nullable else float32
        elif primitive.dtype == float64.dtype:
            return Nullable(float64) if primitive.nullable else float64
        elif primitive.dtype == float128.dtype:
            return Nullable(float128) if primitive.nullable else float128
        elif primitive.dtype == complex64.dtype:
            return Nullable(complex64) if primitive.nullable else complex64
        elif primitive.dtype == complex128.dtype:
            return Nullable(complex128) if primitive.nullable else complex128
        elif primitive.dtype == complex256.dtype:
            return Nullable(complex256) if primitive.nullable else complex256
        else:
            return primitive
    else:
        return primitive
