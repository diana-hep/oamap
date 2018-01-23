#!/usr/bin/env python

# Copyright (c) 2017, DIANA-HEP
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# 
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# 
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import unittest
import sys

import numpy

try:
    import numba
except ImportError:
    numba = None

import oamap.compiler
from oamap.schema import *

class TestCompiler(unittest.TestCase):
    def runTest(self):
        pass

    def test_boxing_list(self):
        if numba is not None:
            @numba.njit
            def boxing1(x):
                return 3.14

            @numba.njit
            def boxing2(x):
                return x

            @numba.njit
            def boxing3(x):
                return x, x

            value = List(Primitive(int)).fromdata([1, 2, 3, 4, 5])
            # value._whence = 314
            # value._stride = 315
            # value._length = 316

            for j in range(10):
                for i in range(10):
                    boxing1(value)
                    value2 = boxing2(value)
                    value3, value4 = boxing3(value)

                    for v in value2, value3, value4:
                        self.assertTrue(value._generator is v._generator)
                        self.assertTrue(value._arrays is v._arrays)
                        self.assertTrue(value._cache is v._cache)

                    # print(sys.getrefcount(value), sys.getrefcount(value._generator), sys.getrefcount(value._arrays), sys.getrefcount(value._cache), sys.getrefcount(value._generator._entercompiled), sys.getrefcount(value._whence), sys.getrefcount(value._stride), sys.getrefcount(value._length))

    def test_boxing_record(self):
        if numba is not None:
            @numba.njit
            def boxing1(x):
                return 3.14

            @numba.njit
            def boxing2(x):
                return x

            @numba.njit
            def boxing3(x):
                return x, x

            value = Record({"one": Primitive(int), "two": Primitive(float)}).fromdata({"one": 1, "two": 2.2})
            value._index = 314

            for j in range(10):
                for i in range(10):
                    boxing1(value)
                    value2 = boxing2(value)
                    value3, value4 = boxing3(value)

                    for v in value2, value3, value4:
                        self.assertTrue(value._generator is v._generator)
                        self.assertTrue(value._arrays is v._arrays)
                        self.assertTrue(value._cache is v._cache)

                    # print(sys.getrefcount(value), sys.getrefcount(value._generator), sys.getrefcount(value._arrays), sys.getrefcount(value._cache), sys.getrefcount(value._generator._entercompiled), sys.getrefcount(value._index))

    def test_boxing_tuple(self):
        if numba is not None:
            @numba.njit
            def boxing1(x):
                return 3.14

            @numba.njit
            def boxing2(x):
                return x

            @numba.njit
            def boxing3(x):
                return x, x

            value = Tuple([Primitive(int), Primitive(float)]).fromdata((1, 2.2))
            value._index = 314

            for j in range(10):
                for i in range(10):
                    boxing1(value)
                    value2 = boxing2(value)
                    value3, value4 = boxing3(value)

                    for v in value2, value3, value4:
                        self.assertTrue(value._generator is v._generator)
                        self.assertTrue(value._arrays is v._arrays)
                        self.assertTrue(value._cache is v._cache)

                    # print(sys.getrefcount(value), sys.getrefcount(value._generator), sys.getrefcount(value._arrays), sys.getrefcount(value._cache), sys.getrefcount(value._generator._entercompiled), sys.getrefcount(value._index))
