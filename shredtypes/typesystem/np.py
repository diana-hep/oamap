from typesystem.common import *
from typesystem.lr import *

try:
    import numpy
except ImportError:
    pass
else:
    i8 = Primitive(numpy.dtype("int8"), repr="i8")
    i16 = Primitive(numpy.dtype("int16"), repr="i16")
    i32 = Primitive(numpy.dtype("int32"), repr="i32")
    i64 = Primitive(numpy.dtype("int64"), repr="i64")

    u8 = Primitive(numpy.dtype("uint8"), repr="u8")
    u16 = Primitive(numpy.dtype("uint16"), repr="u16")
    u32 = Primitive(numpy.dtype("uint32"), repr="u32")
    u64 = Primitive(numpy.dtype("uint64"), repr="u64")

    f32 = Primitive(numpy.dtype("float32"), repr="f32")
    f64 = Primitive(numpy.dtype("float64"), repr="f64")
    f128 = Primitive(numpy.dtype("float128"), repr="f128")

    c64 = Primitive(numpy.dtype("complex64"), repr="c64")
    c128 = Primitive(numpy.dtype("complex128"), repr="c128")
    c256 = Primitive(numpy.dtype("complex256"), repr="c256")

    del numpy
