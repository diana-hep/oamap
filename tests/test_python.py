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

    def test_infertype(self):
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

    def test_toarrays(self):
        def same(observed, expected):
            if set(observed.keys()) != set(expected.keys()):
                raise AssertionError("different keys:\n    observed: {0}\n    expected: {1}".format(sorted(observed.keys()), sorted(expected.keys())))

            if not all(observed[n].dtype == expected[n].dtype and numpy.array_equal(observed[n], expected[n]) for n in observed.keys()):
                out = []
                for n in sorted(observed.keys()):
                    out.append("    {0}".format(n))
                    if not (observed[n].dtype == expected[n].dtype and numpy.array_equal(observed[n], expected[n])):
                        out.append("        {0}\t{1}".format(observed[n].dtype.str, observed[n].tolist()))
                        out.append("        {0}\t{1}".format(expected[n].dtype.str, expected[n].tolist()))
                raise AssertionError("different values:\n{0}".format("\n".join(out)))

        # P
        same(toarrays("prefix", False, boolean), {"prefix": numpy.array([False])})
        same(toarrays("prefix", 3.14, float64), {"prefix": numpy.array([3.14])})

        # L
        same(toarrays("prefix", [False, True], List(boolean)), {"prefix-Lo": numpy.array([2], dtype=numpy.uint64), "prefix-Ld": numpy.array([False, True])})
        same(toarrays("prefix", [1, 2, 3], List(int64)), {"prefix-Lo": numpy.array([3], dtype=numpy.uint64), "prefix-Ld": numpy.array([1, 2, 3])})
        same(toarrays("prefix", [1, 2, 3], List(float64)), {"prefix-Lo": numpy.array([3], dtype=numpy.uint64), "prefix-Ld": numpy.array([1.0, 2.0, 3.0])})

        same(toarrays("prefix", [[1], [2, 3], []], List(List(int64))), {"prefix-Lo": numpy.array([3], dtype=numpy.uint64), "prefix-Ld-Lo": numpy.array([1, 3, 3], dtype=numpy.uint64), "prefix-Ld-Ld": numpy.array([1, 2, 3])})
        same(toarrays("prefix", [[], [1], [2, 3]], List(List(int64))), {"prefix-Lo": numpy.array([3], dtype=numpy.uint64), "prefix-Ld-Lo": numpy.array([0, 1, 3], dtype=numpy.uint64), "prefix-Ld-Ld": numpy.array([1, 2, 3])})

        # U
        same(toarrays("prefix", False, Union(boolean, int64)), {"prefix-Ut": numpy.array([0], dtype=numpy.uint8), "prefix-Uo": numpy.array([0], dtype=numpy.uint64), "prefix-Ud0": numpy.array([False], dtype=numpy.bool), "prefix-Ud1": numpy.array([], dtype=numpy.int64)})
        same(toarrays("prefix", 1, Union(boolean, int64)), {"prefix-Ut": numpy.array([1], dtype=numpy.uint8), "prefix-Uo": numpy.array([0], dtype=numpy.uint64), "prefix-Ud0": numpy.array([], dtype=numpy.bool), "prefix-Ud1": numpy.array([1], dtype=numpy.int64)})

        same(toarrays("prefix", [False, 1], List(Union(boolean, int64))), {"prefix-Lo": numpy.array([2], dtype=numpy.uint64), "prefix-Ld-Ut": numpy.array([0, 1], dtype=numpy.uint8), "prefix-Ld-Uo": numpy.array([0, 0], dtype=numpy.uint64), "prefix-Ld-Ud0": numpy.array([False], dtype=numpy.bool), "prefix-Ld-Ud1": numpy.array([1])})
        same(toarrays("prefix", [1, False], List(Union(boolean, int64))), {"prefix-Lo": numpy.array([2], dtype=numpy.uint64), "prefix-Ld-Ut": numpy.array([1, 0], dtype=numpy.uint8), "prefix-Ld-Uo": numpy.array([0, 0], dtype=numpy.uint64), "prefix-Ld-Ud0": numpy.array([False], dtype=numpy.bool), "prefix-Ld-Ud1": numpy.array([1])})
        same(toarrays("prefix", [1, False, 2], List(Union(boolean, int64))), {"prefix-Lo": numpy.array([3], dtype=numpy.uint64), "prefix-Ld-Ut": numpy.array([1, 0, 1], dtype=numpy.uint8), "prefix-Ld-Uo": numpy.array([0, 0, 1], dtype=numpy.uint64), "prefix-Ld-Ud0": numpy.array([False], dtype=numpy.bool), "prefix-Ld-Ud1": numpy.array([1, 2])})

        same(toarrays("prefix", [1, [3.14], 2], List(Union(List(float64), int64))), {"prefix-Lo": numpy.array([3], dtype=numpy.uint64), "prefix-Ld-Ut": numpy.array([0, 1, 0], dtype=numpy.uint8), "prefix-Ld-Uo": numpy.array([0, 0, 1], dtype=numpy.uint64), "prefix-Ld-Ud0": numpy.array([1, 2]), "prefix-Ld-Ud1-Lo": numpy.array([1], dtype=numpy.uint64), "prefix-Ld-Ud1-Ld": numpy.array([3.14])})

        same(toarrays("prefix", [1, [3.14, False], 2], List(Union(List(Union(boolean, float64)), int64))), {"prefix-Lo": numpy.array([3], dtype=numpy.uint64), "prefix-Ld-Ut": numpy.array([0, 1, 0], dtype=numpy.uint8), "prefix-Ld-Uo": numpy.array([0, 0, 1], dtype=numpy.uint64), "prefix-Ld-Ud0": numpy.array([1, 2]), "prefix-Ld-Ud1-Lo": numpy.array([2], dtype=numpy.uint64), "prefix-Ld-Ud1-Ld-Ut": numpy.array([1, 0], dtype=numpy.uint8), "prefix-Ld-Ud1-Ld-Uo": numpy.array([0, 0], dtype=numpy.uint64), "prefix-Ld-Ud1-Ld-Ud0": numpy.array([False], dtype=numpy.bool), "prefix-Ld-Ud1-Ld-Ud1": numpy.array([3.14])})

        # R
        same(toarrays("prefix", {"one": 1, "two": 3.14}, Record(one=int64, two=float64)), {"prefix-R_one": numpy.array([1]), "prefix-R_two": numpy.array([3.14])})

        same(toarrays("prefix", [{"one": 1, "two": 1.1}, {"one": 2, "two": 2.2}], List(Record(one=int64, two=float64))), {"prefix-Lo": numpy.array([2], dtype=numpy.uint64), "prefix-Ld-R_one": numpy.array([1, 2]), "prefix-Ld-R_two": numpy.array([1.1, 2.2])})

        same(toarrays("prefix", {"one": [1, 2, 3], "two": 3.14}, Record(one=List(int64), two=float64)), {"prefix-R_one-Lo": numpy.array([3], dtype=numpy.uint64), "prefix-R_one-Ld": numpy.array([1, 2, 3]), "prefix-R_two": numpy.array([3.14])})

        same(toarrays("prefix", [{"one": [1, 2], "two": 1.1}, {"one": [], "two": 2.2}, {"one": [3], "two": 3.3}], List(Record(one=List(int64), two=float64))), {"prefix-Lo": numpy.array([3], dtype=numpy.uint64), "prefix-Ld-R_one-Lo": numpy.array([2, 2, 3], dtype=numpy.uint64), "prefix-Ld-R_one-Ld": numpy.array([1, 2, 3]), "prefix-Ld-R_two": numpy.array([1.1, 2.2, 3.3])})

        same(toarrays("prefix", {"one": 99, "two": 3.14}, Record(one=int64, two=Union(boolean, float64))), {"prefix-R_one": numpy.array([99]), "prefix-R_two-Ut": numpy.array([1], dtype=numpy.uint8), "prefix-R_two-Uo": numpy.array([0], dtype=numpy.uint64), "prefix-R_two-Ud0": numpy.array([], dtype=numpy.bool), "prefix-R_two-Ud1": numpy.array([3.14])})
        same(toarrays("prefix", {"one": 99, "two": False}, Record(one=int64, two=Union(boolean, float64))), {"prefix-R_one": numpy.array([99]), "prefix-R_two-Ut": numpy.array([0], dtype=numpy.uint8), "prefix-R_two-Uo": numpy.array([0], dtype=numpy.uint64), "prefix-R_two-Ud0": numpy.array([False], dtype=numpy.bool), "prefix-R_two-Ud1": numpy.array([])})

        same(toarrays("prefix", [{"one": 98, "two": 3.14}, {"one": 99, "two": False}], List(Record(one=int64, two=Union(boolean, float64)))), {"prefix-Lo": numpy.array([2], dtype=numpy.uint64), "prefix-Ld-R_one": numpy.array([98, 99]), "prefix-Ld-R_two-Ut": numpy.array([1, 0], dtype=numpy.uint8), "prefix-Ld-R_two-Uo": numpy.array([0, 0], dtype=numpy.uint64), "prefix-Ld-R_two-Ud0": numpy.array([False], dtype=numpy.bool), "prefix-Ld-R_two-Ud1": numpy.array([3.14])})

        same(toarrays("prefix", [{"one": 99}, {"two": 3.14}], List(Union(Record(one=int64), Record(two=float64)))), {"prefix-Lo": numpy.array([2], dtype=numpy.uint64), "prefix-Ld-Ut": numpy.array([0, 1], dtype=numpy.uint8), "prefix-Ld-Uo": numpy.array([0, 0], dtype=numpy.uint64), "prefix-Ld-Ud0-R_one": numpy.array([99]), "prefix-Ld-Ud1-R_two": numpy.array([3.14])})
        same(toarrays("prefix", [{"one": 98}, {"two": 3.14}, {"one": 99}], List(Union(Record(one=int64), Record(two=float64)))), {"prefix-Lo": numpy.array([3], dtype=numpy.uint64), "prefix-Ld-Ut": numpy.array([0, 1, 0], dtype=numpy.uint8), "prefix-Ld-Uo": numpy.array([0, 0, 1], dtype=numpy.uint64), "prefix-Ld-Ud0-R_one": numpy.array([98, 99]), "prefix-Ld-Ud1-R_two": numpy.array([3.14])})

        same(toarrays("prefix", [{"one": 98}, {"one": 99, "two": 3.14}], List(Union(Record(one=int64), Record(one=int64, two=float64)))), {"prefix-Lo": numpy.array([2], dtype=numpy.uint64), "prefix-Ld-Ut": numpy.array([1, 0], dtype=numpy.uint8), "prefix-Ld-Uo": numpy.array([0, 0], dtype=numpy.uint64), "prefix-Ld-Ud0-R_one": numpy.array([99]), "prefix-Ld-Ud0-R_two": numpy.array([3.14]), "prefix-Ld-Ud1-R_one": numpy.array([98])})
