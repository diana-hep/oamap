#!/usr/bin/env python

# Copyright 2017 DIANA-HEP
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

import numpy
from plur.util import TypeDefinitionError
from plur.types import *
from plur.python import *

class TestPython(unittest.TestCase):
    def runTest(self):
        pass

    def test_types(self):
        # P
        self.assertEqual(infertype(False), boolean)
        self.assertEqual(infertype(True), boolean)

        self.assertEqual(infertype(0), uint8)
        self.assertEqual(infertype(255), uint8)
        self.assertEqual(infertype(256), uint16)
        self.assertEqual(infertype(65535), uint16)
        self.assertEqual(infertype(65536), uint32)
        self.assertEqual(infertype(4294967295), uint32)
        self.assertEqual(infertype(4294967296), uint64)
        self.assertEqual(infertype(18446744073709551615), uint64)
        self.assertEqual(infertype(18446744073709551616), float64)

        self.assertEqual(infertype(-1), int8)
        self.assertEqual(infertype(-128), int8)
        self.assertEqual(infertype(-129), int16)
        self.assertEqual(infertype(-32768), int16)
        self.assertEqual(infertype(-32769), int32)
        self.assertEqual(infertype(-2147483648), int32)
        self.assertEqual(infertype(-2147483649), int64)
        self.assertEqual(infertype(-9223372036854775808), int64)
        self.assertEqual(infertype(-9223372036854775809), float64)

        self.assertEqual(infertype(0.0), float64)
        self.assertEqual(infertype(3.14), float64)
        self.assertEqual(infertype(float("-inf")), float64)
        self.assertEqual(infertype(float("inf")), float64)
        self.assertEqual(infertype(float("nan")), float64)

        self.assertEqual(infertype(1+1j), complex128)

        # L, U
        self.assertEqual(infertype([False]), List(boolean))
        self.assertEqual(infertype([True]), List(boolean))

        self.assertEqual(infertype([0]), List(uint8))
        self.assertEqual(infertype([255]), List(uint8))
        self.assertEqual(infertype([256]), List(uint16))
        self.assertEqual(infertype([65535]), List(uint16))
        self.assertEqual(infertype([65536]), List(uint32))
        self.assertEqual(infertype([4294967295]), List(uint32))
        self.assertEqual(infertype([4294967296]), List(uint64))
        self.assertEqual(infertype([18446744073709551615]), List(uint64))
        self.assertEqual(infertype([18446744073709551616]), List(float64))

        self.assertEqual(infertype([-1]), List(int8))
        self.assertEqual(infertype([-128]), List(int8))
        self.assertEqual(infertype([-129]), List(int16))
        self.assertEqual(infertype([-32768]), List(int16))
        self.assertEqual(infertype([-32769]), List(int32))
        self.assertEqual(infertype([-2147483648]), List(int32))
        self.assertEqual(infertype([-2147483649]), List(int64))
        self.assertEqual(infertype([-9223372036854775808]), List(int64))
        self.assertEqual(infertype([-9223372036854775809]), List(float64))

        self.assertEqual(infertype([float("-inf")]), List(float64))
        self.assertEqual(infertype([float("inf")]), List(float64))
        self.assertEqual(infertype([float("nan")]), List(float64))

        self.assertEqual(infertype([1+1j]), List(complex128))

        self.assertRaises(TypeDefinitionError, lambda: infertype([]))

        self.assertEqual(infertype([0, 255]), List(uint8))
        self.assertEqual(infertype([255, 256]), List(uint16))
        self.assertEqual(infertype([65535, 65536]), List(uint32))
        self.assertEqual(infertype([4294967295, 4294967296]), List(uint64))
        self.assertEqual(infertype([18446744073709551615, 18446744073709551616]), List(float64))
        self.assertEqual(infertype([-1, -128]), List(int8))
        self.assertEqual(infertype([-128, -129]), List(int16))
        self.assertEqual(infertype([-32768, -32769]), List(int32))
        self.assertEqual(infertype([-2147483648, -2147483649]), List(int64))
        self.assertEqual(infertype([-9223372036854775808, -9223372036854775809]), List(float64))
        self.assertEqual(infertype([0, 3.14]), List(float64))
        self.assertEqual(infertype([0, float("-inf")]), List(float64))
        self.assertEqual(infertype([0, float("inf")]), List(float64))
        self.assertEqual(infertype([0, float("nan")]), List(float64))

        self.assertEqual(infertype([0, 1, 255]), List(uint8))
        self.assertEqual(infertype([254, 255, 256]), List(uint16))
        self.assertEqual(infertype([65534, 65535, 65536]), List(uint32))
        self.assertEqual(infertype([4294967294, 4294967295, 4294967296]), List(uint64))
        self.assertEqual(infertype([18446744073709551614, 18446744073709551615, 18446744073709551616]), List(float64))
        self.assertEqual(infertype([-1, -2, -128]), List(int8))
        self.assertEqual(infertype([-127, -128, -129]), List(int16))
        self.assertEqual(infertype([-32767, -32768, -32769]), List(int32))
        self.assertEqual(infertype([-2147483647, -2147483648, -2147483649]), List(int64))
        self.assertEqual(infertype([-9223372036854775807, -9223372036854775808, -9223372036854775809]), List(float64))
        self.assertEqual(infertype([0, 1, 3.14]), List(float64))
        self.assertEqual(infertype([0, 1, float("-inf")]), List(float64))
        self.assertEqual(infertype([0, 1, float("inf")]), List(float64))
        self.assertEqual(infertype([0, 1, float("nan")]), List(float64))

        self.assertEqual(infertype([0, False, 255]), List(Union(uint8, boolean)))
        self.assertEqual(infertype([255, False, 256]), List(Union(uint16, boolean)))
        self.assertEqual(infertype([65535, False, 65536]), List(Union(uint32, boolean)))
        self.assertEqual(infertype([4294967295, False, 4294967296]), List(Union(uint64, boolean)))
        self.assertEqual(infertype([18446744073709551615, False, 18446744073709551616]), List(Union(float64, boolean)))
        self.assertEqual(infertype([-1, False, -128]), List(Union(int8, boolean)))
        self.assertEqual(infertype([-128, False, -129]), List(Union(int16, boolean)))
        self.assertEqual(infertype([-32768, False, -32769]), List(Union(int32, boolean)))
        self.assertEqual(infertype([-2147483648, False, -2147483649]), List(Union(int64, boolean)))
        self.assertEqual(infertype([-9223372036854775808, False, -9223372036854775809]), List(Union(float64, boolean)))
        self.assertEqual(infertype([0, False, 3.14]), List(Union(float64, boolean)))
        self.assertEqual(infertype([0, False, float("-inf")]), List(Union(float64, boolean)))
        self.assertEqual(infertype([0, False, float("inf")]), List(Union(float64, boolean)))
        self.assertEqual(infertype([0, False, float("nan")]), List(Union(float64, boolean)))

        self.assertEqual(infertype([0, [0], 255]), List(Union(uint8, List(uint8))))
        self.assertEqual(infertype([255, [0], 256]), List(Union(uint16, List(uint8))))
        self.assertEqual(infertype([65535, [0], 65536]), List(Union(uint32, List(uint8))))
        self.assertEqual(infertype([4294967295, [0], 4294967296]), List(Union(uint64, List(uint8))))
        self.assertEqual(infertype([18446744073709551615, [0], 18446744073709551616]), List(Union(float64, List(uint8))))
        self.assertEqual(infertype([-1, [0], -128]), List(Union(int8, List(uint8))))
        self.assertEqual(infertype([-128, [0], -129]), List(Union(int16, List(uint8))))
        self.assertEqual(infertype([-32768, [0], -32769]), List(Union(int32, List(uint8))))
        self.assertEqual(infertype([-2147483648, [0], -2147483649]), List(Union(int64, List(uint8))))
        self.assertEqual(infertype([-9223372036854775808, [0], -9223372036854775809]), List(Union(float64, List(uint8))))
        self.assertEqual(infertype([0, [0], 3.14]), List(Union(float64, List(uint8))))
        self.assertEqual(infertype([0, [0], float("-inf")]), List(Union(float64, List(uint8))))
        self.assertEqual(infertype([0, [0], float("inf")]), List(Union(float64, List(uint8))))
        self.assertEqual(infertype([0, [0], float("nan")]), List(Union(float64, List(uint8))))

        self.assertEqual(infertype([0, [0], [], 255]), List(Union(uint8, List(uint8))))
        self.assertEqual(infertype([255, [0], [], 256]), List(Union(uint16, List(uint8))))
        self.assertEqual(infertype([65535, [0], [], 65536]), List(Union(uint32, List(uint8))))
        self.assertEqual(infertype([4294967295, [0], [], 4294967296]), List(Union(uint64, List(uint8))))
        self.assertEqual(infertype([18446744073709551615, [0], [], 18446744073709551616]), List(Union(float64, List(uint8))))
        self.assertEqual(infertype([-1, [0], [], -128]), List(Union(int8, List(uint8))))
        self.assertEqual(infertype([-128, [0], [], -129]), List(Union(int16, List(uint8))))
        self.assertEqual(infertype([-32768, [0], [], -32769]), List(Union(int32, List(uint8))))
        self.assertEqual(infertype([-2147483648, [0], [], -2147483649]), List(Union(int64, List(uint8))))
        self.assertEqual(infertype([-9223372036854775808, [0], [], -9223372036854775809]), List(Union(float64, List(uint8))))
        self.assertEqual(infertype([0, [0], [], 3.14]), List(Union(float64, List(uint8))))
        self.assertEqual(infertype([0, [0], [], float("-inf")]), List(Union(float64, List(uint8))))
        self.assertEqual(infertype([0, [0], [], float("inf")]), List(Union(float64, List(uint8))))
        self.assertEqual(infertype([0, [0], [], float("nan")]), List(Union(float64, List(uint8))))
        self.assertRaises(TypeDefinitionError, lambda: infertype([[], []]))
        self.assertRaises(TypeDefinitionError, lambda: infertype([0, [], []]))
        self.assertRaises(TypeDefinitionError, lambda: infertype([0, [], [], 255]))

        self.assertEqual(infertype([{"one": 1, "two": 3.14}]), List(Record(one=uint8, two=float64)))
        self.assertEqual(infertype([{"one": 1, "two": 3.14}, {"one": 2, "two": 99.9}]), List(Record(one=uint8, two=float64)))
        self.assertEqual(infertype([{"one": 1, "two": 3.14}, {"one": 2.71, "two": 99.9}]), List(Record(one=float64, two=float64)))
        self.assertEqual(infertype([{"one": 1, "two": 3.14}, {"one": False, "two": 99.9}]), List(Record(one=Union(uint8, boolean), two=float64)))
        self.assertEqual(infertype([{"one": 1}, {"two": 3.14}]), List(Union(Record(one=uint8), Record(two=float64))))
        self.assertEqual(infertype([{"one": 1}, {"two": 3.14}, {"one": 2}]), List(Union(Record(one=uint8), Record(two=float64))))
        self.assertEqual(infertype([{"one": 1}, {"two": 3.14}, {"one": 2.71}]), List(Union(Record(one=float64), Record(two=float64))))
        self.assertEqual(infertype([{"one": 1}, {"two": 3.14}, {"one": False}]), List(Union(Record(one=Union(uint8, boolean)), Record(two=float64))))
        self.assertEqual(infertype([{"one": 1}, {"two": 3.14}, {"one": [0]}]), List(Union(Record(one=Union(uint8, List(uint8))), Record(two=float64))))
        self.assertEqual(infertype([{"one": 1}, {"two": 3.14}, {"one": [0]}, {"one": []}]), List(Union(Record(one=Union(uint8, List(uint8))), Record(two=float64))))
        self.assertRaises(TypeDefinitionError, lambda: infertype([{"one": []}, {"one": []}]))
        self.assertRaises(TypeDefinitionError, lambda: infertype([{"one": 1}, {"one": []}, {"one": []}]))
        self.assertRaises(TypeDefinitionError, lambda: infertype([{"two": 3.14}, {"one": []}, {"one": []}]))
        self.assertRaises(TypeDefinitionError, lambda: infertype([{"one": 1}, {"two": 3.14}, {"one": []}, {"one": []}]))

        # R
        self.assertEqual(infertype({"one": 1, "two": 3.14}), Record(one=uint8, two=float64))
