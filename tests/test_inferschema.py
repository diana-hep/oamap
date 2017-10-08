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

import numpy

from arrowed.frompython import inferschema
from arrowed.schema import *

class TestInferSchema(unittest.TestCase):
    def runTest(self):
        pass

    def test_primitives(self):
        self.assertEqual(inferschema(False), Primitive(((1,), numpy.dtype(numpy.bool_))))
        self.assertEqual(inferschema(True), Primitive(((1,), numpy.dtype(numpy.bool_))))

        self.assertEqual(inferschema(0), Primitive(((1,), numpy.dtype(numpy.uint8))))
        self.assertEqual(inferschema(255), Primitive(((1,), numpy.dtype(numpy.uint8))))
        self.assertEqual(inferschema(256), Primitive(((1,), numpy.dtype(numpy.uint16))))
        self.assertEqual(inferschema(65535), Primitive(((1,), numpy.dtype(numpy.uint16))))
        self.assertEqual(inferschema(65536), Primitive(((1,), numpy.dtype(numpy.uint32))))
        self.assertEqual(inferschema(4294967295), Primitive(((1,), numpy.dtype(numpy.uint32))))
        self.assertEqual(inferschema(4294967296), Primitive(((1,), numpy.dtype(numpy.uint64))))
        self.assertEqual(inferschema(18446744073709551615), Primitive(((1,), numpy.dtype(numpy.uint64))))
        self.assertEqual(inferschema(18446744073709551616), Primitive(((1,), numpy.dtype(numpy.float64))))

        self.assertEqual(inferschema(-1), Primitive(((1,), numpy.dtype(numpy.int8))))
        self.assertEqual(inferschema(-128), Primitive(((1,), numpy.dtype(numpy.int8))))
        self.assertEqual(inferschema(-129), Primitive(((1,), numpy.dtype(numpy.int16))))
        self.assertEqual(inferschema(-32768), Primitive(((1,), numpy.dtype(numpy.int16))))
        self.assertEqual(inferschema(-32769), Primitive(((1,), numpy.dtype(numpy.int32))))
        self.assertEqual(inferschema(-2147483648), Primitive(((1,), numpy.dtype(numpy.int32))))
        self.assertEqual(inferschema(-2147483649), Primitive(((1,), numpy.dtype(numpy.int64))))
        self.assertEqual(inferschema(-9223372036854775808), Primitive(((1,), numpy.dtype(numpy.int64))))
        self.assertEqual(inferschema(-9223372036854775809), Primitive(((1,), numpy.dtype(numpy.float64))))

        self.assertEqual(inferschema(0.0), Primitive(((1,), numpy.dtype(numpy.float64))))
        self.assertEqual(inferschema(3.14), Primitive(((1,), numpy.dtype(numpy.float64))))
        self.assertEqual(inferschema(float("-inf")), Primitive(((1,), numpy.dtype(numpy.float64))))
        self.assertEqual(inferschema(float("inf")), Primitive(((1,), numpy.dtype(numpy.float64))))
        self.assertEqual(inferschema(float("nan")), Primitive(((1,), numpy.dtype(numpy.float64))))

        self.assertEqual(inferschema(1+1j), Primitive(((1,), numpy.dtype(numpy.complex128))))

    def test_list0(self):
        self.assertRaises(TypeError, lambda: inferschema([]))

    def test_list1(self):
        self.assertEqual(inferschema([False]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.bool_)))))
        self.assertEqual(inferschema([True]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.bool_)))))

        self.assertEqual(inferschema([0]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.uint8)))))
        self.assertEqual(inferschema([255]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.uint8)))))
        self.assertEqual(inferschema([256]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.uint16)))))
        self.assertEqual(inferschema([65535]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.uint16)))))
        self.assertEqual(inferschema([65536]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.uint32)))))
        self.assertEqual(inferschema([4294967295]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.uint32)))))
        self.assertEqual(inferschema([4294967296]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.uint64)))))
        self.assertEqual(inferschema([18446744073709551615]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.uint64)))))
        self.assertEqual(inferschema([18446744073709551616]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.float64)))))

        self.assertEqual(inferschema([-1]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.int8)))))
        self.assertEqual(inferschema([-128]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.int8)))))
        self.assertEqual(inferschema([-129]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.int16)))))
        self.assertEqual(inferschema([-32768]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.int16)))))
        self.assertEqual(inferschema([-32769]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.int32)))))
        self.assertEqual(inferschema([-2147483648]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.int32)))))
        self.assertEqual(inferschema([-2147483649]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.int64)))))
        self.assertEqual(inferschema([-9223372036854775808]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.int64)))))
        self.assertEqual(inferschema([-9223372036854775809]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.float64)))))

        self.assertEqual(inferschema([float("-inf")]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.float64)))))
        self.assertEqual(inferschema([float("inf")]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.float64)))))
        self.assertEqual(inferschema([float("nan")]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.float64)))))

        self.assertEqual(inferschema([1+1j]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.complex128)))))

    def test_list23(self):
        self.assertEqual(inferschema([0, 255]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((2,), numpy.dtype(numpy.uint8)))))
        self.assertEqual(inferschema([255, 256]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((2,), numpy.dtype(numpy.uint16)))))
        self.assertEqual(inferschema([65535, 65536]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((2,), numpy.dtype(numpy.uint32)))))
        self.assertEqual(inferschema([4294967295, 4294967296]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((2,), numpy.dtype(numpy.uint64)))))
        self.assertEqual(inferschema([18446744073709551615, 18446744073709551616]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((2,), numpy.dtype(numpy.float64)))))
        self.assertEqual(inferschema([-1, -128]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((2,), numpy.dtype(numpy.int8)))))
        self.assertEqual(inferschema([-128, -129]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((2,), numpy.dtype(numpy.int16)))))
        self.assertEqual(inferschema([-32768, -32769]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((2,), numpy.dtype(numpy.int32)))))
        self.assertEqual(inferschema([-2147483648, -2147483649]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((2,), numpy.dtype(numpy.int64)))))
        self.assertEqual(inferschema([-9223372036854775808, -9223372036854775809]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((2,), numpy.dtype(numpy.float64)))))
        self.assertEqual(inferschema([0, 3.14]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((2,), numpy.dtype(numpy.float64)))))
        self.assertEqual(inferschema([0, float("-inf")]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((2,), numpy.dtype(numpy.float64)))))
        self.assertEqual(inferschema([0, float("inf")]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((2,), numpy.dtype(numpy.float64)))))
        self.assertEqual(inferschema([0, float("nan")]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((2,), numpy.dtype(numpy.float64)))))

        self.assertEqual(inferschema([0, 1, 255]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((3,), numpy.dtype(numpy.uint8)))))
        self.assertEqual(inferschema([254, 255, 256]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((3,), numpy.dtype(numpy.uint16)))))
        self.assertEqual(inferschema([65534, 65535, 65536]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((3,), numpy.dtype(numpy.uint32)))))
        self.assertEqual(inferschema([4294967294, 4294967295, 4294967296]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((3,), numpy.dtype(numpy.uint64)))))
        self.assertEqual(inferschema([18446744073709551614, 18446744073709551615, 18446744073709551616]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((3,), numpy.dtype(numpy.float64)))))
        self.assertEqual(inferschema([-1, -2, -128]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((3,), numpy.dtype(numpy.int8)))))
        self.assertEqual(inferschema([-127, -128, -129]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((3,), numpy.dtype(numpy.int16)))))
        self.assertEqual(inferschema([-32767, -32768, -32769]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((3,), numpy.dtype(numpy.int32)))))
        self.assertEqual(inferschema([-2147483647, -2147483648, -2147483649]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((3,), numpy.dtype(numpy.int64)))))
        self.assertEqual(inferschema([-9223372036854775807, -9223372036854775808, -9223372036854775809]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((3,), numpy.dtype(numpy.float64)))))
        self.assertEqual(inferschema([0, 1, 3.14]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((3,), numpy.dtype(numpy.float64)))))
        self.assertEqual(inferschema([0, 1, float("-inf")]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((3,), numpy.dtype(numpy.float64)))))
        self.assertEqual(inferschema([0, 1, float("inf")]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((3,), numpy.dtype(numpy.float64)))))
        self.assertEqual(inferschema([0, 1, float("nan")]), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((3,), numpy.dtype(numpy.float64)))))

    def test_uniondata(self):
        self.assertEqual(inferschema([0, False, 255]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((3,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.uint8))), Primitive(((1,), numpy.dtype(numpy.bool_)))))))
        self.assertEqual(inferschema([255, False, 256]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((3,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.uint16))), Primitive(((1,), numpy.dtype(numpy.bool_)))))))
        self.assertEqual(inferschema([65535, False, 65536]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((3,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.uint32))), Primitive(((1,), numpy.dtype(numpy.bool_)))))))
        self.assertEqual(inferschema([4294967295, False, 4294967296]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((3,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.uint64))), Primitive(((1,), numpy.dtype(numpy.bool_)))))))
        self.assertEqual(inferschema([18446744073709551615, False, 18446744073709551616]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((3,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.float64))), Primitive(((1,), numpy.dtype(numpy.bool_)))))))
        self.assertEqual(inferschema([-1, False, -128]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((3,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.int8))), Primitive(((1,), numpy.dtype(numpy.bool_)))))))
        self.assertEqual(inferschema([-128, False, -129]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((3,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.int16))), Primitive(((1,), numpy.dtype(numpy.bool_)))))))
        self.assertEqual(inferschema([-32768, False, -32769]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((3,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.int32))), Primitive(((1,), numpy.dtype(numpy.bool_)))))))
        self.assertEqual(inferschema([-2147483648, False, -2147483649]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((3,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.int64))), Primitive(((1,), numpy.dtype(numpy.bool_)))))))
        self.assertEqual(inferschema([-9223372036854775808, False, -9223372036854775809]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((3,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.float64))), Primitive(((1,), numpy.dtype(numpy.bool_)))))))
        self.assertEqual(inferschema([0, False, 3.14]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((3,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.float64))), Primitive(((1,), numpy.dtype(numpy.bool_)))))))
        self.assertEqual(inferschema([0, False, float("-inf")]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((3,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.float64))), Primitive(((1,), numpy.dtype(numpy.bool_)))))))
        self.assertEqual(inferschema([0, False, float("inf")]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((3,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.float64))), Primitive(((1,), numpy.dtype(numpy.bool_)))))))
        self.assertEqual(inferschema([0, False, float("nan")]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((3,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.float64))), Primitive(((1,), numpy.dtype(numpy.bool_)))))))

    def test_unionstructure(self):
        self.assertEqual(inferschema([0, [0], 255]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((3,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.uint8))), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.uint8))))))))
        self.assertEqual(inferschema([255, [0], 256]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((3,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.uint16))), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.uint8))))))))
        self.assertEqual(inferschema([65535, [0], 65536]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((3,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.uint32))), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.uint8))))))))
        self.assertEqual(inferschema([4294967295, [0], 4294967296]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((3,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.uint64))), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.uint8))))))))
        self.assertEqual(inferschema([18446744073709551615, [0], 18446744073709551616]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((3,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.float64))), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.uint8))))))))
        self.assertEqual(inferschema([-1, [0], -128]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((3,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.int8))), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.uint8))))))))
        self.assertEqual(inferschema([-128, [0], -129]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((3,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.int16))), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.uint8))))))))
        self.assertEqual(inferschema([-32768, [0], -32769]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((3,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.int32))), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.uint8))))))))
        self.assertEqual(inferschema([-2147483648, [0], -2147483649]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((3,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.int64))), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.uint8))))))))
        self.assertEqual(inferschema([-9223372036854775808, [0], -9223372036854775809]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((3,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.float64))), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.uint8))))))))
        self.assertEqual(inferschema([0, [0], 3.14]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((3,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.float64))), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.uint8))))))))
        self.assertEqual(inferschema([0, [0], float("-inf")]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((3,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.float64))), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.uint8))))))))
        self.assertEqual(inferschema([0, [0], float("inf")]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((3,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.float64))), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.uint8))))))))
        self.assertEqual(inferschema([0, [0], float("nan")]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((3,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.float64))), ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.uint8))))))))

        self.assertEqual(inferschema([0, [0], [], 255]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((4,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.uint8))), ListOffset(((3,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.uint8))))))))
        self.assertEqual(inferschema([255, [0], [], 256]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((4,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.uint16))), ListOffset(((3,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.uint8))))))))
        self.assertEqual(inferschema([65535, [0], [], 65536]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((4,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.uint32))), ListOffset(((3,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.uint8))))))))
        self.assertEqual(inferschema([4294967295, [0], [], 4294967296]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((4,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.uint64))), ListOffset(((3,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.uint8))))))))
        self.assertEqual(inferschema([18446744073709551615, [0], [], 18446744073709551616]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((4,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.float64))), ListOffset(((3,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.uint8))))))))
        self.assertEqual(inferschema([-1, [0], [], -128]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((4,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.int8))), ListOffset(((3,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.uint8))))))))
        self.assertEqual(inferschema([-128, [0], [], -129]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((4,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.int16))), ListOffset(((3,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.uint8))))))))
        self.assertEqual(inferschema([-32768, [0], [], -32769]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((4,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.int32))), ListOffset(((3,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.uint8))))))))
        self.assertEqual(inferschema([-2147483648, [0], [], -2147483649]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((4,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.int64))), ListOffset(((3,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.uint8))))))))
        self.assertEqual(inferschema([-9223372036854775808, [0], [], -9223372036854775809]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((4,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.float64))), ListOffset(((3,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.uint8))))))))
        self.assertEqual(inferschema([0, [0], [], 3.14]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((4,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.float64))), ListOffset(((3,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.uint8))))))))
        self.assertEqual(inferschema([0, [0], [], float("-inf")]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((4,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.float64))), ListOffset(((3,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.uint8))))))))
        self.assertEqual(inferschema([0, [0], [], float("inf")]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((4,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.float64))), ListOffset(((3,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.uint8))))))))
        self.assertEqual(inferschema([0, [0], [], float("nan")]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((4,), numpy.dtype(numpy.int8)), (Primitive(((2,), numpy.dtype(numpy.float64))), ListOffset(((3,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.uint8))))))))

        self.assertRaises(TypeError, lambda: inferschema([[], []]))
        self.assertRaises(TypeError, lambda: inferschema([0, [], []]))
        self.assertRaises(TypeError, lambda: inferschema([0, [], [], 255]))

    def test_record(self):
        self.assertEqual(inferschema({"one": 1, "two": 3.14}), Record({"two": Primitive(((1,), numpy.dtype(numpy.float64))), "one": Primitive(((1,), numpy.dtype(numpy.uint8)))}))

        self.assertEqual(inferschema([{"one": 1, "two": 3.14}]), ListOffset(((2,), numpy.dtype(numpy.int32)), Record({"two": Primitive(((1,), numpy.dtype(numpy.float64))), "one": Primitive(((1,), numpy.dtype(numpy.uint8)))})))
        self.assertEqual(inferschema([{"one": 1, "two": 3.14}, {"one": 2, "two": 99.9}]), ListOffset(((2,), numpy.dtype(numpy.int32)), Record({"two": Primitive(((2,), numpy.dtype(numpy.float64))), "one": Primitive(((2,), numpy.dtype(numpy.uint8)))})))
        self.assertEqual(inferschema([{"one": 1, "two": 3.14}, {"one": 2.71, "two": 99.9}]), ListOffset(((2,), numpy.dtype(numpy.int32)), Record({"two": Primitive(((2,), numpy.dtype(numpy.float64))), "one": Primitive(((2,), numpy.dtype(numpy.float64)))})))
        self.assertEqual(inferschema([{"one": 1, "two": 3.14}, {"one": False, "two": 99.9}]), ListOffset(((2,), numpy.dtype(numpy.int32)), Record({"two": Primitive(((2,), numpy.dtype(numpy.float64))), "one": UnionDense(((2,), numpy.dtype(numpy.int8)), (Primitive(((1,), numpy.dtype(numpy.uint8))), Primitive(((1,), numpy.dtype(numpy.bool)))))})))
        self.assertEqual(inferschema([{"one": 1}, {"two": 3.14}]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((2,), numpy.dtype(numpy.int8)), (Record({"one": Primitive(((1,), numpy.dtype(numpy.uint8)))}), Record({"two": Primitive(((1,), numpy.dtype(numpy.float64)))})))))
        self.assertEqual(inferschema([{"one": 1}, {"two": 3.14}, {"one": 2}]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((3,), numpy.dtype(numpy.int8)), (Record({"one": Primitive(((2,), numpy.dtype(numpy.uint8)))}), Record({"two": Primitive(((1,), numpy.dtype(numpy.float64)))})))))
        self.assertEqual(inferschema([{"one": 1}, {"two": 3.14}, {"one": 2.71}]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((3,), numpy.dtype(numpy.int8)), (Record({"one": Primitive(((2,), numpy.dtype(numpy.float64)))}), Record({"two": Primitive(((1,), numpy.dtype(numpy.float64)))})))))
        self.assertEqual(inferschema([{"one": 1}, {"two": 3.14}, {"one": False}]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((3,), numpy.dtype(numpy.int8)), (Record({"one": UnionDense(((2,), numpy.dtype(numpy.int8)), (Primitive(((1,), numpy.dtype(numpy.bool))), Primitive(((1,), numpy.dtype(numpy.uint8)))))}), Record({"two": Primitive(((1,), numpy.dtype(numpy.float64)))})))))
        self.assertEqual(inferschema([{"one": 1}, {"two": 3.14}, {"one": [0]}]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((3,), numpy.dtype(numpy.int8)), (Record({"one": UnionDense(((2,), numpy.dtype(numpy.int8)), (ListOffset(((2,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.uint8)))), Primitive(((1,), numpy.dtype(numpy.uint8)))))}), Record({"two": Primitive(((1,), numpy.dtype(numpy.float64)))})))))
        self.assertEqual(inferschema([{"one": 1}, {"two": 3.14}, {"one": [0]}, {"one": []}]), ListOffset(((2,), numpy.dtype(numpy.int32)), UnionDense(((4,), numpy.dtype(numpy.int8)), (Record({"one": UnionDense(((3,), numpy.dtype(numpy.int8)), (ListOffset(((3,), numpy.dtype(numpy.int32)), Primitive(((1,), numpy.dtype(numpy.uint8)))), Primitive(((1,), numpy.dtype(numpy.uint8)))))}), Record({"two": Primitive(((1,), numpy.dtype(numpy.float64)))})))))

        self.assertRaises(TypeError, lambda: inferschema([{"one": []}, {"one": []}]))
        self.assertRaises(TypeError, lambda: inferschema([{"one": 1}, {"one": []}, {"one": []}]))
        self.assertRaises(TypeError, lambda: inferschema([{"two": 3.14}, {"one": []}, {"one": []}]))
        self.assertRaises(TypeError, lambda: inferschema([{"one": 1}, {"two": 3.14}, {"one": []}, {"one": []}]))
