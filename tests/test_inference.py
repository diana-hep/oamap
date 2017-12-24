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
from collections import namedtuple

from oamap.schema import *
from oamap.inference import fromdata
from oamap.inference import fromnames

class TestInference(unittest.TestCase):
    def runTest(self):
        pass

    def checkdata(self, data, schema):
        self.assertEqual(fromdata(data), schema)
        self.assertTrue(data in schema)

    def test_infer_Unknown(self):
        with self.assertRaises(TypeError):
            fromdata(None)

    def test_infer_Primitive(self):
        self.checkdata(False, Primitive("bool_"))
        self.checkdata(True, Primitive("bool_"))
        self.checkdata(0, Primitive("u1"))
        self.checkdata(255, Primitive("u1"))
        self.checkdata(256, Primitive("u2"))
        self.checkdata(65535, Primitive("u2"))
        self.checkdata(65536, Primitive("u4"))
        self.checkdata(4294967295, Primitive("u4"))
        self.checkdata(4294967296, Primitive("u8"))
        self.checkdata(18446744073709551615, Primitive("u8"))
        self.checkdata(18446744073709551616, Primitive("f8"))
        self.checkdata(-1, Primitive("i1"))
        self.checkdata(-128, Primitive("i1"))
        self.checkdata(-129, Primitive("i2"))
        self.checkdata(-32768, Primitive("i2"))
        self.checkdata(-32769, Primitive("i4"))
        self.checkdata(-2147483648, Primitive("i4"))
        self.checkdata(-2147483649, Primitive("i8"))
        self.checkdata(-9223372036854775808, Primitive("i8"))
        self.checkdata(-9223372036854775809, Primitive("f8"))
        self.checkdata(0.0, Primitive("f8"))
        self.checkdata(3.14, Primitive("f8"))
        self.checkdata(float("-inf"), Primitive("f8"))
        self.checkdata(float("inf"), Primitive("f8"))
        self.checkdata(float("nan"), Primitive("f8"))
        self.checkdata(1+1j, Primitive("c16"))

    def test_Primitive_dims(self):        
        self.assertTrue([False, False] in Primitive("bool_", [2]))
        self.assertTrue([False, True] in Primitive("bool_", [2]))
        self.assertTrue([0, 0] in Primitive("u1", [2]))
        self.assertTrue([0, 255] in Primitive("u1", [2]))
        self.assertTrue([0, 256] in Primitive("u2", [2]))
        self.assertTrue([0, 65535] in Primitive("u2", [2]))
        self.assertTrue([0, 65536] in Primitive("u4", [2]))
        self.assertTrue([0, 4294967295] in Primitive("u4", [2]))
        self.assertTrue([0, 4294967296] in Primitive("u8", [2]))
        self.assertTrue([0, 18446744073709551615] in Primitive("u8", [2]))
        self.assertTrue([0, 18446744073709551616] in Primitive("f8", [2]))
        self.assertTrue([0, -1] in Primitive("i1", [2]))
        self.assertTrue([0, -128] in Primitive("i1", [2]))
        self.assertTrue([0, -129] in Primitive("i2", [2]))
        self.assertTrue([0, -32768] in Primitive("i2", [2]))
        self.assertTrue([0, -32769] in Primitive("i4", [2]))
        self.assertTrue([0, -2147483648] in Primitive("i4", [2]))
        self.assertTrue([0, -2147483649] in Primitive("i8", [2]))
        self.assertTrue([0, -9223372036854775808] in Primitive("i8", [2]))
        self.assertTrue([0, -9223372036854775809] in Primitive("f8", [2]))
        self.assertTrue([0, 0.0] in Primitive("f8", [2]))
        self.assertTrue([0, 3.14] in Primitive("f8", [2]))
        self.assertTrue([0, float("-inf")] in Primitive("f8", [2]))
        self.assertTrue([0, float("inf")] in Primitive("f8", [2]))
        self.assertTrue([0, float("nan")] in Primitive("f8", [2]))
        self.assertTrue([0, 1+1j] in Primitive("c16", [2]))

        self.assertTrue([[False, False]] in Primitive("bool_", [1, 2]))
        self.assertTrue([[False, True]] in Primitive("bool_", [1, 2]))
        self.assertTrue([[0, 0]] in Primitive("u1", [1, 2]))
        self.assertTrue([[0, 255]] in Primitive("u1", [1, 2]))
        self.assertTrue([[0, 256]] in Primitive("u2", [1, 2]))
        self.assertTrue([[0, 65535]] in Primitive("u2", [1, 2]))
        self.assertTrue([[0, 65536]] in Primitive("u4", [1, 2]))
        self.assertTrue([[0, 4294967295]] in Primitive("u4", [1, 2]))
        self.assertTrue([[0, 4294967296]] in Primitive("u8", [1, 2]))
        self.assertTrue([[0, 18446744073709551615]] in Primitive("u8", [1, 2]))
        self.assertTrue([[0, 18446744073709551616]] in Primitive("f8", [1, 2]))
        self.assertTrue([[0, -1]] in Primitive("i1", [1, 2]))
        self.assertTrue([[0, -128]] in Primitive("i1", [1, 2]))
        self.assertTrue([[0, -129]] in Primitive("i2", [1, 2]))
        self.assertTrue([[0, -32768]] in Primitive("i2", [1, 2]))
        self.assertTrue([[0, -32769]] in Primitive("i4", [1, 2]))
        self.assertTrue([[0, -2147483648]] in Primitive("i4", [1, 2]))
        self.assertTrue([[0, -2147483649]] in Primitive("i8", [1, 2]))
        self.assertTrue([[0, -9223372036854775808]] in Primitive("i8", [1, 2]))
        self.assertTrue([[0, -9223372036854775809]] in Primitive("f8", [1, 2]))
        self.assertTrue([[0, 0.0]] in Primitive("f8", [1, 2]))
        self.assertTrue([[0, 3.14]] in Primitive("f8", [1, 2]))
        self.assertTrue([[0, float("-inf")]] in Primitive("f8", [1, 2]))
        self.assertTrue([[0, float("inf")]] in Primitive("f8", [1, 2]))
        self.assertTrue([[0, float("nan")]] in Primitive("f8", [1, 2]))
        self.assertTrue([[0, 1+1j]] in Primitive("c16", [1, 2]))

        self.assertTrue([False], [False] in Primitive("bool_", [2, 1]))
        self.assertTrue([False], [True] in Primitive("bool_", [2, 1]))
        self.assertTrue([0], [0] in Primitive("u1", [2, 1]))
        self.assertTrue([0], [255] in Primitive("u1", [2, 1]))
        self.assertTrue([0], [256] in Primitive("u2", [2, 1]))
        self.assertTrue([0], [65535] in Primitive("u2", [2, 1]))
        self.assertTrue([0], [65536] in Primitive("u4", [2, 1]))
        self.assertTrue([0], [4294967295] in Primitive("u4", [2, 1]))
        self.assertTrue([0], [4294967296] in Primitive("u8", [2, 1]))
        self.assertTrue([0], [18446744073709551615] in Primitive("u8", [2, 1]))
        self.assertTrue([0], [18446744073709551616] in Primitive("f8", [2, 1]))
        self.assertTrue([0], [-1] in Primitive("i1", [2, 1]))
        self.assertTrue([0], [-128] in Primitive("i1", [2, 1]))
        self.assertTrue([0], [-129] in Primitive("i2", [2, 1]))
        self.assertTrue([0], [-32768] in Primitive("i2", [2, 1]))
        self.assertTrue([0], [-32769] in Primitive("i4", [2, 1]))
        self.assertTrue([0], [-2147483648] in Primitive("i4", [2, 1]))
        self.assertTrue([0], [-2147483649] in Primitive("i8", [2, 1]))
        self.assertTrue([0], [-9223372036854775808] in Primitive("i8", [2, 1]))
        self.assertTrue([0], [-9223372036854775809] in Primitive("f8", [2, 1]))
        self.assertTrue([0], [0.0] in Primitive("f8", [2, 1]))
        self.assertTrue([0], [3.14] in Primitive("f8", [2, 1]))
        self.assertTrue([0], [float("-inf")] in Primitive("f8", [2, 1]))
        self.assertTrue([0], [float("inf")] in Primitive("f8", [2, 1]))
        self.assertTrue([0], [float("nan")] in Primitive("f8", [2, 1]))
        self.assertTrue([0], [1+1j] in Primitive("c16", [2, 1]))

    def test_infer_List0(self):
        with self.assertRaises(TypeError):
            fromdata([])

        with self.assertRaises(TypeError):
            fromdata([None])

        with self.assertRaises(TypeError):
            fromdata([None, None, None])

    def test_infer_List1(self):
        self.checkdata([False], List(Primitive("bool_")))
        self.checkdata([True], List(Primitive("bool_")))
        self.checkdata([0], List(Primitive("u1")))
        self.checkdata([255], List(Primitive("u1")))
        self.checkdata([256], List(Primitive("u2")))
        self.checkdata([65535], List(Primitive("u2")))
        self.checkdata([65536], List(Primitive("u4")))
        self.checkdata([4294967295], List(Primitive("u4")))
        self.checkdata([4294967296], List(Primitive("u8")))
        self.checkdata([18446744073709551615], List(Primitive("u8")))
        self.checkdata([18446744073709551616], List(Primitive("f8")))
        self.checkdata([-1], List(Primitive("i1")))
        self.checkdata([-128], List(Primitive("i1")))
        self.checkdata([-129], List(Primitive("i2")))
        self.checkdata([-32768], List(Primitive("i2")))
        self.checkdata([-32769], List(Primitive("i4")))
        self.checkdata([-2147483648], List(Primitive("i4")))
        self.checkdata([-2147483649], List(Primitive("i8")))
        self.checkdata([-9223372036854775808], List(Primitive("i8")))
        self.checkdata([-9223372036854775809], List(Primitive("f8")))
        self.checkdata([0.0], List(Primitive("f8")))
        self.checkdata([3.14], List(Primitive("f8")))
        self.checkdata([float("-inf")], List(Primitive("f8")))
        self.checkdata([float("inf")], List(Primitive("f8")))
        self.checkdata([float("nan")], List(Primitive("f8")))
        self.checkdata([1+1j], List(Primitive("c16")))
        
    def test_infer_List2(self):
        self.checkdata([False, False], List(Primitive("bool_")))
        self.checkdata([False, True], List(Primitive("bool_")))
        self.checkdata([0, 0], List(Primitive("u1")))
        self.checkdata([0, 255], List(Primitive("u1")))
        self.checkdata([0, 256], List(Primitive("u2")))
        self.checkdata([0, 65535], List(Primitive("u2")))
        self.checkdata([0, 65536], List(Primitive("u4")))
        self.checkdata([0, 4294967295], List(Primitive("u4")))
        self.checkdata([0, 4294967296], List(Primitive("u8")))
        self.checkdata([0, 18446744073709551615], List(Primitive("u8")))
        self.checkdata([0, 18446744073709551616], List(Primitive("f8")))
        self.checkdata([0, -1], List(Primitive("i1")))
        self.checkdata([0, -128], List(Primitive("i1")))
        self.checkdata([0, -129], List(Primitive("i2")))
        self.checkdata([0, -32768], List(Primitive("i2")))
        self.checkdata([0, -32769], List(Primitive("i4")))
        self.checkdata([0, -2147483648], List(Primitive("i4")))
        self.checkdata([0, -2147483649], List(Primitive("i8")))
        self.checkdata([0, -9223372036854775808], List(Primitive("i8")))
        self.checkdata([0, -9223372036854775809], List(Primitive("f8")))
        self.checkdata([0, 0.0], List(Primitive("f8")))
        self.checkdata([0, 3.14], List(Primitive("f8")))
        self.checkdata([0, float("-inf")], List(Primitive("f8")))
        self.checkdata([0, float("inf")], List(Primitive("f8")))
        self.checkdata([0, float("nan")], List(Primitive("f8")))
        self.checkdata([0, 1+1j], List(Primitive("c16")))
        
    def test_infer_List2_nullable(self):
        self.checkdata([None, False], List(Primitive("bool_", nullable=True)))
        self.checkdata([None, True], List(Primitive("bool_", nullable=True)))
        self.checkdata([None, 0], List(Primitive("u1", nullable=True)))
        self.checkdata([None, 255], List(Primitive("u1", nullable=True)))
        self.checkdata([None, 256], List(Primitive("u2", nullable=True)))
        self.checkdata([None, 65535], List(Primitive("u2", nullable=True)))
        self.checkdata([None, 65536], List(Primitive("u4", nullable=True)))
        self.checkdata([None, 4294967295], List(Primitive("u4", nullable=True)))
        self.checkdata([None, 4294967296], List(Primitive("u8", nullable=True)))
        self.checkdata([None, 18446744073709551615], List(Primitive("u8", nullable=True)))
        self.checkdata([None, 18446744073709551616], List(Primitive("f8", nullable=True)))
        self.checkdata([None, -1], List(Primitive("i1", nullable=True)))
        self.checkdata([None, -128], List(Primitive("i1", nullable=True)))
        self.checkdata([None, -129], List(Primitive("i2", nullable=True)))
        self.checkdata([None, -32768], List(Primitive("i2", nullable=True)))
        self.checkdata([None, -32769], List(Primitive("i4", nullable=True)))
        self.checkdata([None, -2147483648], List(Primitive("i4", nullable=True)))
        self.checkdata([None, -2147483649], List(Primitive("i8", nullable=True)))
        self.checkdata([None, -9223372036854775808], List(Primitive("i8", nullable=True)))
        self.checkdata([None, -9223372036854775809], List(Primitive("f8", nullable=True)))
        self.checkdata([None, 0.0], List(Primitive("f8", nullable=True)))
        self.checkdata([None, 3.14], List(Primitive("f8", nullable=True)))
        self.checkdata([None, float("-inf")], List(Primitive("f8", nullable=True)))
        self.checkdata([None, float("inf")], List(Primitive("f8", nullable=True)))
        self.checkdata([None, float("nan")], List(Primitive("f8", nullable=True)))
        self.checkdata([None, 1+1j], List(Primitive("c16", nullable=True)))

    def test_infer_Union(self):
        self.checkdata([[0], False], List(Union([List(Primitive("u1")), Primitive("bool_")])))
        self.checkdata([[0], True], List(Union([List(Primitive("u1")), Primitive("bool_")])))
        self.checkdata([[0], 0], List(Union([List(Primitive("u1")), Primitive("u1")])))
        self.checkdata([[0], 255], List(Union([List(Primitive("u1")), Primitive("u1")])))
        self.checkdata([[0], 256], List(Union([List(Primitive("u1")), Primitive("u2")])))
        self.checkdata([[0], 65535], List(Union([List(Primitive("u1")), Primitive("u2")])))
        self.checkdata([[0], 65536], List(Union([List(Primitive("u1")), Primitive("u4")])))
        self.checkdata([[0], 4294967295], List(Union([List(Primitive("u1")), Primitive("u4")])))
        self.checkdata([[0], 4294967296], List(Union([List(Primitive("u1")), Primitive("u8")])))
        self.checkdata([[0], 18446744073709551615], List(Union([List(Primitive("u1")), Primitive("u8")])))
        self.checkdata([[0], 18446744073709551616], List(Union([List(Primitive("u1")), Primitive("f8")])))
        self.checkdata([[0], -1], List(Union([List(Primitive("u1")), Primitive("i1")])))
        self.checkdata([[0], -128], List(Union([List(Primitive("u1")), Primitive("i1")])))
        self.checkdata([[0], -129], List(Union([List(Primitive("u1")), Primitive("i2")])))
        self.checkdata([[0], -32768], List(Union([List(Primitive("u1")), Primitive("i2")])))
        self.checkdata([[0], -32769], List(Union([List(Primitive("u1")), Primitive("i4")])))
        self.checkdata([[0], -2147483648], List(Union([List(Primitive("u1")), Primitive("i4")])))
        self.checkdata([[0], -2147483649], List(Union([List(Primitive("u1")), Primitive("i8")])))
        self.checkdata([[0], -9223372036854775808], List(Union([List(Primitive("u1")), Primitive("i8")])))
        self.checkdata([[0], -9223372036854775809], List(Union([List(Primitive("u1")), Primitive("f8")])))
        self.checkdata([[0], 0.0], List(Union([List(Primitive("u1")), Primitive("f8")])))
        self.checkdata([[0], 3.14], List(Union([List(Primitive("u1")), Primitive("f8")])))
        self.checkdata([[0], float("-inf")], List(Union([List(Primitive("u1")), Primitive("f8")])))
        self.checkdata([[0], float("inf")], List(Union([List(Primitive("u1")), Primitive("f8")])))
        self.checkdata([[0], float("nan")], List(Union([List(Primitive("u1")), Primitive("f8")])))
        self.checkdata([[0], 1+1j], List(Union([List(Primitive("u1")), Primitive("c16")])))
        
    def test_infer_Record_dict(self):
        self.checkdata({"one": [0], "two": False}, Record({"one": List(Primitive("u1")), "two": Primitive("bool_")}))
        self.checkdata({"one": [0], "two": True}, Record({"one": List(Primitive("u1")), "two": Primitive("bool_")}))
        self.checkdata({"one": [0], "two": 0}, Record({"one": List(Primitive("u1")), "two": Primitive("u1")}))
        self.checkdata({"one": [0], "two": 255}, Record({"one": List(Primitive("u1")), "two": Primitive("u1")}))
        self.checkdata({"one": [0], "two": 256}, Record({"one": List(Primitive("u1")), "two": Primitive("u2")}))
        self.checkdata({"one": [0], "two": 65535}, Record({"one": List(Primitive("u1")), "two": Primitive("u2")}))
        self.checkdata({"one": [0], "two": 65536}, Record({"one": List(Primitive("u1")), "two": Primitive("u4")}))
        self.checkdata({"one": [0], "two": 4294967295}, Record({"one": List(Primitive("u1")), "two": Primitive("u4")}))
        self.checkdata({"one": [0], "two": 4294967296}, Record({"one": List(Primitive("u1")), "two": Primitive("u8")}))
        self.checkdata({"one": [0], "two": 18446744073709551615}, Record({"one": List(Primitive("u1")), "two": Primitive("u8")}))
        self.checkdata({"one": [0], "two": 18446744073709551616}, Record({"one": List(Primitive("u1")), "two": Primitive("f8")}))
        self.checkdata({"one": [0], "two": -1}, Record({"one": List(Primitive("u1")), "two": Primitive("i1")}))
        self.checkdata({"one": [0], "two": -128}, Record({"one": List(Primitive("u1")), "two": Primitive("i1")}))
        self.checkdata({"one": [0], "two": -129}, Record({"one": List(Primitive("u1")), "two": Primitive("i2")}))
        self.checkdata({"one": [0], "two": -32768}, Record({"one": List(Primitive("u1")), "two": Primitive("i2")}))
        self.checkdata({"one": [0], "two": -32769}, Record({"one": List(Primitive("u1")), "two": Primitive("i4")}))
        self.checkdata({"one": [0], "two": -2147483648}, Record({"one": List(Primitive("u1")), "two": Primitive("i4")}))
        self.checkdata({"one": [0], "two": -2147483649}, Record({"one": List(Primitive("u1")), "two": Primitive("i8")}))
        self.checkdata({"one": [0], "two": -9223372036854775808}, Record({"one": List(Primitive("u1")), "two": Primitive("i8")}))
        self.checkdata({"one": [0], "two": -9223372036854775809}, Record({"one": List(Primitive("u1")), "two": Primitive("f8")}))
        self.checkdata({"one": [0], "two": 0.0}, Record({"one": List(Primitive("u1")), "two": Primitive("f8")}))
        self.checkdata({"one": [0], "two": 3.14}, Record({"one": List(Primitive("u1")), "two": Primitive("f8")}))
        self.checkdata({"one": [0], "two": float("-inf")}, Record({"one": List(Primitive("u1")), "two": Primitive("f8")}))
        self.checkdata({"one": [0], "two": float("inf")}, Record({"one": List(Primitive("u1")), "two": Primitive("f8")}))
        self.checkdata({"one": [0], "two": float("nan")}, Record({"one": List(Primitive("u1")), "two": Primitive("f8")}))
        self.checkdata({"one": [0], "two": 1+1j}, Record({"one": List(Primitive("u1")), "two": Primitive("c16")}))

    def test_infer_Record_namedtuple(self):
        T = namedtuple("T", ["one", "two"])
        self.checkdata(T([0], False), Record({"one": List(Primitive("u1")), "two": Primitive("bool_")}, name="T"))
        self.checkdata(T([0], True), Record({"one": List(Primitive("u1")), "two": Primitive("bool_")}, name="T"))
        self.checkdata(T([0], 0), Record({"one": List(Primitive("u1")), "two": Primitive("u1")}, name="T"))
        self.checkdata(T([0], 255), Record({"one": List(Primitive("u1")), "two": Primitive("u1")}, name="T"))
        self.checkdata(T([0], 256), Record({"one": List(Primitive("u1")), "two": Primitive("u2")}, name="T"))
        self.checkdata(T([0], 65535), Record({"one": List(Primitive("u1")), "two": Primitive("u2")}, name="T"))
        self.checkdata(T([0], 65536), Record({"one": List(Primitive("u1")), "two": Primitive("u4")}, name="T"))
        self.checkdata(T([0], 4294967295), Record({"one": List(Primitive("u1")), "two": Primitive("u4")}, name="T"))
        self.checkdata(T([0], 4294967296), Record({"one": List(Primitive("u1")), "two": Primitive("u8")}, name="T"))
        self.checkdata(T([0], 18446744073709551615), Record({"one": List(Primitive("u1")), "two": Primitive("u8")}, name="T"))
        self.checkdata(T([0], 18446744073709551616), Record({"one": List(Primitive("u1")), "two": Primitive("f8")}, name="T"))
        self.checkdata(T([0], -1), Record({"one": List(Primitive("u1")), "two": Primitive("i1")}, name="T"))
        self.checkdata(T([0], -128), Record({"one": List(Primitive("u1")), "two": Primitive("i1")}, name="T"))
        self.checkdata(T([0], -129), Record({"one": List(Primitive("u1")), "two": Primitive("i2")}, name="T"))
        self.checkdata(T([0], -32768), Record({"one": List(Primitive("u1")), "two": Primitive("i2")}, name="T"))
        self.checkdata(T([0], -32769), Record({"one": List(Primitive("u1")), "two": Primitive("i4")}, name="T"))
        self.checkdata(T([0], -2147483648), Record({"one": List(Primitive("u1")), "two": Primitive("i4")}, name="T"))
        self.checkdata(T([0], -2147483649), Record({"one": List(Primitive("u1")), "two": Primitive("i8")}, name="T"))
        self.checkdata(T([0], -9223372036854775808), Record({"one": List(Primitive("u1")), "two": Primitive("i8")}, name="T"))
        self.checkdata(T([0], -9223372036854775809), Record({"one": List(Primitive("u1")), "two": Primitive("f8")}, name="T"))
        self.checkdata(T([0], 0.0), Record({"one": List(Primitive("u1")), "two": Primitive("f8")}, name="T"))
        self.checkdata(T([0], 3.14), Record({"one": List(Primitive("u1")), "two": Primitive("f8")}, name="T"))
        self.checkdata(T([0], float("-inf")), Record({"one": List(Primitive("u1")), "two": Primitive("f8")}, name="T"))
        self.checkdata(T([0], float("inf")), Record({"one": List(Primitive("u1")), "two": Primitive("f8")}, name="T"))
        self.checkdata(T([0], float("nan")), Record({"one": List(Primitive("u1")), "two": Primitive("f8")}, name="T"))
        self.checkdata(T([0], 1+1j), Record({"one": List(Primitive("u1")), "two": Primitive("c16")}, name="T"))
        
    def test_infer_Record_class(self):
        class T(object):
            def __init__(self, one, two):
                self.one = one
                self.two = two
        self.checkdata(T([0], False), Record({"one": List(Primitive("u1")), "two": Primitive("bool_")}, name="T"))
        self.checkdata(T([0], True), Record({"one": List(Primitive("u1")), "two": Primitive("bool_")}, name="T"))
        self.checkdata(T([0], 0), Record({"one": List(Primitive("u1")), "two": Primitive("u1")}, name="T"))
        self.checkdata(T([0], 255), Record({"one": List(Primitive("u1")), "two": Primitive("u1")}, name="T"))
        self.checkdata(T([0], 256), Record({"one": List(Primitive("u1")), "two": Primitive("u2")}, name="T"))
        self.checkdata(T([0], 65535), Record({"one": List(Primitive("u1")), "two": Primitive("u2")}, name="T"))
        self.checkdata(T([0], 65536), Record({"one": List(Primitive("u1")), "two": Primitive("u4")}, name="T"))
        self.checkdata(T([0], 4294967295), Record({"one": List(Primitive("u1")), "two": Primitive("u4")}, name="T"))
        self.checkdata(T([0], 4294967296), Record({"one": List(Primitive("u1")), "two": Primitive("u8")}, name="T"))
        self.checkdata(T([0], 18446744073709551615), Record({"one": List(Primitive("u1")), "two": Primitive("u8")}, name="T"))
        self.checkdata(T([0], 18446744073709551616), Record({"one": List(Primitive("u1")), "two": Primitive("f8")}, name="T"))
        self.checkdata(T([0], -1), Record({"one": List(Primitive("u1")), "two": Primitive("i1")}, name="T"))
        self.checkdata(T([0], -128), Record({"one": List(Primitive("u1")), "two": Primitive("i1")}, name="T"))
        self.checkdata(T([0], -129), Record({"one": List(Primitive("u1")), "two": Primitive("i2")}, name="T"))
        self.checkdata(T([0], -32768), Record({"one": List(Primitive("u1")), "two": Primitive("i2")}, name="T"))
        self.checkdata(T([0], -32769), Record({"one": List(Primitive("u1")), "two": Primitive("i4")}, name="T"))
        self.checkdata(T([0], -2147483648), Record({"one": List(Primitive("u1")), "two": Primitive("i4")}, name="T"))
        self.checkdata(T([0], -2147483649), Record({"one": List(Primitive("u1")), "two": Primitive("i8")}, name="T"))
        self.checkdata(T([0], -9223372036854775808), Record({"one": List(Primitive("u1")), "two": Primitive("i8")}, name="T"))
        self.checkdata(T([0], -9223372036854775809), Record({"one": List(Primitive("u1")), "two": Primitive("f8")}, name="T"))
        self.checkdata(T([0], 0.0), Record({"one": List(Primitive("u1")), "two": Primitive("f8")}, name="T"))
        self.checkdata(T([0], 3.14), Record({"one": List(Primitive("u1")), "two": Primitive("f8")}, name="T"))
        self.checkdata(T([0], float("-inf")), Record({"one": List(Primitive("u1")), "two": Primitive("f8")}, name="T"))
        self.checkdata(T([0], float("inf")), Record({"one": List(Primitive("u1")), "two": Primitive("f8")}, name="T"))
        self.checkdata(T([0], float("nan")), Record({"one": List(Primitive("u1")), "two": Primitive("f8")}, name="T"))
        self.checkdata(T([0], 1+1j), Record({"one": List(Primitive("u1")), "two": Primitive("c16")}, name="T"))

    def test_infer_List_Record(self):
        # same field --> unify types of that field if possible
        self.checkdata([{"one": 0}, {"one": 3.14}], List(Record({"one": Primitive("f8")})))
        # same field, can't unify --> Record with a Union-valued field
        self.checkdata([{"one": 0}, {"one": [0]}], List(Record({"one": Union([Primitive("u1"), List(Primitive("u1"))])})))
        # different fields --> Union of Records
        self.checkdata([{"one": 0}, {"two": 0}], List(Union([Record({"one": Primitive("u1")}), Record({"two": Primitive("u1")})])))
        self.checkdata([{"one": 0}, {"one": 0, "two": 0}], List(Union([Record({"one": Primitive("u1")}), Record({"one": Primitive("u1"), "two": Primitive("u1")})])))
        self.checkdata([{"one": 0, "two": 0}, {"one": 0}], List(Union([Record({"one": Primitive("u1"), "two": Primitive("u1")}), Record({"one": Primitive("u1")})])))
        # None --> nullable Record
        self.checkdata([{"one": 0}, None], List(Record({"one": Primitive("u1")}, nullable=True)))
        self.checkdata([{"one": 0}, None, {"two": 0}], List(Union([Record({"one": Primitive("u1")}, nullable=True), Record({"two": Primitive("u1")})])))
