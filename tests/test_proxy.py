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

import numpy

from oamap.frompython import toarrays
from oamap.schema import *

class TestProxy(unittest.TestCase):
    def runTest(self):
        pass

    def test_primitives(self):
        self.assertEqual(toarrays(False).proxy(), False)
        self.assertEqual(toarrays(True).proxy(), True)

        self.assertEqual(toarrays(0).proxy(), 0)
        self.assertEqual(toarrays(255).proxy(), 255)
        self.assertEqual(toarrays(256).proxy(), 256)
        self.assertEqual(toarrays(65535).proxy(), 65535)
        self.assertEqual(toarrays(65536).proxy(), 65536)
        self.assertEqual(toarrays(4294967295).proxy(), 4294967295)
        self.assertEqual(toarrays(4294967296).proxy(), 4294967296)
        self.assertEqual(toarrays(18446744073709551615).proxy(), 18446744073709551615)
        self.assertEqual(toarrays(18446744073709551616).proxy(), 18446744073709551616)

        self.assertEqual(toarrays(-1).proxy(), -1)
        self.assertEqual(toarrays(-128).proxy(), -128)
        self.assertEqual(toarrays(-129).proxy(), -129)
        self.assertEqual(toarrays(-32768).proxy(), -32768)
        self.assertEqual(toarrays(-32769).proxy(), -32769)
        self.assertEqual(toarrays(-2147483648).proxy(), -2147483648)
        self.assertEqual(toarrays(-2147483649).proxy(), -2147483649)
        self.assertEqual(toarrays(-9223372036854775808).proxy(), -9223372036854775808)
        self.assertEqual(toarrays(-9223372036854775809).proxy(), float(-9223372036854775809))

        self.assertEqual(toarrays(0.0).proxy(), 0.0)
        self.assertEqual(toarrays(3.14).proxy(), 3.14)
        self.assertEqual(toarrays(float("-inf")).proxy(), float("-inf"))
        self.assertEqual(toarrays(float("inf")).proxy(), float("inf"))

        self.assertEqual(toarrays(1+1j).proxy(), 1+1j)

    def test_list1(self):
        self.assertEqual(toarrays([False]).proxy(), [False])
        self.assertEqual(toarrays([True]).proxy(), [True])

        self.assertEqual(toarrays([0]).proxy(), [0])
        self.assertEqual(toarrays([255]).proxy(), [255])
        self.assertEqual(toarrays([256]).proxy(), [256])
        self.assertEqual(toarrays([65535]).proxy(), [65535])
        self.assertEqual(toarrays([65536]).proxy(), [65536])
        self.assertEqual(toarrays([4294967295]).proxy(), [4294967295])
        self.assertEqual(toarrays([4294967296]).proxy(), [4294967296])
        self.assertEqual(toarrays([18446744073709551615]).proxy(), [18446744073709551615])
        self.assertEqual(toarrays([18446744073709551616]).proxy(), [18446744073709551616])

        self.assertEqual(toarrays([-1]).proxy(), [-1])
        self.assertEqual(toarrays([-128]).proxy(), [-128])
        self.assertEqual(toarrays([-129]).proxy(), [-129])
        self.assertEqual(toarrays([-32768]).proxy(), [-32768])
        self.assertEqual(toarrays([-32769]).proxy(), [-32769])
        self.assertEqual(toarrays([-2147483648]).proxy(), [-2147483648])
        self.assertEqual(toarrays([-2147483649]).proxy(), [-2147483649])
        self.assertEqual(toarrays([-9223372036854775808]).proxy(), [-9223372036854775808])
        self.assertEqual(toarrays([-9223372036854775809]).proxy(), [float(-9223372036854775809)])

        self.assertEqual(toarrays([float("-inf")]).proxy(), [float("-inf")])
        self.assertEqual(toarrays([float("inf")]).proxy(), [float("inf")])

        self.assertEqual(toarrays([1+1j]).proxy(), [1+1j])

    def test_list23(self):
        self.assertEqual(toarrays([0, 255]).proxy(), [0, 255])
        self.assertEqual(toarrays([255, 256]).proxy(), [255, 256])
        self.assertEqual(toarrays([65535, 65536]).proxy(), [65535, 65536])
        self.assertEqual(toarrays([4294967295, 4294967296]).proxy(), [4294967295, 4294967296])
        self.assertEqual(toarrays([18446744073709551615, 18446744073709551616]).proxy(), [18446744073709551615, 18446744073709551616])
        self.assertEqual(toarrays([-1, -128]).proxy(), [-1, -128])
        self.assertEqual(toarrays([-128, -129]).proxy(), [-128, -129])
        self.assertEqual(toarrays([-32768, -32769]).proxy(), [-32768, -32769])
        self.assertEqual(toarrays([-2147483648, -2147483649]).proxy(), [-2147483648, -2147483649])
        self.assertEqual(toarrays([-9223372036854775808, -9223372036854775809]).proxy(), [-9223372036854775808, float(-9223372036854775809)])
        self.assertEqual(toarrays([0, 3.14]).proxy(), [0, 3.14])
        self.assertEqual(toarrays([0, float("-inf")]).proxy(), [0, float("-inf")])
        self.assertEqual(toarrays([0, float("inf")]).proxy(), [0, float("inf")])

        self.assertEqual(toarrays([0, 1, 255]).proxy(), [0, 1, 255])
        self.assertEqual(toarrays([254, 255, 256]).proxy(), [254, 255, 256])
        self.assertEqual(toarrays([65534, 65535, 65536]).proxy(), [65534, 65535, 65536])
        self.assertEqual(toarrays([4294967294, 4294967295, 4294967296]).proxy(), [4294967294, 4294967295, 4294967296])
        self.assertEqual(toarrays([18446744073709551614, 18446744073709551615, 18446744073709551616]).proxy(), [18446744073709551614, 18446744073709551615, 18446744073709551616])
        self.assertEqual(toarrays([-1, -2, -128]).proxy(), [-1, -2, -128])
        self.assertEqual(toarrays([-127, -128, -129]).proxy(), [-127, -128, -129])
        self.assertEqual(toarrays([-32767, -32768, -32769]).proxy(), [-32767, -32768, -32769])
        self.assertEqual(toarrays([-2147483647, -2147483648, -2147483649]).proxy(), [-2147483647, -2147483648, -2147483649])
        self.assertEqual(toarrays([-9223372036854775807, -9223372036854775808, -9223372036854775809]).proxy(), [-9223372036854775807, -9223372036854775808, float(-9223372036854775809)])
        self.assertEqual(toarrays([0, 1, 3.14]).proxy(), [0, 1, 3.14])
        self.assertEqual(toarrays([0, 1, float("-inf")]).proxy(), [0, 1, float("-inf")])
        self.assertEqual(toarrays([0, 1, float("inf")]).proxy(), [0, 1, float("inf")])

    def test_record(self):
        self.assertEqual(toarrays({"one": 1, "two": 3.14}).proxy(), {"one": 1, "two": 3.14})

        self.assertEqual(toarrays([{"one": 1, "two": 3.14}]).proxy(), [{"one": 1, "two": 3.14}])
        self.assertEqual(toarrays([{"one": 1, "two": 3.14}, {"one": 2, "two": 99.9}]).proxy(), [{"one": 1, "two": 3.14}, {"one": 2, "two": 99.9}])
        self.assertEqual(toarrays([{"one": 1, "two": 3.14}, {"one": 2.71, "two": 99.9}]).proxy(), [{"one": 1, "two": 3.14}, {"one": 2.71, "two": 99.9}])
        self.assertEqual(toarrays([{"one": 1, "two": 3.14}, {"one": False, "two": 99.9}]).proxy(), [{"one": 1, "two": 3.14}, {"one": False, "two": 99.9}])
        self.assertEqual(toarrays([{"one": 1}, {"two": 3.14}]).proxy(), [{"one": 1}, {"two": 3.14}])
        self.assertEqual(toarrays([{"one": 1}, {"two": 3.14}, {"one": 2}]).proxy(), [{"one": 1}, {"two": 3.14}, {"one": 2}])
        self.assertEqual(toarrays([{"one": 1}, {"two": 3.14}, {"one": 2.71}]).proxy(), [{"one": 1}, {"two": 3.14}, {"one": 2.71}])
        self.assertEqual(toarrays([{"one": 1}, {"two": 3.14}, {"one": False}]).proxy(), [{"one": 1}, {"two": 3.14}, {"one": False}])
        self.assertEqual(toarrays([{"one": 1}, {"two": 3.14}, {"one": [0]}]).proxy(), [{"one": 1}, {"two": 3.14}, {"one": [0]}])
        self.assertEqual(toarrays([{"one": 1}, {"two": 3.14}, {"one": [0]}, {"one": []}]).proxy(), [{"one": 1}, {"two": 3.14}, {"one": [0]}, {"one": []}])

        one = namedtuple("one", ["one"])
        two = namedtuple("two", ["two"])
        onetwo = namedtuple("onetwo", ["one", "two"])

        self.assertEqual(toarrays(onetwo(1, 3.14)).proxy(), onetwo(1, 3.14))

        self.assertEqual(toarrays([onetwo(1, 3.14)]).proxy(), [onetwo(1, 3.14)])
        self.assertEqual(toarrays([onetwo(1, 3.14), onetwo(2, 99.9)]).proxy(), [onetwo(1, 3.14), onetwo(2, 99.9)])
        self.assertEqual(toarrays([onetwo(1, 3.14), onetwo(2.71, 99.9)]).proxy(), [onetwo(1, 3.14), onetwo(2.71, 99.9)])
        self.assertEqual(toarrays([onetwo(1, 3.14), onetwo(False, 99.9)]).proxy(), [onetwo(1, 3.14), onetwo(False, 99.9)])
        self.assertEqual(toarrays([one(1), two(3.14)]).proxy(), [one(1), two(3.14)])
        self.assertEqual(toarrays([one(1), two(3.14), one(2)]).proxy(), [one(1), two(3.14), one(2)])
        self.assertEqual(toarrays([one(1), two(3.14), one(2.71)]).proxy(), [one(1), two(3.14), one(2.71)])
        self.assertEqual(toarrays([one(1), two(3.14), one(False)]).proxy(), [one(1), two(3.14), one(False)])
        self.assertEqual(toarrays([one(1), two(3.14), one([0])]).proxy(), [one(1), two(3.14), one([0])])
        self.assertEqual(toarrays([one(1), two(3.14), one([0]), one([])]).proxy(), [one(1), two(3.14), one([0]), one([])])

    def test_uniondata(self):
        self.assertEqual(toarrays([0, False, 255]).proxy(), [0, False, 255])
        self.assertEqual(toarrays([255, False, 256]).proxy(), [255, False, 256])
        self.assertEqual(toarrays([65535, False, 65536]).proxy(), [65535, False, 65536])
        self.assertEqual(toarrays([4294967295, False, 4294967296]).proxy(), [4294967295, False, 4294967296])
        self.assertEqual(toarrays([18446744073709551615, False, 18446744073709551616]).proxy(), [18446744073709551615, False, 18446744073709551616])
        self.assertEqual(toarrays([-1, False, -128]).proxy(), [-1, False, -128])
        self.assertEqual(toarrays([-128, False, -129]).proxy(), [-128, False, -129])
        self.assertEqual(toarrays([-32768, False, -32769]).proxy(), [-32768, False, -32769])
        self.assertEqual(toarrays([-2147483648, False, -2147483649]).proxy(), [-2147483648, False, -2147483649])
        self.assertEqual(toarrays([-9223372036854775808, False, -9223372036854775809]).proxy(), [-9223372036854775808, False, float(-9223372036854775809)])
        self.assertEqual(toarrays([0, False, 3.14]).proxy(), [0, False, 3.14])
        self.assertEqual(toarrays([0, False, float("-inf")]).proxy(), [0, False, float("-inf")])
        self.assertEqual(toarrays([0, False, float("inf")]).proxy(), [0, False, float("inf")])

    def test_unionstructure(self):
        self.assertEqual(toarrays([0, [0], 255]).proxy(), [0, [0], 255])
        self.assertEqual(toarrays([255, [0], 256]).proxy(), [255, [0], 256])
        self.assertEqual(toarrays([65535, [0], 65536]).proxy(), [65535, [0], 65536])
        self.assertEqual(toarrays([4294967295, [0], 4294967296]).proxy(), [4294967295, [0], 4294967296])
        self.assertEqual(toarrays([18446744073709551615, [0], 18446744073709551616]).proxy(), [18446744073709551615, [0], 18446744073709551616])
        self.assertEqual(toarrays([-1, [0], -128]).proxy(), [-1, [0], -128])
        self.assertEqual(toarrays([-128, [0], -129]).proxy(), [-128, [0], -129])
        self.assertEqual(toarrays([-32768, [0], -32769]).proxy(), [-32768, [0], -32769])
        self.assertEqual(toarrays([-2147483648, [0], -2147483649]).proxy(), [-2147483648, [0], -2147483649])
        self.assertEqual(toarrays([-9223372036854775808, [0], -9223372036854775809]).proxy(), [-9223372036854775808, [0], float(-9223372036854775809)])
        self.assertEqual(toarrays([0, [0], 3.14]).proxy(), [0, [0], 3.14])
        self.assertEqual(toarrays([0, [0], float("-inf")]).proxy(), [0, [0], float("-inf")])
        self.assertEqual(toarrays([0, [0], float("inf")]).proxy(), [0, [0], float("inf")])

        self.assertEqual(toarrays([0, [0], [], 255]).proxy(), [0, [0], [], 255])
        self.assertEqual(toarrays([255, [0], [], 256]).proxy(), [255, [0], [], 256])
        self.assertEqual(toarrays([65535, [0], [], 65536]).proxy(), [65535, [0], [], 65536])
        self.assertEqual(toarrays([4294967295, [0], [], 4294967296]).proxy(), [4294967295, [0], [], 4294967296])
        self.assertEqual(toarrays([18446744073709551615, [0], [], 18446744073709551616]).proxy(), [18446744073709551615, [0], [], 18446744073709551616])
        self.assertEqual(toarrays([-1, [0], [], -128]).proxy(), [-1, [0], [], -128])
        self.assertEqual(toarrays([-128, [0], [], -129]).proxy(), [-128, [0], [], -129])
        self.assertEqual(toarrays([-32768, [0], [], -32769]).proxy(), [-32768, [0], [], -32769])
        self.assertEqual(toarrays([-2147483648, [0], [], -2147483649]).proxy(), [-2147483648, [0], [], -2147483649])
        self.assertEqual(toarrays([-9223372036854775808, [0], [], -9223372036854775809]).proxy(), [-9223372036854775808, [0], [], float(-9223372036854775809)])
        self.assertEqual(toarrays([0, [0], [], 3.14]).proxy(), [0, [0], [], 3.14])
        self.assertEqual(toarrays([0, [0], [], float("-inf")]).proxy(), [0, [0], [], float("-inf")])
        self.assertEqual(toarrays([0, [0], [], float("inf")]).proxy(), [0, [0], [], float("inf")])
