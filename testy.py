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

print x._cache
y = do(x)
print x._cache
print y._cache
print y
print x._cache
print y._cache

for i in range(100):
    print sys.getrefcount(x._cache.data), sys.getrefcount(x._cache.size), sys.getrefcount(x._cache.entercompiled)
    y = do(x)
