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

import numpy

from rolup.util import *
from rolup.typesystem.type import Type

class Primitive(Type):
    def __init__(self, of):
        if not isinstance(of, numpy.dtype):
            of = numpy.dtype(of)
        self.of = of
        super(Primitive, self).__init__()

    @property
    def args(self):
        return (str(self.of),)

    def __contains__(self, element):
        if element is True or element is False:
            return self.of.kind == "b"

        elif isinstance(element, complex):
            return self.of.kind == "c"

        elif isinstance(element, float):
            return self.of.kind == "c" or self.of.kind == "f"

        elif isinstance(element, (int, long)):
            if self.of.kind == "c" or self.of.kind == "f":
                return True

            elif self.of.kind == "i":
                bits = self.of.itemsize * 8 - 1
                return -2**bits <= element < 2**bits

            elif self.of.kind == "u":
                bits = self.of.itemsize * 8
                return 0 <= element < 2**bits

            else:
                return False

        else:
            return False

    def issubtype(self, supertype):
        if super(Primitive, self).issubtype(supertype):
            return True

        elif (isinstance(supertype, self.__class__) or isinstance(self, supertype.__class__)) and supertype.rtname == self.rtname and supertype.rtargs == self.rtargs:
            if supertype.of.kind == "b":
                return self.of.kind == "b"

            elif supertype.of.kind == "c":
                if self.of.kind == "i" or self.of.kind == "u":
                    return True
                elif self.of.kind == "c" or self.of.kind == "f":
                    return self.of.itemsize <= supertype.of.itemsize
                else:
                    return False

            elif supertype.of.kind == "f":
                if self.of.kind == "i" or self.of.kind == "u":
                    return True
                elif self.of.kind == "f":
                    return self.of.itemsize <= supertype.of.itemsize
                else:
                    return False

            elif supertype.of.kind == "i":
                if self.of.kind == "i":
                    return self.of.itemsize <= supertype.of.itemsize
                elif self.of.kind == "u":
                    return self.of.itemsize <= supertype.of.itemsize - 0.125
                else:
                    return False

            elif supertype.of.kind == "u":
                if self.of.kind == "u":
                    return self.of.itemsize <= supertype.of.itemsize
                else:
                    return False

            else:
                return False

        else:
            return False

    def toJson(self):
        return str(self.of)

class PrimitiveWithRepr(Primitive):
    def __init__(self, of, repr):
        self._repr = repr
        Primitive.__init__(self, of)

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

def withrepr(obj):
    if isinstance(obj, Primitive):
        if obj.of == boolean.of: return boolean

        elif obj.of == int8.of: return int8
        elif obj.of == int16.of: return int16
        elif obj.of == int32.of: return int32
        elif obj.of == int64.of: return int64

        elif obj.of == uint8.of: return uint8
        elif obj.of == uint16.of: return uint16
        elif obj.of == uint32.of: return uint32
        elif obj.of == uint64.of: return uint64

        elif obj.of == float32.of: return float32
        elif obj.of == float64.of: return float64
        elif obj.of == float128.of: return float128

        elif obj.of == complex64.of: return complex64
        elif obj.of == complex128.of: return complex128
        elif obj.of == complex256.of: return complex256

    return obj
