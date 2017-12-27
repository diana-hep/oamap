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

import oamap.inference
import oamap.fill
import oamap.proxy
from oamap.schema import *

class TestFill(unittest.TestCase):
    def runTest(self):
        pass

    def check(self, value, schema=None, debug=False):
        if schema is None:
            schema = oamap.inference.fromjson(value)
        if debug:
            print("schema: {0}".format(schema))
        arrays = oamap.fill.toarrays(oamap.fill.fromjson(value, schema))
        if debug:
            print("arrays: {0}".format(arrays))
        columnar = schema(arrays)
        if debug:
            print("columnar: {0}".format(columnar))
        value2 = oamap.proxy.tojson(columnar)
        self.assertEqual(value, value2)

    def test_Primitive(self):
        self.check(3)
        self.check(3.14)
        self.check({"real": 3, "imag": 4})
        self.check("inf")
        self.check("-inf")
        self.check("nan")
        self.check([[1, 2], [3, 4]], Primitive("i8", (2, 2)))

    def test_List(self):
        self.check([1, 2, 3])
