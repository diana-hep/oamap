import sys

import numba
import numpy

from oamap.schema import *

s = List(Primitive("f8"))
t = s()
x = t({"object-B": numpy.array([0], numpy.int32), "object-E": numpy.array([5], numpy.int32), "object-L": numpy.array([1.1, 2.2, 3.3, 4.4, 5.5])})

@numba.njit
def do(x):
    return x

for i in range(10):
    print sys.getrefcount(x.__class__), sys.getrefcount(x._arrays), sys.getrefcount(x._cache), [sys.getrefcount(z) for z in x._cache], sys.getrefcount(x._start), sys.getrefcount(x._stop), sys.getrefcount(x._step), sys.getrefcount(x.__class__._slice)
    y = do(x)

print y

for i in range(10):
    print sys.getrefcount(x.__class__), sys.getrefcount(x._arrays), sys.getrefcount(x._cache), [sys.getrefcount(z) for z in x._cache], sys.getrefcount(x._start), sys.getrefcount(x._stop), sys.getrefcount(x._step), sys.getrefcount(x.__class__._slice)
    y = do(x)

@numba.njit
def do(x):
    return x[0]

print do(x)
