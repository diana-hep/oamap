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

from arrowed.frompython import toarrays
from arrowed.schema import *

class TestFromPython(unittest.TestCase):
    def runTest(self):
        pass

    def test_primitives(self):
        print
        print toarrays(False).format()
        print Primitive(numpy.array([False], dtype=numpy.bool_)).format()

        self.assertEqual(toarrays(False), Primitive(numpy.array([False], dtype=numpy.bool_)))
        self.assertEqual(toarrays(True), Primitive(numpy.array([True], dtype=numpy.bool_)))

        self.assertEqual(toarrays(0), Primitive(numpy.array([0], dtype=numpy.uint8)))
        self.assertEqual(toarrays(255), Primitive(numpy.array([255], dtype=numpy.uint8)))
        self.assertEqual(toarrays(256), Primitive(numpy.array([256], dtype=numpy.uint16)))
        self.assertEqual(toarrays(65535), Primitive(numpy.array([65535], dtype=numpy.uint16)))
        self.assertEqual(toarrays(65536), Primitive(numpy.array([65536], dtype=numpy.uint32)))
        self.assertEqual(toarrays(4294967295), Primitive(numpy.array([4294967295], dtype=numpy.uint32)))
        self.assertEqual(toarrays(4294967296), Primitive(numpy.array([4294967296], dtype=numpy.uint64)))
        self.assertEqual(toarrays(18446744073709551615), Primitive(numpy.array([18446744073709551615], dtype=numpy.uint64)))
        self.assertEqual(toarrays(18446744073709551616), Primitive(numpy.array([18446744073709551616], dtype=numpy.float64)))

        self.assertEqual(toarrays(-1), Primitive(numpy.array([-1], dtype=numpy.int8)))
        self.assertEqual(toarrays(-128), Primitive(numpy.array([-128], dtype=numpy.int8)))
        self.assertEqual(toarrays(-129), Primitive(numpy.array([-129], dtype=numpy.int16)))
        self.assertEqual(toarrays(-32768), Primitive(numpy.array([-32768], dtype=numpy.int16)))
        self.assertEqual(toarrays(-32769), Primitive(numpy.array([-32769], dtype=numpy.int32)))
        self.assertEqual(toarrays(-2147483648), Primitive(numpy.array([-2147483648], dtype=numpy.int32)))
        self.assertEqual(toarrays(-2147483649), Primitive(numpy.array([-2147483649], dtype=numpy.int64)))
        self.assertEqual(toarrays(-9223372036854775808), Primitive(numpy.array([-9223372036854775808], dtype=numpy.int64)))
        self.assertEqual(toarrays(-9223372036854775809), Primitive(numpy.array([-9223372036854775809], dtype=numpy.float64)))

        self.assertEqual(toarrays(0.0), Primitive(numpy.array([0.0], dtype=numpy.float64)))
        self.assertEqual(toarrays(3.14), Primitive(numpy.array([3.14], dtype=numpy.float64)))
        self.assertEqual(toarrays(float("-inf")), Primitive(numpy.array([float("-inf")], dtype=numpy.float64)))
        self.assertEqual(toarrays(float("inf")), Primitive(numpy.array([float("inf")], dtype=numpy.float64)))

        self.assertEqual(toarrays(1+1j), Primitive(numpy.array([1+1j], dtype=numpy.complex128)))

    def test_list1(self):
        self.assertEqual(toarrays([False]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([1], dtype=numpy.int32), Primitive(numpy.array([False], dtype=numpy.bool_))))
        self.assertEqual(toarrays([True]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([1], dtype=numpy.int32), Primitive(numpy.array([True], dtype=numpy.bool_))))

        self.assertEqual(toarrays([0]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([1], dtype=numpy.int32), Primitive(numpy.array([0], dtype=numpy.uint8))))
        self.assertEqual(toarrays([255]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([1], dtype=numpy.int32), Primitive(numpy.array([255], dtype=numpy.uint8))))
        self.assertEqual(toarrays([256]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([1], dtype=numpy.int32), Primitive(numpy.array([256], dtype=numpy.uint16))))
        self.assertEqual(toarrays([65535]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([1], dtype=numpy.int32), Primitive(numpy.array([65535], dtype=numpy.uint16))))
        self.assertEqual(toarrays([65536]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([1], dtype=numpy.int32), Primitive(numpy.array([65536], dtype=numpy.uint32))))
        self.assertEqual(toarrays([4294967295]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([1], dtype=numpy.int32), Primitive(numpy.array([4294967295], dtype=numpy.uint32))))
        self.assertEqual(toarrays([4294967296]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([1], dtype=numpy.int32), Primitive(numpy.array([4294967296], dtype=numpy.uint64))))
        self.assertEqual(toarrays([18446744073709551615]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([1], dtype=numpy.int32), Primitive(numpy.array([18446744073709551615], dtype=numpy.uint64))))
        self.assertEqual(toarrays([18446744073709551616]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([1], dtype=numpy.int32), Primitive(numpy.array([18446744073709551616], dtype=numpy.float64))))

        self.assertEqual(toarrays([-1]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([1], dtype=numpy.int32), Primitive(numpy.array([-1], dtype=numpy.int8))))
        self.assertEqual(toarrays([-128]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([1], dtype=numpy.int32), Primitive(numpy.array([-128], dtype=numpy.int8))))
        self.assertEqual(toarrays([-129]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([1], dtype=numpy.int32), Primitive(numpy.array([-129], dtype=numpy.int16))))
        self.assertEqual(toarrays([-32768]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([1], dtype=numpy.int32), Primitive(numpy.array([-32768], dtype=numpy.int16))))
        self.assertEqual(toarrays([-32769]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([1], dtype=numpy.int32), Primitive(numpy.array([-32769], dtype=numpy.int32))))
        self.assertEqual(toarrays([-2147483648]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([1], dtype=numpy.int32), Primitive(numpy.array([-2147483648], dtype=numpy.int32))))
        self.assertEqual(toarrays([-2147483649]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([1], dtype=numpy.int32), Primitive(numpy.array([-2147483649], dtype=numpy.int64))))
        self.assertEqual(toarrays([-9223372036854775808]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([1], dtype=numpy.int32), Primitive(numpy.array([-9223372036854775808], dtype=numpy.int64))))
        self.assertEqual(toarrays([-9223372036854775809]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([1], dtype=numpy.int32), Primitive(numpy.array([-9223372036854775809], dtype=numpy.float64))))

        self.assertEqual(toarrays([float("-inf")]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([1], dtype=numpy.int32), Primitive(numpy.array([float("-inf")], dtype=numpy.float64))))
        self.assertEqual(toarrays([float("inf")]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([1], dtype=numpy.int32), Primitive(numpy.array([float("inf")], dtype=numpy.float64))))

        self.assertEqual(toarrays([1+1j]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([1], dtype=numpy.int32), Primitive(numpy.array([1+1j], dtype=numpy.complex128))))

    def test_list23(self):
        self.assertEqual(toarrays([0, 255]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([2], dtype=numpy.int32), Primitive(numpy.array([0, 255], dtype=numpy.uint8))))
        self.assertEqual(toarrays([255, 256]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([2], dtype=numpy.int32), Primitive(numpy.array([255, 256], dtype=numpy.uint16))))
        self.assertEqual(toarrays([65535, 65536]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([2], dtype=numpy.int32), Primitive(numpy.array([65535, 65536], dtype=numpy.uint32))))
        self.assertEqual(toarrays([4294967295, 4294967296]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([2], dtype=numpy.int32), Primitive(numpy.array([4294967295, 4294967296], dtype=numpy.uint64))))
        self.assertEqual(toarrays([18446744073709551615, 18446744073709551616]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([2], dtype=numpy.int32), Primitive(numpy.array([18446744073709551615, 18446744073709551616], dtype=numpy.float64))))
        self.assertEqual(toarrays([-1, -128]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([2], dtype=numpy.int32), Primitive(numpy.array([-1, -128], dtype=numpy.int8))))
        self.assertEqual(toarrays([-128, -129]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([2], dtype=numpy.int32), Primitive(numpy.array([-128, -129], dtype=numpy.int16))))
        self.assertEqual(toarrays([-32768, -32769]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([2], dtype=numpy.int32), Primitive(numpy.array([-32768, -32769], dtype=numpy.int32))))
        self.assertEqual(toarrays([-2147483648, -2147483649]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([2], dtype=numpy.int32), Primitive(numpy.array([-2147483648, -2147483649], dtype=numpy.int64))))
        self.assertEqual(toarrays([-9223372036854775808, -9223372036854775809]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([2], dtype=numpy.int32), Primitive(numpy.array([-9223372036854775808, -9223372036854775809], dtype=numpy.float64))))
        self.assertEqual(toarrays([0, 3.14]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([2], dtype=numpy.int32), Primitive(numpy.array([0, 3.14], dtype=numpy.float64))))
        self.assertEqual(toarrays([0, float("-inf")]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([2], dtype=numpy.int32), Primitive(numpy.array([0, float("-inf")], dtype=numpy.float64))))
        self.assertEqual(toarrays([0, float("inf")]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([2], dtype=numpy.int32), Primitive(numpy.array([0, float("inf")], dtype=numpy.float64))))

        self.assertEqual(toarrays([0, 1, 255]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([3], dtype=numpy.int32), Primitive(numpy.array([0, 1, 255], dtype=numpy.uint8))))
        self.assertEqual(toarrays([254, 255, 256]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([3], dtype=numpy.int32), Primitive(numpy.array([254, 255, 256], dtype=numpy.uint16))))
        self.assertEqual(toarrays([65534, 65535, 65536]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([3], dtype=numpy.int32), Primitive(numpy.array([65534, 65535, 65536], dtype=numpy.uint32))))
        self.assertEqual(toarrays([4294967294, 4294967295, 4294967296]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([3], dtype=numpy.int32), Primitive(numpy.array([4294967294, 4294967295, 4294967296], dtype=numpy.uint64))))
        self.assertEqual(toarrays([18446744073709551614, 18446744073709551615, 18446744073709551616]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([3], dtype=numpy.int32), Primitive(numpy.array([18446744073709551614, 18446744073709551615, 18446744073709551616], dtype=numpy.float64))))
        self.assertEqual(toarrays([-1, -2, -128]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([3], dtype=numpy.int32), Primitive(numpy.array([-1, -2, -128], dtype=numpy.int8))))
        self.assertEqual(toarrays([-127, -128, -129]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([3], dtype=numpy.int32), Primitive(numpy.array([-127, -128, -129], dtype=numpy.int16))))
        self.assertEqual(toarrays([-32767, -32768, -32769]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([3], dtype=numpy.int32), Primitive(numpy.array([-32767, -32768, -32769], dtype=numpy.int32))))
        self.assertEqual(toarrays([-2147483647, -2147483648, -2147483649]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([3], dtype=numpy.int32), Primitive(numpy.array([-2147483647, -2147483648, -2147483649], dtype=numpy.int64))))
        self.assertEqual(toarrays([-9223372036854775807, -9223372036854775808, -9223372036854775809]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([3], dtype=numpy.int32), Primitive(numpy.array([-9223372036854775807, -9223372036854775808, -9223372036854775809], dtype=numpy.float64))))
        self.assertEqual(toarrays([0, 1, 3.14]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([3], dtype=numpy.int32), Primitive(numpy.array([0, 1, 3.14], dtype=numpy.float64))))
        self.assertEqual(toarrays([0, 1, float("-inf")]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([3], dtype=numpy.int32), Primitive(numpy.array([0, 1, float("-inf")], dtype=numpy.float64))))
        self.assertEqual(toarrays([0, 1, float("inf")]), ListBeginEnd(numpy.array([0], dtype=numpy.int32), numpy.array([3], dtype=numpy.int32), Primitive(numpy.array([0, 1, float("inf")], dtype=numpy.float64))))
