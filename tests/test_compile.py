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
from plur.types.columns import columns2type
from plur.python import *
from plur.compile.code import rewrite

from plur.thirdparty.meta import dump_python_source

class TestCompile(unittest.TestCase):
    def runTest(self):
        pass

    def test_rewrite(self):
        arrays = toarrays("prefix", [1, 2, 3, 4, 5])
        tpe = columns2type(dict((n, a.dtype) for n, a in arrays.items()), "prefix")

        def f(xs):
            return xs[2]

        code, enclosedfcns, encloseddata, columns = rewrite(f, {"xs": tpe})
        print dump_python_source(code)
        print columns
