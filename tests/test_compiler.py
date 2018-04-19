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
        if numba is None:
            sys.stderr.write("Numba is not installed: skipping ... ")
        else:
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
        if numba is None:
            sys.stderr.write("Numba is not installed: skipping ... ")
        else:
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
        if numba is None:
            sys.stderr.write("Numba is not installed: skipping ... ")
        else:
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
        if numba is None:
            sys.stderr.write("Numba is not installed: skipping ... ")
        else:
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
        if numba is None:
            sys.stderr.write("Numba is not installed: skipping ... ")
        else:
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
        if numba is None:
            sys.stderr.write("Numba is not installed: skipping ... ")
        else:
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
        if numba is None:
            sys.stderr.write("Numba is not installed: skipping ... ")
        else:
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
        if numba is None:
            sys.stderr.write("Numba is not installed: skipping ... ")
        else:
            @numba.njit
            def doit(x, i):
                return x[i]

            value = List(Primitive(float)).fromdata([0.0, 1.1, 2.2, 3.3, 4.4])

            self.assertEqual(doit(value, 0), 0.0)
            self.assertEqual(doit(value, 1), 1.1)
            self.assertEqual(doit(value, 2), 2.2)
            self.assertEqual(doit(value, 3), 3.3)
            self.assertEqual(doit(value, 4), 4.4)

            self.assertEqual(doit(value, -1), 4.4)
            self.assertEqual(doit(value, -2), 3.3)
            self.assertEqual(doit(value, -3), 2.2)
            self.assertEqual(doit(value, -4), 1.1)
            self.assertEqual(doit(value, -5), 0.0)

            self.assertRaises(IndexError, lambda: doit(value, 5))
            self.assertRaises(IndexError, lambda: doit(value, -6))

    def test_list_getitem_slice(self):
        if numba is None:
            sys.stderr.write("Numba is not installed: skipping ... ")
        else:
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
        if numba is None:
            sys.stderr.write("Numba is not installed: skipping ... ")
        else:
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
        if numba is None:
            sys.stderr.write("Numba is not installed: skipping ... ")
        else:
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
        if numba is None:
            sys.stderr.write("Numba is not installed: skipping ... ")
        else:
            @numba.njit
            def doit(x):
                return len(x)

            value = Tuple([Primitive(int), Primitive(float), Primitive(bool)]).fromdata((1, 2.2, True))
            self.assertEqual(doit(value), 3)

            value = Tuple([Primitive(int)]).fromdata((1,))
            self.assertEqual(doit(value), 1)

    def test_tuple_getitem(self):
        if numba is None:
            sys.stderr.write("Numba is not installed: skipping ... ")
        else:
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

    def test_pointer(self):
        if numba is None:
            sys.stderr.write("Numba is not installed: skipping ... ")
        else:
            linkedlist = Record({"label": Primitive(int)})
            linkedlist["next"] = Pointer(linkedlist)

            value = linkedlist({"object-Flabel-Di8": numpy.array([0, 1, 2], dtype=int), "object-Fnext-P-object": numpy.array([1, 2, 0], dtype=oamap.generator.PointerGenerator.posdtype)})

            @numba.njit
            def closed1(x):
                return x.next.label

            @numba.njit
            def closed2(x):
                return x.next.next.label

            @numba.njit
            def closed3(x):
                return x.next.next.next.label

            @numba.njit
            def closed4(x):
                return x.next.next.next.next.label

            self.assertEqual(closed1(value), 1)
            self.assertEqual(closed2(value), 2)
            self.assertEqual(closed3(value), 0)
            self.assertEqual(closed4(value), 1)

            @numba.njit
            def open1(x):
                return x.next

            @numba.njit
            def open2(x):
                return x.next.next

            @numba.njit
            def open3(x):
                return x.next.next.next

            @numba.njit
            def open4(x):
                return x.next.next.next.next

            self.assertEqual(open1(value).label, 1)
            self.assertEqual(open2(value).label, 2)
            self.assertEqual(open3(value).label, 0)
            self.assertEqual(open4(value).label, 1)

    def test_pointer_masked(self):
        if numba is None:
            sys.stderr.write("Numba is not installed: skipping ... ")
        else:
            @numba.njit
            def doit(x, i):
                return x[i]

            data = [3.3, 2.2, 3.3, None, 1.1, None, 4.4, 1.1, 3.3, None]
            value = List(Pointer(Primitive(float), nullable=True)).fromdata(data, pointer_fromequal=True)

            for i in range(10):
                self.assertEqual(doit(value, i), data[i])

            for i in range(10):
                self.assertEqual(doit(value, i), value[i])

            schema = List(Pointer(Primitive(float, nullable=True), nullable=True))
            value = schema({
                "object-B":       numpy.array([0]),
                "object-L-X-Df8": numpy.array([3.3, 2.2, 4.4]),
                "object-L-X-M":   numpy.array([0, 1, -1, 2]),
                "object-L-P":     numpy.array([0, 1, 0, 2, 3, 2, 0]),
                "object-E":       numpy.array([10]),
                "object-L-M":     numpy.array([ 0, 1, 2, -1, 3, -1, 4, 5, 6, -1])
                })

            data = [3.3, 2.2, 3.3, None, None, None, 4.4, None, 3.3, None]
            for i in range(10):
                self.assertEqual(doit(value, i), data[i])

    def test_boxing_schema(self):
        if numba is None:
            sys.stderr.write("Numba is not installed: skipping ... ")
        else:
            @numba.njit
            def boxing1(x):
                return 3.14

            @numba.njit
            def boxing2(x):
                return x

            @numba.njit
            def boxing3(x):
                return x, x

            schema = List(Record({"one": Primitive(int), "two": ByteString()}))

            boxing1(schema)
            schema2 = boxing2(schema)
            schema3, schema4 = boxing3(schema)

            self.assertEqual(schema, schema2)
            self.assertEqual(schema, schema3)
            self.assertEqual(schema, schema4)

    def test_deriving_schema(self):
        if numba is None:
            sys.stderr.write("Numba is not installed: skipping ... ")
        else:
            @numba.njit
            def nullable(x):
                return x.nullable

            @numba.njit
            def notnullable(x):
                return not x.nullable

            @numba.njit
            def dtype(x):
                return x.dtype

            @numba.njit
            def content(x):
                return x.content

            @numba.njit
            def possibilities(x):
                return x.possibilities

            @numba.njit
            def possibilities_0(x):
                return x.possibilities[0]

            @numba.njit
            def fields(x):
                return x.fields

            @numba.njit
            def fields_one(x):
                return x.fields["one"]

            @numba.njit
            def types(x):
                return x.types

            @numba.njit
            def types_0(x):
                return x.types[0]

            @numba.njit
            def target(x):
                return x.target
            
            self.assertTrue(nullable(Primitive("int")) is False)
            self.assertTrue(nullable(Primitive("int", nullable=True)) is True)
            self.assertTrue(notnullable(Primitive("int")) is True)
            self.assertTrue(notnullable(Primitive("int", nullable=True)) is False)

            self.assertEqual(dtype(Primitive("float")), numpy.dtype("float"))

            self.assertEqual(content(List("int")), Primitive("int"))
            self.assertEqual(possibilities(Union(["int", "float"])), (Primitive("int"), Primitive("float")))
            self.assertEqual(possibilities_0(Union(["int", "float"])), Primitive("int"))
            self.assertEqual(fields(Record({"one": "int", "two": "float"})), {"one": Primitive("int"), "two": Primitive("float")})
            self.assertEqual(fields_one(Record({"one": "int", "two": "float"})), Primitive("int"))
            self.assertEqual(types(Tuple(["int", "float"])), (Primitive("int"), Primitive("float")))
            self.assertEqual(types_0(Tuple(["int", "float"])), Primitive("int"))
            self.assertEqual(target(Pointer("int")), Primitive("int"))

    def test_schema_case(self):
        if numba is None:
            sys.stderr.write("Numba is not installed: skipping ... ")
        else:
            @numba.njit
            def case(x, y):
                return x.case(y)

            @numba.njit
            def case_i(x, y, i):
                return x.case(y[i])

            justint = Primitive("int")
            justfloat = Primitive("float")

            self.assertTrue(case(justint, 999) is True)
            self.assertTrue(case(justint, 3.14) is False)
            self.assertTrue(case(justfloat, 999) is False)
            self.assertTrue(case(justfloat, 3.14) is True)

            listint = List("int")
            listfloat = List("float")

            self.assertTrue(case(listint, listint.fromdata([1, 2, 3])) is True)
            self.assertTrue(case(listfloat, listint.fromdata([1, 2, 3])) is False)

            values = List(Union([justint, justfloat])).fromdata([1, 2, 3.3, 4.4, 5, 6.6, 7.7, 8.8, 9, 10])

            self.assertTrue(case_i(justint, values, 0) is True)
            self.assertTrue(case_i(justint, values, 1) is True)
            self.assertTrue(case_i(justint, values, 2) is False)
            self.assertTrue(case_i(justint, values, 3) is False)
            self.assertTrue(case_i(justint, values, 4) is True)
            self.assertTrue(case_i(justint, values, 5) is False)
            self.assertTrue(case_i(justint, values, 6) is False)
            self.assertTrue(case_i(justint, values, 7) is False)
            self.assertTrue(case_i(justint, values, 8) is True)
            self.assertTrue(case_i(justint, values, 9) is True)

            self.assertTrue(case_i(justfloat, values, 0) is False)
            self.assertTrue(case_i(justfloat, values, 1) is False)
            self.assertTrue(case_i(justfloat, values, 2) is True)
            self.assertTrue(case_i(justfloat, values, 3) is True)
            self.assertTrue(case_i(justfloat, values, 4) is False)
            self.assertTrue(case_i(justfloat, values, 5) is True)
            self.assertTrue(case_i(justfloat, values, 6) is True)
            self.assertTrue(case_i(justfloat, values, 7) is True)
            self.assertTrue(case_i(justfloat, values, 8) is False)
            self.assertTrue(case_i(justfloat, values, 9) is False)

            nullableint = Primitive("int", nullable=True)
            nullablefloat = Primitive("float", nullable=True)

            values = List(Union([nullableint, nullablefloat])).fromdata([1, 2, 3.3, None, None, 6.6, 7.7, None, 9, 10])

            self.assertTrue(case_i(nullableint, values, 0) is True)
            self.assertTrue(case_i(nullableint, values, 1) is True)
            self.assertTrue(case_i(nullableint, values, 2) is False)
            self.assertTrue(case_i(nullableint, values, 3) is True)
            self.assertTrue(case_i(nullableint, values, 4) is True)
            self.assertTrue(case_i(nullableint, values, 5) is False)
            self.assertTrue(case_i(nullableint, values, 6) is False)
            self.assertTrue(case_i(nullableint, values, 7) is True)
            self.assertTrue(case_i(nullableint, values, 8) is True)
            self.assertTrue(case_i(nullableint, values, 9) is True)

            self.assertTrue(case_i(nullablefloat, values, 0) is False)
            self.assertTrue(case_i(nullablefloat, values, 1) is False)
            self.assertTrue(case_i(nullablefloat, values, 2) is True)
            self.assertTrue(case_i(nullablefloat, values, 3) is False)
            self.assertTrue(case_i(nullablefloat, values, 4) is False)
            self.assertTrue(case_i(nullablefloat, values, 5) is True)
            self.assertTrue(case_i(nullablefloat, values, 6) is True)
            self.assertTrue(case_i(nullablefloat, values, 7) is False)
            self.assertTrue(case_i(nullablefloat, values, 8) is False)
            self.assertTrue(case_i(nullablefloat, values, 9) is False)

            values = List(Union([justint, justfloat], nullable=True)).fromdata([1, 2, 3.3, None, None, 6.6, 7.7, None, 9, 10])

            self.assertTrue(case_i(justint, values, 0) is True)
            self.assertTrue(case_i(justint, values, 1) is True)
            self.assertTrue(case_i(justint, values, 2) is False)
            self.assertTrue(case_i(justint, values, 3) is False)
            self.assertTrue(case_i(justint, values, 4) is False)
            self.assertTrue(case_i(justint, values, 5) is False)
            self.assertTrue(case_i(justint, values, 6) is False)
            self.assertTrue(case_i(justint, values, 7) is False)
            self.assertTrue(case_i(justint, values, 8) is True)
            self.assertTrue(case_i(justint, values, 9) is True)

            self.assertTrue(case_i(justfloat, values, 0) is False)
            self.assertTrue(case_i(justfloat, values, 1) is False)
            self.assertTrue(case_i(justfloat, values, 2) is True)
            self.assertTrue(case_i(justfloat, values, 3) is False)
            self.assertTrue(case_i(justfloat, values, 4) is False)
            self.assertTrue(case_i(justfloat, values, 5) is True)
            self.assertTrue(case_i(justfloat, values, 6) is True)
            self.assertTrue(case_i(justfloat, values, 7) is False)
            self.assertTrue(case_i(justfloat, values, 8) is False)
            self.assertTrue(case_i(justfloat, values, 9) is False)

    def test_schema_cast(self):
        if numba is None:
            sys.stderr.write("Numba is not installed: skipping ... ")
        else:
            @numba.njit
            def cast(x, y):
                return x.cast(y)

            @numba.njit
            def cast_i(x, y, i):
                return x.cast(y[i])

            justint = Primitive("int")
            justfloat = Primitive("float")

            self.assertEqual(cast(justint, 999), 999)
            self.assertEqual(cast(justint, 3.14), 3)
            self.assertEqual(cast(justfloat, 999), 999.0)
            self.assertEqual(cast(justfloat, 3.14), 3.14)

            listint = List("int")
            listfloat = List("float")

            self.assertEqual(cast(listint, listint.fromdata([1, 2, 3])), [1, 2, 3])
            self.assertRaises(TypeError, lambda: cast(listfloat, listint.fromdata([1, 2, 3])))

            values = List(Union([justint, justfloat])).fromdata([1, 2, 3.3, 4.4, 5, 6.6, 7.7, 8.8, 9, 10])

            self.assertEqual(cast_i(justint, values, 0), 1)
            self.assertEqual(cast_i(justint, values, 1), 2)
            self.assertRaises(TypeError, lambda: cast_i(justint, values, 2))
            self.assertRaises(TypeError, lambda: cast_i(justint, values, 3))
            self.assertEqual(cast_i(justint, values, 4), 5)
            self.assertRaises(TypeError, lambda: cast_i(justint, values, 5))
            self.assertRaises(TypeError, lambda: cast_i(justint, values, 6))
            self.assertRaises(TypeError, lambda: cast_i(justint, values, 7))
            self.assertEqual(cast_i(justint, values, 8), 9)
            self.assertEqual(cast_i(justint, values, 9), 10)

            self.assertRaises(TypeError, lambda: cast_i(justfloat, values, 0))
            self.assertRaises(TypeError, lambda: cast_i(justfloat, values, 1))
            self.assertEqual(cast_i(justfloat, values, 2), 3.3)
            self.assertEqual(cast_i(justfloat, values, 3), 4.4)
            self.assertRaises(TypeError, lambda: cast_i(justfloat, values, 4))
            self.assertEqual(cast_i(justfloat, values, 5), 6.6)
            self.assertEqual(cast_i(justfloat, values, 6), 7.7)
            self.assertEqual(cast_i(justfloat, values, 7), 8.8)
            self.assertRaises(TypeError, lambda: cast_i(justfloat, values, 8))
            self.assertRaises(TypeError, lambda: cast_i(justfloat, values, 9))

            nullableint = Primitive("int", nullable=True)
            nullablefloat = Primitive("float", nullable=True)

            values = List(Union([nullableint, nullablefloat])).fromdata([1, 2, 3.3, None, None, 6.6, 7.7, None, 9, 10])

            self.assertEqual(cast_i(nullableint, values, 0), 1)
            self.assertEqual(cast_i(nullableint, values, 1), 2)
            self.assertRaises(TypeError, lambda: cast_i(nullableint, values, 2))
            self.assertEqual(cast_i(nullableint, values, 3), None)
            self.assertEqual(cast_i(nullableint, values, 4), None)
            self.assertRaises(TypeError, lambda: cast_i(nullableint, values, 5))
            self.assertRaises(TypeError, lambda: cast_i(nullableint, values, 6))
            self.assertEqual(cast_i(nullableint, values, 7), None)
            self.assertEqual(cast_i(nullableint, values, 8), 9)
            self.assertEqual(cast_i(nullableint, values, 9), 10)

            self.assertRaises(TypeError, lambda: cast_i(nullablefloat, values, 0))
            self.assertRaises(TypeError, lambda: cast_i(nullablefloat, values, 1))
            self.assertEqual(cast_i(nullablefloat, values, 2), 3.3)
            self.assertRaises(TypeError, lambda: cast_i(nullablefloat, values, 3))
            self.assertRaises(TypeError, lambda: cast_i(nullablefloat, values, 4))
            self.assertEqual(cast_i(nullablefloat, values, 5), 6.6)
            self.assertEqual(cast_i(nullablefloat, values, 6), 7.7)
            self.assertRaises(TypeError, lambda: cast_i(nullablefloat, values, 7))
            self.assertRaises(TypeError, lambda: cast_i(nullablefloat, values, 8))
            self.assertRaises(TypeError, lambda: cast_i(nullablefloat, values, 9))

            values = List(Union([justint, justfloat], nullable=True)).fromdata([1, 2, 3.3, None, None, 6.6, 7.7, None, 9, 10])

            self.assertEqual(cast_i(justint, values, 0), 1)
            self.assertEqual(cast_i(justint, values, 1), 2)
            self.assertRaises(TypeError, lambda: cast_i(justint, values, 2))
            self.assertRaises(TypeError, lambda: cast_i(justint, values, 3))
            self.assertRaises(TypeError, lambda: cast_i(justint, values, 4))
            self.assertRaises(TypeError, lambda: cast_i(justint, values, 5))
            self.assertRaises(TypeError, lambda: cast_i(justint, values, 6))
            self.assertRaises(TypeError, lambda: cast_i(justint, values, 7))
            self.assertEqual(cast_i(justint, values, 8), 9)
            self.assertEqual(cast_i(justint, values, 9), 10)

            self.assertRaises(TypeError, lambda: cast_i(justfloat, values, 0))
            self.assertRaises(TypeError, lambda: cast_i(justfloat, values, 1))
            self.assertEqual(cast_i(justfloat, values, 2), 3.3)
            self.assertRaises(TypeError, lambda: cast_i(justfloat, values, 3))
            self.assertRaises(TypeError, lambda: cast_i(justfloat, values, 4))
            self.assertEqual(cast_i(justfloat, values, 5), 6.6)
            self.assertEqual(cast_i(justfloat, values, 6), 7.7)
            self.assertRaises(TypeError, lambda: cast_i(justfloat, values, 7))
            self.assertRaises(TypeError, lambda: cast_i(justfloat, values, 8))
            self.assertRaises(TypeError, lambda: cast_i(justfloat, values, 9))

    def test_union_getattr(self):
        if numba is None:
            sys.stderr.write("Numba is not installed: skipping ... ")
        else:
            @numba.njit
            def one(x, i):
                return x[i].one
            
            value = List(Union([Record({"one": "int"}), Record({"one": "float"})])).fromdata([{"one": 1}, {"one": 2}, {"one": 3.3}, {"one": 4.4}, {"one": 5}])

            self.assertEqual(one(value, 0), 1.0)
            self.assertEqual(one(value, 1), 2.0)
            self.assertEqual(one(value, 2), 3.3)
            self.assertEqual(one(value, 3), 4.4)
            self.assertEqual(one(value, 4), 5.0)

    def test_boxing_optional(self):
        if numba is None:
            sys.stderr.write("Numba is not installed: skipping ... ")
        else:
            @numba.njit
            def boxing(x):
                return x.one

            # primitive

            schema = Record({"one": Primitive("int", nullable=True)})
            value1 = schema.fromdata({"one": 999})
            value2 = schema.fromdata({"one": None})

            self.assertEqual(boxing(value1), 999)
            self.assertEqual(boxing(value2), None)

            # list

            schema = Record({"one": List("int", nullable=True)})
            value1 = schema.fromdata({"one": [1, 2, 3]})
            value2 = schema.fromdata({"one": None})

            self.assertEqual(boxing(value1), [1, 2, 3])
            self.assertEqual(boxing(value2), None)

            # union

            schema = Record({"one": Union(["int", "float"], nullable=True)})
            value1 = schema.fromdata({"one": 999})
            value2 = schema.fromdata({"one": 3.14})
            value3 = schema.fromdata({"one": None})

            self.assertEqual(boxing(value1), 999)
            self.assertEqual(boxing(value2), 3.14)
            self.assertEqual(boxing(value3), None)

            # schema = Record({"one": Union(["int", "float"])})
            # value1 = schema.fromdata({"one": 999})
            # value2 = schema.fromdata({"one": 3.14})
            # for i in range(20):
            #     boxing(value2)
            #     print(sys.getrefcount(value1._generator.fields["one"]), sys.getrefcount(value1._arrays), sys.getrefcount(value1._cache), sys.getrefcount(value1._generator.fields["one"].possibilities), [sys.getrefcount(x) for x in value1._generator.fields["one"].possibilities], [sys.getrefcount(x._generate) for x in value1._generator.fields["one"].possibilities])

            # record

            schema = Record({"one": Record({"x": "int", "y": "float"}, nullable=True)})
            value1 = schema.fromdata({"one": {"x": 999, "y": 3.14}})
            value2 = schema.fromdata({"one": None})

            self.assertEqual(boxing(value1).x, 999)
            self.assertEqual(boxing(value1).y, 3.14)
            self.assertEqual(boxing(value2), None)

            # tuple

            schema = Record({"one": Tuple(["int", "float"], nullable=True)})
            value1 = schema.fromdata({"one": (999, 3.14)})
            value2 = schema.fromdata({"one": None})

            self.assertEqual(boxing(value1), (999, 3.14))
            self.assertEqual(boxing(value2), None)

    def test_reference_equality(self):
        if numba is None:
            sys.stderr.write("Numba is not installed: skipping ... ")
        else:
            @numba.njit
            def oneone(x, y):
                return x.one is y.one

            @numba.njit
            def onetwo(x, y):
                return x.one is y.two

            @numba.njit
            def onenone(x):
                return x.one is None

            @numba.njit
            def not_oneone(x, y):
                return x.one is not y.one

            @numba.njit
            def not_onetwo(x, y):
                return x.one is not y.two

            @numba.njit
            def not_onenone(x):
                return x.one is not None

            # list

            schema = Record({"one": List("int"), "two": List("int")})
            value1 = schema.fromdata({"one": [1, 2, 3], "two": [1, 2, 3]})
            value2 = schema.fromdata({"one": [1, 2, 3], "two": [1, 2, 3]})

            self.assertTrue(oneone(value1, value1) is True)
            self.assertTrue(onetwo(value1, value1) is False)
            self.assertTrue(oneone(value1, value2) is False)
            self.assertTrue(onenone(value1) is False)
            self.assertFalse(not_oneone(value1, value1) is True)
            self.assertFalse(not_onetwo(value1, value1) is False)
            self.assertFalse(not_oneone(value1, value2) is False)
            self.assertFalse(not_onenone(value1) is False)

            schema = Record({"one": List("int", nullable=True)})
            value1 = schema.fromdata({"one": [1, 2, 3]})
            value2 = schema.fromdata({"one": None})

            # self.assertTrue(oneone(value1, value1) is True)    # REPORTME: a bug in Numba!
            self.assertTrue(onenone(value1) is False)
            self.assertTrue(onenone(value2) is True)
            self.assertFalse(not_onenone(value1) is False)
            self.assertFalse(not_onenone(value2) is True)

            # union

            schema = Record({"one": Union(["int", "float"]), "two": Union(["int", "float"])})
            value1 = schema.fromdata({"one": 999, "two": 999})
            value2 = schema.fromdata({"one": 999, "two": 999})

            self.assertTrue(oneone(value1, value1) is True)
            self.assertTrue(onetwo(value1, value1) is False)
            self.assertTrue(oneone(value1, value2) is False)
            self.assertTrue(onenone(value1) is False)
            self.assertFalse(not_oneone(value1, value1) is True)
            self.assertFalse(not_onetwo(value1, value1) is False)
            self.assertFalse(not_oneone(value1, value2) is False)
            self.assertFalse(not_onenone(value1) is False)

            schema = Record({"one": Union(["int", "float"], nullable=True)})
            value1 = schema.fromdata({"one": 999})
            value2 = schema.fromdata({"one": None})

            # self.assertTrue(oneone(value1, value1) is True)    # REPORTME: a bug in Numba!
            self.assertTrue(onenone(value1) is False)
            self.assertTrue(onenone(value2) is True)
            # self.assertFalse(not_oneone(value1, value1) is True)    # REPORTME: a bug in Numba!
            self.assertFalse(not_onenone(value1) is False)
            self.assertFalse(not_onenone(value2) is True)

            # record

            schema = Record({"one": Record({"x": "int", "y": "float"}), "two": Record({"x": "int", "y": "float"})})
            value1 = schema.fromdata({"one": {"x": 999, "y": 3.14}, "two": {"x": 999, "y": 3.14}})
            value2 = schema.fromdata({"one": {"x": 999, "y": 3.14}, "two": {"x": 999, "y": 3.14}})

            self.assertTrue(oneone(value1, value1) is True)
            self.assertTrue(onetwo(value1, value1) is False)
            self.assertTrue(oneone(value1, value2) is False)
            self.assertTrue(onenone(value1) is False)
            self.assertFalse(not_oneone(value1, value1) is True)
            self.assertFalse(not_onetwo(value1, value1) is False)
            self.assertFalse(not_oneone(value1, value2) is False)
            self.assertFalse(not_onenone(value1) is False)

            schema = Record({"one": Record({"x": "int", "y": "float"}, nullable=True)})
            value1 = schema.fromdata({"one": {"x": 999, "y": 3.14}})
            value2 = schema.fromdata({"one": None})

            # self.assertTrue(oneone(value1, value1) is True)    # REPORTME: a bug in Numba!
            self.assertTrue(onenone(value1) is False)
            self.assertTrue(onenone(value2) is True)
            # self.assertFalse(not_oneone(value1, value1) is True)    # REPORTME: a bug in Numba!
            self.assertFalse(not_onenone(value1) is False)
            self.assertFalse(not_onenone(value2) is True)

            # tuple

            schema = Record({"one": Tuple(["int", "float"]), "two": Tuple(["int", "float"])})
            value1 = schema.fromdata({"one": [999, 3.14], "two": [999, 3.14]})
            value2 = schema.fromdata({"one": [999, 3.14], "two": [999, 3.14]})

            self.assertTrue(oneone(value1, value1) is True)
            self.assertTrue(onetwo(value1, value1) is False)
            self.assertTrue(oneone(value1, value2) is False)
            self.assertTrue(onenone(value1) is False)
            self.assertFalse(not_oneone(value1, value1) is True)
            self.assertFalse(not_onetwo(value1, value1) is False)
            self.assertFalse(not_oneone(value1, value2) is False)
            self.assertFalse(not_onenone(value1) is False)

            schema = Record({"one": Tuple(["int", "float"], nullable=True)})
            value1 = schema.fromdata({"one": [999, 3.14]})
            value2 = schema.fromdata({"one": None})

            # self.assertTrue(oneone(value1, value1) is True)    # REPORTME: a bug in Numba!
            self.assertTrue(onenone(value1) is False)
            self.assertTrue(onenone(value2) is True)
            # self.assertFalse(not_oneone(value1, value1) is True)    # REPORTME: a bug in Numba!
            self.assertFalse(not_onenone(value1) is False)
            self.assertFalse(not_onenone(value2) is True)

    def test_value_equality(self):
        if numba is None:
            sys.stderr.write("Numba is not installed: skipping ... ")
        else:
            @numba.njit
            def oneone(x, y):
                return x.one == y.one

            @numba.njit
            def onetwo(x, y):
                return x.one == y.two

            @numba.njit
            def onenone(x):
                return x.one == None

            @numba.njit
            def not_oneone(x, y):
                return x.one != y.one

            @numba.njit
            def not_onetwo(x, y):
                return x.one != y.two

            @numba.njit
            def not_onenone(x):
                return x.one != None

            # lists

            schema = Record({"one": List("int"), "two": List("int")})
            value1 = schema.fromdata({"one": [1, 2, 3], "two": [1, 2, 3]})
            value2 = schema.fromdata({"one": [1, 2, 3], "two": [5, 4, 3]})
            value3 = schema.fromdata({"one": [1, 2, 3], "two": [5, 4, 3, 2, 1]})

            self.assertTrue(oneone(value1, value1) is True)
            self.assertTrue(onetwo(value1, value1) is True)
            self.assertTrue(oneone(value1, value2) is True)
            self.assertTrue(onetwo(value2, value2) is False)
            self.assertTrue(onetwo(value3, value3) is False)
            # self.assertTrue(onenone(value1) is False)    # REPORTME
            self.assertFalse(not_oneone(value1, value1) is True)
            self.assertFalse(not_onetwo(value1, value1) is True)
            self.assertFalse(not_oneone(value1, value2) is True)
            self.assertFalse(not_onetwo(value2, value2) is False)
            self.assertFalse(not_onetwo(value3, value3) is False)
            # self.assertFalse(not_onenone(value1) is False)    # REPORTME

            schema = Record({"one": List("int", nullable=True), "two": List("int")})
            value1 = schema.fromdata({"one": [1, 2, 3], "two": [1, 2, 3]})
            value2 = schema.fromdata({"one": None, "two": [1, 2, 3]})

            # self.assertTrue(oneone(value1, value1) is True)    # REPORTME
            # self.assertTrue(onetwo(value1, value1) is True)    # REPORTME
            # self.assertTrue(oneone(value1, value2) is False)    # REPORTME
            # self.assertTrue(onetwo(value2, value2) is False)    # REPORTME
            # self.assertTrue(onenone(value1) is False)    # REPORTME
            # self.assertTrue(onenone(value2) is False)    # REPORTME
            # self.assertFalse(not_oneone(value1, value1) is True)    # REPORTME
            # self.assertFalse(not_onetwo(value1, value1) is True)    # REPORTME
            # self.assertFalse(not_oneone(value1, value2) is False)    # REPORTME
            # self.assertFalse(not_onetwo(value2, value2) is False)    # REPORTME
            # self.assertFalse(not_onenone(value1) is False)    # REPORTME
            # self.assertFalse(not_onenone(value2) is False)    # REPORTME

            # unions

            schema = Record({"one": Union(["int", "float"]), "two": Union(["int", "float"])})
            value1 = schema.fromdata({"one": 999, "two": 999})
            value2 = schema.fromdata({"one": 999, "two": 3.14})

            self.assertTrue(oneone(value1, value1) is True)
            self.assertTrue(onetwo(value1, value1) is True)
            self.assertTrue(oneone(value1, value2) is True)
            self.assertTrue(onetwo(value2, value2) is False)
            # self.assertTrue(onenone(value1) is False)    # REPORTME
            self.assertFalse(not_oneone(value1, value1) is True)
            self.assertFalse(not_onetwo(value1, value1) is True)
            self.assertFalse(not_oneone(value1, value2) is True)
            self.assertFalse(not_onetwo(value2, value2) is False)
            # self.assertFalse(not_onenone(value1) is False)    # REPORTME

            schema = Record({"one": Union(["int", "float"], nullable=True), "two": Union(["int", "float"])})
            value1 = schema.fromdata({"one": 999, "two": 999})
            value2 = schema.fromdata({"one": None, "two": 999})

            # self.assertTrue(oneone(value1, value1) is True)    # REPORTME
            # self.assertTrue(onetwo(value1, value1) is True)    # REPORTME
            # self.assertTrue(oneone(value1, value2) is False)    # REPORTME
            # self.assertTrue(onetwo(value2, value2) is False)    # REPORTME
            # self.assertTrue(onenone(value1) is False)    # REPORTME
            # self.assertTrue(onenone(value2) is False)    # REPORTME
            # self.assertFalse(not_oneone(value1, value1) is True)    # REPORTME
            # self.assertFalse(not_onetwo(value1, value1) is True)    # REPORTME
            # self.assertFalse(not_oneone(value1, value2) is False)    # REPORTME
            # self.assertFalse(not_onetwo(value2, value2) is False)    # REPORTME
            # self.assertFalse(not_onenone(value1) is False)    # REPORTME
            # self.assertFalse(not_onenone(value2) is False)    # REPORTME

            schema = Record({"one": Union(["int", "float"]), "two": "int"})
            value1 = schema.fromdata({"one": 999, "two": 999})
            value2 = schema.fromdata({"one": 123, "two": 999})
            value3 = schema.fromdata({"one": 3.14, "two": 999})

            self.assertTrue(oneone(value1, value1) is True)
            self.assertTrue(onetwo(value1, value1) is True)
            self.assertTrue(oneone(value1, value2) is False)
            self.assertTrue(onetwo(value2, value2) is False)
            self.assertTrue(oneone(value1, value3) is False)
            self.assertTrue(onetwo(value3, value3) is False)

            # records

            schema = Record({"one": Record({"x": "int", "y": "float"}), "two": Record({"x": "int", "y": "float"})})
            value1 = schema.fromdata({"one": {"x": 999, "y": 3.14}, "two": {"x": 999, "y": 3.14}})
            value2 = schema.fromdata({"one": {"x": 999, "y": 3.14}, "two": {"x": 999, "y": -3.14}})

            value3 = schema.fromdata({"one": {"x": 123, "y": 3.14}, "two": {"x": 999, "y": -3.14}})
            self.assertTrue(oneone(value1, value3) is False)

            self.assertTrue(oneone(value1, value1) is True)
            self.assertTrue(onetwo(value1, value1) is True)
            self.assertTrue(oneone(value1, value2) is True)
            self.assertTrue(onetwo(value2, value2) is False)
            # self.assertTrue(onenone(value1) is False)    # REPORTME
            self.assertFalse(not_oneone(value1, value1) is True)
            self.assertFalse(not_onetwo(value1, value1) is True)
            self.assertFalse(not_oneone(value1, value2) is True)
            self.assertFalse(not_onetwo(value2, value2) is False)
            # self.assertFalse(not_onenone(value1) is False)    # REPORTME

            schema = Record({"one": Record({"x": "int", "y": "float"}, nullable=True), "two": Record({"x": "int", "y": "float"})})
            value1 = schema.fromdata({"one": {"x": 999, "y": 3.14}, "two": {"x": 999, "y": 3.14}})
            value2 = schema.fromdata({"one": None, "two": {"x": 999, "y": 3.14}})

            # self.assertTrue(oneone(value1, value1) is True)    # REPORTME
            # self.assertTrue(onetwo(value1, value1) is True)    # REPORTME
            # self.assertTrue(oneone(value1, value2) is False)    # REPORTME
            # self.assertTrue(onetwo(value2, value2) is False)    # REPORTME
            # self.assertTrue(onenone(value1) is False)    # REPORTME
            # self.assertTrue(onenone(value2) is False)    # REPORTME
            # self.assertFalse(not_oneone(value1, value1) is True)    # REPORTME
            # self.assertFalse(not_onetwo(value1, value1) is True)    # REPORTME
            # self.assertFalse(not_oneone(value1, value2) is False)    # REPORTME
            # self.assertFalse(not_onetwo(value2, value2) is False)    # REPORTME
            # self.assertFalse(not_onenone(value1) is False)    # REPORTME
            # self.assertFalse(not_onenone(value2) is False)    # REPORTME

            # tuples

            schema = Record({"one": Tuple(["int", "float"]), "two": Tuple(["int", "float"])})
            value1 = schema.fromdata({"one": (999, 3.14), "two": (999, 3.14)})
            value2 = schema.fromdata({"one": (999, 3.14), "two": (999, -3.14)})

            self.assertTrue(oneone(value1, value1) is True)
            self.assertTrue(onetwo(value1, value1) is True)
            self.assertTrue(oneone(value1, value2) is True)
            self.assertTrue(onetwo(value2, value2) is False)
            # self.assertTrue(onenone(value1) is False)    # REPORTME
            self.assertFalse(not_oneone(value1, value1) is True)
            self.assertFalse(not_onetwo(value1, value1) is True)
            self.assertFalse(not_oneone(value1, value2) is True)
            self.assertFalse(not_onetwo(value2, value2) is False)
            # self.assertFalse(not_onenone(value1) is False)    # REPORTME

            schema = Record({"one": Tuple(["int", "float"], nullable=True), "two": Tuple(["int", "float"])})
            value1 = schema.fromdata({"one": (999, 3.14), "two": (999, 3.14)})
            value2 = schema.fromdata({"one": None, "two": (999, 3.14)})

            # self.assertTrue(oneone(value1, value1) is True)    # REPORTME
            # self.assertTrue(onetwo(value1, value1) is True)    # REPORTME
            # self.assertTrue(oneone(value1, value2) is False)    # REPORTME
            # self.assertTrue(onetwo(value2, value2) is False)    # REPORTME
            # self.assertTrue(onenone(value1) is False)    # REPORTME
            # self.assertTrue(onenone(value2) is False)    # REPORTME
            # self.assertFalse(not_oneone(value1, value1) is True)    # REPORTME
            # self.assertFalse(not_onetwo(value1, value1) is True)    # REPORTME
            # self.assertFalse(not_oneone(value1, value2) is False)    # REPORTME
            # self.assertFalse(not_onetwo(value2, value2) is False)    # REPORTME
            # self.assertFalse(not_onenone(value1) is False)    # REPORTME
            # self.assertFalse(not_onenone(value2) is False)    # REPORTME

    def test_list_contains(self):
        if numba is None:
            sys.stderr.write("Numba is not installed: skipping ... ")
        else:
            @numba.njit
            def contains(x):
                return x.one in x.two

            schema = Record({"one": Record({"x": "int", "y": "float"}), "two": List(Record({"x": "int", "y": "float"}))})

            value = schema.fromdata({"one": {"x": 3, "y": 3.3}, "two": [{"x": 1, "y": 1.1}, {"x": 2, "y": 2.2}, {"x": 3, "y": 3.3}, {"x": 4, "y": 4.4}, {"x": 5, "y": 5.5}]})
            self.assertTrue(contains(value) is True)

            value = schema.fromdata({"one": {"x": 999, "y": 3.3}, "two": [{"x": 1, "y": 1.1}, {"x": 2, "y": 2.2}, {"x": 3, "y": 3.3}, {"x": 4, "y": 4.4}, {"x": 5, "y": 5.5}]})
            self.assertTrue(contains(value) is False)

            value = schema.fromdata({"one": {"x": 3, "y": 3.14}, "two": [{"x": 1, "y": 1.1}, {"x": 2, "y": 2.2}, {"x": 3, "y": 3.3}, {"x": 4, "y": 4.4}, {"x": 5, "y": 5.5}]})
            self.assertTrue(contains(value) is False)

            schema = Record({"one": Record({"x": "int"}), "two": List(Record({"x": "int", "y": "float"}))})
            value = schema.fromdata({"one": {"x": 3}, "two": [{"x": 1, "y": 1.1}, {"x": 2, "y": 2.2}, {"x": 3, "y": 3.3}, {"x": 4, "y": 4.4}, {"x": 5, "y": 5.5}]})
            self.assertRaises(numba.TypingError, lambda: contains(value))

            schema = Record({"one": "int", "two": List("int")})

            value = schema.fromdata({"one": 3, "two": [1, 2, 3, 4, 5]})
            self.assertTrue(contains(value) is True)

            value = schema.fromdata({"one": 999, "two": [1, 2, 3, 4, 5]})
            self.assertTrue(contains(value) is False)

            schema = Record({"one": "float", "two": List("int")})

            value = schema.fromdata({"one": 3.0, "two": [1, 2, 3, 4, 5]})
            self.assertTrue(contains(value) is True)

            value = schema.fromdata({"one": 123.0, "two": [1, 2, 3, 4, 5]})
            self.assertTrue(contains(value) is False)

            schema = Record({"one": Record({"x": "int", "y": "float"}), "two": List("int")})
            value = schema.fromdata({"one": {"x": 3, "y": 3.3}, "two": [1, 2, 3, 4, 5]})
            self.assertRaises(numba.TypingError, lambda: contains(value))

            schema = Record({"one": "int", "two": List(Record({"x": "int", "y": "float"}))})
            value = schema.fromdata({"one": 3, "two": [{"x": 1, "y": 1.1}, {"x": 2, "y": 2.2}, {"x": 3, "y": 3.3}, {"x": 4, "y": 4.4}, {"x": 5, "y": 5.5}]})
            self.assertRaises(numba.TypingError, lambda: contains(value))
