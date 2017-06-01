from shredtypes.typesystem.defs import *
from shredtypes.typesystem.lr import *

import numpy

# signed integers
i8   = Primitive(numpy.dtype("int8"),       repr="i8")
i16  = Primitive(numpy.dtype("int16"),      repr="i16")
i32  = Primitive(numpy.dtype("int32"),      repr="i32")
i64  = Primitive(numpy.dtype("int64"),      repr="i64")

# unsigned integers
u8   = Primitive(numpy.dtype("uint8"),      repr="u8")
u16  = Primitive(numpy.dtype("uint16"),     repr="u16")
u32  = Primitive(numpy.dtype("uint32"),     repr="u32")
u64  = Primitive(numpy.dtype("uint64"),     repr="u64")

# floating point numbers
f32  = Primitive(numpy.dtype("float32"),    repr="f32")
f64  = Primitive(numpy.dtype("float64"),    repr="f64")
f128 = Primitive(numpy.dtype("float128"),   repr="f128")

# complex numbers (real float followed by imaginary float)
c64  = Primitive(numpy.dtype("complex64"),  repr="c64")
c128 = Primitive(numpy.dtype("complex128"), repr="c128")
c256 = Primitive(numpy.dtype("complex256"), repr="c256")

# give up the lowest value of the signed range; get a symmetric range
i8nan   = numpy.iinfo(numpy.int8).min
i16nan  = numpy.iinfo(numpy.int16).min
i32nan  = numpy.iinfo(numpy.int32).min
i64nan  = numpy.iinfo(numpy.int64).min

# give up the highest value of the unsigned range; values are close to overflowing anyway
u8nan   = numpy.iinfo(numpy.uint8).max
u16nan  = numpy.iinfo(numpy.uint16).max
u32nan  = numpy.iinfo(numpy.uint32).max
u64nan  = numpy.iinfo(numpy.uint64).max

# IEEE defines a float NaN for us
f32nan  = numpy.float32("nan")
f64nan  = numpy.float64("nan")
f128nan = numpy.float128("nan")
c64nan  = numpy.complex64(numpy.float32("nan") + numpy.float32("nan")*1j)
c128nan = numpy.complex128(numpy.float64("nan") + numpy.float64("nan")*1j)
c256nan = numpy.complex256(numpy.float128("nan") + numpy.float128("nan")*1j)

# nice feature: reinterpret_cast<int NaN> == float NaN (independent of endianness)

assert i32nan == numpy.asscalar(numpy.cast["int32"](numpy.float32("nan")))
assert i64nan == numpy.asscalar(numpy.cast["int64"](numpy.float64("nan")))

def selecttype(min, max, whole, real, nullable):
    from shredtypes.typesystem.defs import nullable as n
    if whole:
        shift = 1 if nullable else 0
        if min >= 0:
            if max <= numpy.iinfo(numpy.uint8).max - shift:
                return n(u8) if nullable else u8
            elif max <= numpy.iinfo(numpy.uint16).max - shift:
                return n(u16) if nullable else u16
            elif max <= numpy.iinfo(numpy.uint32).max - shift:
                return n(u32) if nullable else u32
            elif max <= numpy.iinfo(numpy.uint64).max - shift:
                return n(u64) if nullable else u64
            else:
                return n(f64) if nullable else f64
        else:
            if numpy.iinfo(numpy.int8).min + shift <= min and max <= numpy.iinfo(numpy.int8).max:
                return n(i8) if nullable else i8
            elif numpy.iinfo(numpy.int16).min + shift <= min and max <= numpy.iinfo(numpy.int16).max:
                return n(i16) if nullable else i16
            elif numpy.iinfo(numpy.int32).min + shift <= min and max <= numpy.iinfo(numpy.int32).max:
                return n(i32) if nullable else i32
            elif numpy.iinfo(numpy.int64).min + shift <= min and max <= numpy.iinfo(numpy.int64).max:
                return n(i64) if nullable else i64
            else:
                return n(f64) if nullable else f64
    elif real:
        return n(f64) if nullable else f64
    else:
        return n(c128) if nullable else c128
