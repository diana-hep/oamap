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

from rolup.typesystem import *

class TestTypesystem(unittest.TestCase):
    def runTest(self):
        pass

    def test_contain_element_primitives(self):
        inf = float("inf")
        nan = float("nan")

        self.assertTrue(False in boolean)
        self.assertTrue(True in boolean)
        self.assertTrue(0 not in boolean)
        self.assertTrue(1 not in boolean)
        self.assertTrue(0.0 not in boolean)
        self.assertTrue(inf not in boolean)
        self.assertTrue(-inf not in boolean)
        self.assertTrue(nan not in boolean)
        self.assertTrue(1+1j not in boolean)
        self.assertTrue(inf+1j not in boolean)

        self.assertTrue(0 in int8)
        self.assertTrue(127 in int8)
        self.assertTrue(128 not in int8)
        self.assertTrue(-128 in int8)
        self.assertTrue(-129 not in int8)
        self.assertTrue(0.0 not in int8)
        self.assertTrue(inf not in int8)
        self.assertTrue(-inf not in int8)
        self.assertTrue(nan not in int8)
        self.assertTrue(1+1j not in int8)
        self.assertTrue(inf+1j not in int8)
        self.assertTrue(False not in int8)
        self.assertTrue(True not in int8)

        self.assertTrue(0 in int16)
        self.assertTrue(32767 in int16)
        self.assertTrue(32768 not in int16)
        self.assertTrue(-32768 in int16)
        self.assertTrue(-32769 not in int16)
        self.assertTrue(0.0 not in int16)
        self.assertTrue(inf not in int16)
        self.assertTrue(-inf not in int16)
        self.assertTrue(nan not in int16)
        self.assertTrue(1+1j not in int16)
        self.assertTrue(inf+1j not in int16)
        self.assertTrue(False not in int16)
        self.assertTrue(True not in int16)

        self.assertTrue(0 in int32)
        self.assertTrue(2147483647 in int32)
        self.assertTrue(2147483648 not in int32)
        self.assertTrue(-2147483648 in int32)
        self.assertTrue(-2147483649 not in int32)
        self.assertTrue(0.0 not in int32)
        self.assertTrue(inf not in int32)
        self.assertTrue(-inf not in int32)
        self.assertTrue(nan not in int32)
        self.assertTrue(1+1j not in int32)
        self.assertTrue(inf+1j not in int32)
        self.assertTrue(False not in int32)
        self.assertTrue(True not in int32)

        self.assertTrue(0 in int64)
        self.assertTrue(9223372036854775807 in int64)
        self.assertTrue(9223372036854775808 not in int64)
        self.assertTrue(-9223372036854775808 in int64)
        self.assertTrue(-9223372036854775809 not in int64)
        self.assertTrue(0.0 not in int64)
        self.assertTrue(inf not in int64)
        self.assertTrue(-inf not in int64)
        self.assertTrue(nan not in int64)
        self.assertTrue(1+1j not in int64)
        self.assertTrue(inf+1j not in int64)
        self.assertTrue(False not in int64)
        self.assertTrue(True not in int64)

        self.assertTrue(0 in uint8)
        self.assertTrue(255 in uint8)
        self.assertTrue(256 not in uint8)
        self.assertTrue(-1 not in uint8)
        self.assertTrue(0.0 not in uint8)
        self.assertTrue(inf not in uint8)
        self.assertTrue(-inf not in uint8)
        self.assertTrue(nan not in uint8)
        self.assertTrue(1+1j not in uint8)
        self.assertTrue(inf+1j not in uint8)
        self.assertTrue(False not in uint8)
        self.assertTrue(True not in uint8)

        self.assertTrue(0 in uint16)
        self.assertTrue(65535 in uint16)
        self.assertTrue(65536 not in uint16)
        self.assertTrue(-1 not in uint16)
        self.assertTrue(0.0 not in uint16)
        self.assertTrue(inf not in uint16)
        self.assertTrue(-inf not in uint16)
        self.assertTrue(nan not in uint16)
        self.assertTrue(1+1j not in uint16)
        self.assertTrue(inf+1j not in uint16)
        self.assertTrue(False not in uint16)
        self.assertTrue(True not in uint16)

        self.assertTrue(0 in uint32)
        self.assertTrue(4294967295 in uint32)
        self.assertTrue(4294967296 not in uint32)
        self.assertTrue(-1 not in uint32)
        self.assertTrue(0.0 not in uint32)
        self.assertTrue(inf not in uint32)
        self.assertTrue(-inf not in uint32)
        self.assertTrue(nan not in uint32)
        self.assertTrue(1+1j not in uint32)
        self.assertTrue(inf+1j not in uint32)
        self.assertTrue(False not in uint32)
        self.assertTrue(True not in uint32)

        self.assertTrue(0 in uint64)
        self.assertTrue(18446744073709551615 in uint64)
        self.assertTrue(18446744073709551616 not in uint64)
        self.assertTrue(-1 not in uint64)
        self.assertTrue(0.0 not in uint64)
        self.assertTrue(inf not in uint64)
        self.assertTrue(-inf not in uint64)
        self.assertTrue(nan not in uint64)
        self.assertTrue(1+1j not in uint64)
        self.assertTrue(inf+1j not in uint64)
        self.assertTrue(False not in uint64)
        self.assertTrue(True not in uint64)

        self.assertTrue(0.0 in float32)
        self.assertTrue(1.0 in float32)
        self.assertTrue(inf in float32)
        self.assertTrue(-inf in float32)
        self.assertTrue(nan in float32)
        self.assertTrue(1+1j not in float32)
        self.assertTrue(inf+1j not in float32)
        self.assertTrue(False not in float32)
        self.assertTrue(True not in float32)

        self.assertTrue(0.0 in float64)
        self.assertTrue(1.0 in float64)
        self.assertTrue(inf in float64)
        self.assertTrue(-inf in float64)
        self.assertTrue(nan in float64)
        self.assertTrue(1+1j not in float64)
        self.assertTrue(inf+1j not in float64)
        self.assertTrue(False not in float64)
        self.assertTrue(True not in float64)

        self.assertTrue(0.0 in float128)
        self.assertTrue(1.0 in float128)
        self.assertTrue(inf in float128)
        self.assertTrue(-inf in float128)
        self.assertTrue(nan in float128)
        self.assertTrue(1+1j not in float128)
        self.assertTrue(inf+1j not in float128)
        self.assertTrue(False not in float128)
        self.assertTrue(True not in float128)

        self.assertTrue(0.0 in complex64)
        self.assertTrue(1.0 in complex64)
        self.assertTrue(inf in complex64)
        self.assertTrue(-inf in complex64)
        self.assertTrue(nan in complex64)
        self.assertTrue(1+1j in complex64)
        self.assertTrue(inf+1j in complex64)
        self.assertTrue(False not in complex64)
        self.assertTrue(True not in complex64)

        self.assertTrue(0.0 in complex128)
        self.assertTrue(1.0 in complex128)
        self.assertTrue(inf in complex128)
        self.assertTrue(-inf in complex128)
        self.assertTrue(nan in complex128)
        self.assertTrue(1+1j in complex128)
        self.assertTrue(inf+1j in complex128)
        self.assertTrue(False not in complex128)
        self.assertTrue(True not in complex128)

        self.assertTrue(0.0 in complex256)
        self.assertTrue(1.0 in complex256)
        self.assertTrue(inf in complex256)
        self.assertTrue(-inf in complex256)
        self.assertTrue(nan in complex256)
        self.assertTrue(1+1j in complex256)
        self.assertTrue(inf+1j in complex256)
        self.assertTrue(False not in complex256)
        self.assertTrue(True not in complex256)

    def test_contain_set_primitives(self):
        boolean in boolean
        boolean not in int8
        boolean not in int16
        boolean not in int32
        boolean not in int64
        boolean not in uint8
        boolean not in uint16
        boolean not in uint32
        boolean not in uint64
        boolean not in float32
        boolean not in float64
        boolean not in float128
        boolean not in complex64
        boolean not in complex128
        boolean not in complex256

        int8 not in boolean
        int8 in int8
        int8 in int16
        int8 in int32
        int8 in int64
        int8 not in uint8
        int8 not in uint16
        int8 not in uint32
        int8 not in uint64
        int8 in float32
        int8 in float64
        int8 in float128
        int8 in complex64
        int8 in complex128
        int8 in complex256

        # int16 in boolean
        # int16 in int8
        # int16 in int16
        # int16 in int32
        # int16 in int64
        # int16 not in uint8
        # int16 not in uint16
        # int16 not in uint32
        # int16 not in uint64
        # int16 in float32
        # int16 in float64
        # int16 in float128
        # int16 in complex64
        # int16 in complex128
        # int16 in complex256
