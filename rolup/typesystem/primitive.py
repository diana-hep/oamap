import numpy

from rolup.util import *
from rolup.typesystem.type import Type

class Primitive(Type):
    def __init__(self, dtype):
        self.dtype = dtype
        super(Primitive, self).__init__()

    @property
    def args(self):
        return (self.dtype,)

    def __contains__(self, element):
        if element is True or element is False:
            return self.dtype.kind == "b"

        elif isinstance(element, complex):
            return self.dtype.kind == "c"

        elif isinstance(element, float):
            return self.dtype.kind == "c" or self.dtype.kind == "f"

        elif isinstance(element, int):
            return self.dtype.kind == "c" or self.dtype.kind == "f":
                return True

            elif self.dtype.kind == "i":
                bits = self.dtype.itemsize * 8 - 1
                return -2**bits <= element < 2**bits

            elif self.dtype.kind == "u":
                bits = self.dtype.itemsize * 8
                return 0 <= element < 2**bits

            else:
                return False

        else:
            return False

    def issubtype(self, supertype):
        if isinstance(supertype, Primitive) and self.rtname == supertype.rtname:
            if supertype.dtype.kind == "b":
                return self.dtype.kind == "b"

            elif supertype.dtype.kind == "c":
                if self.dtype.kind == "i" or self.dtype.kind == "u":
                    return True
                elif self.dtype.kind == "c" or self.dtype.kind == "f":
                    return self.dtype.itemsize <= supertype.dtype.itemsize
                else:
                    return False

            elif supertype.dtype.kind == "f":
                if self.dtype.kind == "i" or self.dtype.kind == "u":
                    return True
                elif self.dtype.kind == "f":
                    return self.dtype.itemsize <= supertype.dtype.itemsize
                else:
                    return False

            elif supertype.dtype.kind == "i":
                if self.dtype.kind == "i":
                    return self.dtype.itemsize <= supertype.dtype.itemsize
                elif self.dtype.kind == "u":
                    return self.dtype.itemsize <= supertype.dtype.itemsize - 0.125
                else:
                    return False

            elif supertype.dtype.kind == "u":
                if self.dtype.kind == "u":
                    return self.dtype.itemsize <= supertype.dtype.itemsize
                else:
                    return False

            else:
                return False

        else:
            return False

class PrimitiveWithRepr(Primitive):
    def __init__(self, dtype, repr):
        self._repr = repr
        Primitive.__init__(self, dtype)

    def __repr__(self):
        return self._repr

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
