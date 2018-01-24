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

            value = generator.fromdata({"one": 999, "two": 3.14})

            self.assertEqual(value._cache, [None, None, None, None])

            self.assertEqual(one(value), 999)
            self.assertTrue(value._cache[0] is value._arrays["object-Fone-M"])
            self.assertTrue(value._cache[1] is value._arrays["object-Fone-Di8"])

            self.assertEqual(two(value), 3.14)
            self.assertTrue(value._cache[2] is value._arrays["object-Ftwo-M"])
            self.assertTrue(value._cache[3] is value._arrays["object-Ftwo-Df8"])

            value = generator.fromdata({"one": None, "two": None})

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

            value = generator.fromdata({"one": {"uno": 1, "dos": 2.2}, "two": {"tres": True}})

            self.assertTrue(doit1(value) is True)
            self.assertEqual(doit2(value).dos, 2.2)

            value = generator.fromdata({"one": None, "two": {"tres": None}})

            self.assertTrue(doit1(value) is None)
            self.assertTrue(doit2(value) is None)

    def test_list_getitem(self):
        if numba is not None:
            @numba.njit
            def doit(x, i):
                return x[i]

            value = List(Primitive(float)).fromdata([0.0, 1.1, 2.2, 3.3, 4.4])

            self.assertEquals(doit(value, 0), 0.0)
            self.assertEquals(doit(value, 1), 1.1)
            self.assertEquals(doit(value, 2), 2.2)
            self.assertEquals(doit(value, 3), 3.3)
            self.assertEquals(doit(value, 4), 4.4)

            self.assertEquals(doit(value, -1), 4.4)
            self.assertEquals(doit(value, -2), 3.3)
            self.assertEquals(doit(value, -3), 2.2)
            self.assertEquals(doit(value, -4), 1.1)
            self.assertEquals(doit(value, -5), 0.0)

            self.assertRaises(IndexError, lambda: doit(value, 5))
            self.assertRaises(IndexError, lambda: doit(value, -6))

    def test_list_getitem_slice(self):
        if numba is not None:
            @numba.njit
            def low(x, i):
                return x[i:]

            @numba.njit
            def high(x, i):
                return x[:i]

            @numba.njit
            def posstep(x, i):
                return x[1:9:i]

            @numba.njit
            def negstep(x, i):
                return x[9:1:i]

            data = [0.0, 1.1, 2.2, 3.3, 4.4]
            value = List(Primitive(float)).fromdata(data)

            self.assertEqual(low(value, 2), data[2:])
            self.assertEqual(low(value, -2), data[-2:])
            self.assertEqual(low(value, 10), data[10:])
            self.assertEqual(low(value, -10), data[-10:])

            self.assertEqual(high(value, 2), data[:2])
            self.assertEqual(high(value, -2), data[:-2])
            self.assertEqual(high(value, 10), data[:10])
            self.assertEqual(high(value, -10), data[:-10])

            data = [0.0, 1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7, 8.8, 9.9]
            value = List(Primitive(float)).fromdata(data)

            self.assertEqual(posstep(value, 2), data[1:9:2])
            self.assertEqual(posstep(value, -2), data[1:9:-2])
            self.assertEqual(posstep(value, 3), data[1:9:3])
            self.assertEqual(posstep(value, -3), data[1:9:-3])

            self.assertEqual(negstep(value, 2), data[9:1:2])
            self.assertEqual(negstep(value, -2), data[9:1:-2])
            self.assertEqual(negstep(value, 3), data[9:1:3])
            self.assertEqual(negstep(value, -3), data[9:1:-3])

    def test_list_len(self):
        if numba is not None:
            @numba.njit
            def doit(x):
                return len(x)

            schema = List(Primitive(float))
            generator = schema.generator()

            value = generator.fromdata([])
            self.assertEqual(doit(value), 0)

            value = generator.fromdata([3.14])
            self.assertEqual(doit(value), 1)

            value = generator.fromdata([1, 2, 3, 4, 5])
            self.assertEqual(doit(value), 5)

    def test_list_iter(self):
        if numba is not None:
            @numba.njit
            def doit(x):
                out = 0.0
                for xi in x:
                    out += xi
                return out

            schema = List(Primitive(float))
            generator = schema.generator()

            value = generator.fromdata([])
            self.assertEqual(doit(value), 0.0)

            value = generator.fromdata([1.1, 2.2, 3.3])
            self.assertEqual(doit(value), 6.6)

            @numba.njit
            def doit2(outer):
                out = 0.0
                for inner in outer:
                    tmp = 0.0
                    for x in inner:
                        tmp += x
                    if tmp > out:
                        out = tmp
                return out

            schema = List(List(Primitive(float)))
            generator = schema.generator()

            value = generator.fromdata([])
            self.assertEqual(doit2(value), 0.0)

            value = generator.fromdata([[], [], []])
            self.assertEqual(doit2(value), 0.0)

            value = generator.fromdata([[], [-1.1, -2.2], []])
            self.assertEqual(doit2(value), 0.0)

            value = generator.fromdata([[], [-1.1, -2.2], [2.2, 2.2]])
            self.assertEqual(doit2(value), 4.4)

    def test_tuple_len(self):
        if numba is not None:
            @numba.njit
            def doit(x):
                return len(x)

            value = Tuple([Primitive(int), Primitive(float), Primitive(bool)]).fromdata((1, 2.2, True))
            self.assertEqual(doit(value), 3)

            value = Tuple([Primitive(int)]).fromdata((1,))
            self.assertEqual(doit(value), 1)

    def test_tuple_getitem(self):
        if numba is not None:
            @numba.njit
            def doit0(x):
                return x[0]

            @numba.njit
            def doit1(x):
                return x[1]

            @numba.njit
            def doit2(x):
                return x[2]

            value = Tuple([Primitive(int), Primitive(float), Primitive(bool)]).fromdata((1, 2.2, True))
            self.assertEqual(doit0(value), 1)
            self.assertEqual(doit1(value), 2.2)
            self.assertEqual(doit2(value), True)

            value = Tuple([Primitive(int, nullable=True), Primitive(float, nullable=True), Primitive(bool, nullable=True)]).fromdata((1, 2.2, True))
            self.assertEqual(doit0(value), 1)
            self.assertEqual(doit1(value), 2.2)
            self.assertEqual(doit2(value), True)

            value = Tuple([Primitive(int, nullable=True), Primitive(float, nullable=True), Primitive(bool, nullable=True)]).fromdata((None, None, None))
            self.assertTrue(doit0(value) is None)
            self.assertTrue(doit1(value) is None)
            self.assertTrue(doit2(value) is None)

            value = Tuple([Primitive(int), Primitive(float)]).fromdata((1, 2.2))
            self.assertRaises(numba.errors.TypingError, lambda: doit2(value))
