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

import sys
import unittest

import numpy

from plur.types import *
from plur.python.data import *
from plur.compile.code import *

class TestIntegration(unittest.TestCase):
    def runTest(self):
        pass

    def same(self, data, fcn):
        result = fcn(data)

        arrays = toarrays("prefix", data)
        tpe = arrays2type(arrays, "prefix")
        proxies = fromarrays("prefix", arrays)

        self.assertEqual(fcn(proxies), result)
        self.assertEqual(run(arrays, fcn, tpe), result)

    def test_primitive(self):
        self.same(3.14, lambda x: x + 99)
