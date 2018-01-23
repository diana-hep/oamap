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
import oamap.fill
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

            for j in range(3):
                value = List(Primitive(int)).fromdata([1, 2, 3, 4, 5])
                # value._whence = 314
                # value._stride = 315
                # value._length = 316

                for i in range(10):
                    boxing1(value)
                    value2 = boxing2(value)
                    value3, value4 = boxing3(value)

                    for v in value2, value3, value4:
                        self.assertNotEqual(value._generator.id, v._generator.id)
                        self.assertTrue(value._arrays is v._arrays)
                        self.assertTrue(value._cache is v._cache)

                    # print(sys.getrefcount(value), sys.getrefcount(value._generator), sys.getrefcount(value2._generator), sys.getrefcount(value3._generator), sys.getrefcount(value4._generator), sys.getrefcount(value._arrays), sys.getrefcount(value._cache), sys.getrefcount(value._generator._entercompiled), sys.getrefcount(value._whence), sys.getrefcount(value._stride), sys.getrefcount(value._length))

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

            for j in range(3):
                value = Record({"one": Primitive(int), "two": Primitive(float)}).fromdata({"one": 1, "two": 2.2})
                # value._index = 314

                for i in range(10):
                    boxing1(value)
                    value2 = boxing2(value)
                    value3, value4 = boxing3(value)

                    for v in value2, value3, value4:
                        self.assertNotEqual(value._generator.id, v._generator.id)
                        self.assertTrue(value._arrays is v._arrays)
                        self.assertTrue(value._cache is v._cache)

                    # print(sys.getrefcount(value), sys.getrefcount(value._generator), sys.getrefcount(value2._generator), sys.getrefcount(value3._generator), sys.getrefcount(value4._generator), sys.getrefcount(value._arrays), sys.getrefcount(value._cache), sys.getrefcount(value._generator._entercompiled), sys.getrefcount(value._index))

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

            for j in range(3):
                value = Tuple([Primitive(int), Primitive(float)]).fromdata((1, 2.2))
                # value._index = 314

                for i in range(10):
                    boxing1(value)
                    value2 = boxing2(value)
                    value3, value4 = boxing3(value)

                    for v in value2, value3, value4:
                        self.assertNotEqual(value._generator.id, v._generator.id)
                        self.assertTrue(value._arrays is v._arrays)
                        self.assertTrue(value._cache is v._cache)

                    # print(sys.getrefcount(value), sys.getrefcount(value._generator), sys.getrefcount(value2._generator), sys.getrefcount(value3._generator), sys.getrefcount(value4._generator), sys.getrefcount(value._arrays), sys.getrefcount(value._cache), sys.getrefcount(value._generator._entercompiled), sys.getrefcount(value._index))

                value = value2

    def test_record_attr(self):
        if numba is not None:
            @numba.njit
            def doit(x):
                return x.one, x.two

            value = Record({"one": Primitive(int), "two": Primitive(float)}).fromdata({"one": 999, "two": 3.14})

            self.assertTrue(value._cache[0] is None)
            self.assertTrue(value._cache[1] is None)

            self.assertEqual(doit(value), (999, 3.14))

            self.assertTrue(value._cache[0] is value._arrays["object-Fone-Di8"])
            self.assertTrue(value._cache[1] is value._arrays["object-Ftwo-Df8"])

    def test_record_attr_masked(self):
        if numba is not None:
            @numba.njit
            def one(x):
                return x.one

            @numba.njit
            def two(x):
                return x.two

            schema = Record({"one": Primitive(int, nullable=True), "two": Primitive(float, nullable=True)})
            generator = schema.generator()

            value = generator(oamap.fill.fromdata({"one": 999, "two": 3.14}, generator))

            self.assertEqual(value._cache, [None, None, None, None])

            self.assertEqual(one(value), 999)
            self.assertTrue(value._cache[0] is value._arrays["object-Fone-M"])
            self.assertTrue(value._cache[1] is value._arrays["object-Fone-Di8"])

            self.assertEqual(two(value), 3.14)
            self.assertTrue(value._cache[2] is value._arrays["object-Ftwo-M"])
            self.assertTrue(value._cache[3] is value._arrays["object-Ftwo-Df8"])

            value = generator(oamap.fill.fromdata({"one": None, "two": None}, generator))

            self.assertEqual(value._cache, [None, None, None, None])

            self.assertEqual(one(value), None)
            self.assertTrue(value._cache[0] is value._arrays["object-Fone-M"])
            self.assertTrue(value._cache[1] is value._arrays["object-Fone-Di8"])

            self.assertEqual(two(value), None)
            self.assertTrue(value._cache[2] is value._arrays["object-Ftwo-M"])
            self.assertTrue(value._cache[3] is value._arrays["object-Ftwo-Df8"])

    def test_record_attr_attr(self):
        if numba is not None:
            @numba.njit
            def doit(x):
                return x.one.uno, x.one.dos, x.two.tres

            value = Record({"one": Record({"uno": Primitive(int), "dos": Primitive(float)}), "two": Record({"tres": Primitive(bool)})}).fromdata({"one": {"uno": 1, "dos": 2.2}, "two": {"tres": True}})

            self.assertEqual(value._cache, [None, None, None])

            self.assertEqual(doit(value), (1, 2.2, True))

            self.assertTrue(value._cache[0] is value._arrays["object-Fone-Fdos-Df8"])
            self.assertTrue(value._cache[1] is value._arrays["object-Fone-Funo-Di8"])
            self.assertTrue(value._cache[2] is value._arrays["object-Ftwo-Ftres-Db1"])

    def test_record_attr_attr_masked(self):
        if numba is not None:
            @numba.njit
            def doit1(x):
                return x.two.tres

            @numba.njit
            def doit2(x):
                return x.one

            schema = Record({"one": Record({"uno": Primitive(int), "dos": Primitive(float)}, nullable=True), "two": Record({"tres": Primitive(bool, nullable=True)})})
            generator = schema.generator()

            value = generator(oamap.fill.fromdata({"one": {"uno": 1, "dos": 2.2}, "two": {"tres": True}}, generator))

            self.assertTrue(doit1(value) is True)
            self.assertEqual(doit2(value).dos, 2.2)

            value = generator(oamap.fill.fromdata({"one": None, "two": {"tres": None}}, generator))

            self.assertTrue(doit1(value) is None)
            self.assertTrue(doit2(value) is None)

    def test_list_getitem(self):
        if numba is not None:
            @numba.njit
            def doit(x, i):
                return x[i]

            value = List(Primitive(float)).fromdata([0.0, 1.1, 2.2, 3.3, 4.4])

            print doit(value, 0)
            print doit(value, 1)
            print doit(value, 2)
            print doit(value, 3)
            print doit(value, 4)
