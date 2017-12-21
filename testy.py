import sys
import time

import numba
import numpy

from oamap.schema import *

# schema = List(List(Primitive("f8")))
# x = schema({"object-B": numpy.array([0], numpy.int32), "object-E": numpy.array([3], numpy.int32), "object-L-B": numpy.array([0, 3, 3], numpy.int32), "object-L-E": numpy.array([3, 3, 5], numpy.int32), "object-L-L": numpy.array([1.1, 2.2, 3.3, 4.4, 5.5])})

# # schema = List(Primitive("f8"))
# # x = schema({"object-B": numpy.array([0], numpy.int32), "object-E": numpy.array([5], numpy.int32), "object-L": numpy.array([1.1, 2.2, 3.3, 4.4, 5.5])})

# @numba.njit
# def do1(x, i):
#     return x[i]

# @numba.njit
# def do2(x, i, j):
#     return x[i][j]

# for i in (0, 2, -1, -3):
#     y = do1(x, i)
#     print y, sys.getrefcount(y._arrays), sys.getrefcount(y._cache)
#     for j in (0, 1, -1, -2):
#         print do2(x, i, j), sys.getrefcount(x._arrays), sys.getrefcount(x._cache)

schema = Record({"a": Primitive("i8"), "b": Primitive("f8")})
x = schema({"object-Fa": numpy.array([999]), "object-Fb": numpy.array([3.14])})
print x.a, x.b

@numba.njit
def do(x):
    return x.a, x.b

print do(x)
