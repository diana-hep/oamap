from rolup.typesystem.type import Type

from rolup.typesystem.record import Record       # R
from rolup.typesystem.option import Option       # O
from rolup.typesystem.list import List           # L
from rolup.typesystem.union import Union         # U
from rolup.typesystem.primitive import Primitive # P

# logical
from rolup.typesystem.primitive import boolean

# signed integers
from rolup.typesystem.primitive import int8
from rolup.typesystem.primitive import int16
from rolup.typesystem.primitive import int32
from rolup.typesystem.primitive import int64

# unsigned integers
from rolup.typesystem.primitive import uint8
from rolup.typesystem.primitive import uint16
from rolup.typesystem.primitive import uint32
from rolup.typesystem.primitive import uint64

# floating point numbers
from rolup.typesystem.primitive import float32
from rolup.typesystem.primitive import float64
from rolup.typesystem.primitive import float128

# complex numbers (real float followed by imaginary float)
from rolup.typesystem.primitive import complex64
from rolup.typesystem.primitive import complex128
from rolup.typesystem.primitive import complex256
