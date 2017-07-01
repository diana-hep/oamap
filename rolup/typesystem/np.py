import numpy

from rolup.typesystem.defs import Optional
from rolup.typesystem.defs import Primitive
from rolup.typesystem.defs import PrimitiveWithRepr

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
    if isinstance(primitive, Optional):
        return Optional(identifytype(primitive.type))

    elif primitive.rtname is None:
        for tpe in [boolean, int8, int16, int32, int64, uint8, uint16, uint32, uint64, float32, float64, float128, complex64, complex128, complex256]:
            if primitive.dtype == tpe.dtype:
                return tpe

    return primitive
