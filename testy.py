import sys

import numba
import numpy

from oamap.schema import *

schema = List(Primitive("f8"))
x = schema({"object-B": numpy.array([0], numpy.int32), "object-E": numpy.array([5], numpy.int32), "object-L": numpy.array([1.1, 2.2, 3.3, 4.4, 5.5])})

@numba.njit
def do(x, i):
    return x[i]

print do(x, -1)
print do(x, -2)
print do(x, -3)
print do(x, -4)
print do(x, -5)
