import sys
import time

import numba
import numpy

from oamap.schema import *

schema = List(List(Primitive("f8")))
x = schema({"object-B": numpy.array([0], numpy.int32), "object-E": numpy.array([3], numpy.int32), "object-L-B": numpy.array([0, 3, 3], numpy.int32), "object-L-E": numpy.array([3, 3, 5], numpy.int32), "object-L-L": numpy.array([1.1, 2.2, 3.3, 4.4, 5.5])})

@numba.njit
def do(x, i, j):
    return x[i][j] + 100

for i in range(10):
    print do(x, -1, 0)

print "hello"
print "there"
print "how"
print "are"
print "you"

numpy.zeros(10000000)

print "HELLO"
print "THERE"
print "HOW"
print "ARE"
print "YOU"
