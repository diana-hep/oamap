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

