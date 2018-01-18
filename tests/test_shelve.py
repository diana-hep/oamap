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

import os
import shutil
import tempfile
import unittest

import oamap.source.shelve
from oamap.proxy import tojson
from oamap.schema import *

class TestShelve(unittest.TestCase):
    def runTest(self):
        pass

    def test_simple(self):
        try:
            tmpdir = tempfile.mkdtemp()
            d = oamap.source.shelve.open(os.path.join(tmpdir, "database"))

            d["one"] = 1
            self.assertEqual(d.schema("one"), Primitive("uint8"))
            self.assertEqual(d["one"], 1)

            d["two"] = 3.14
            self.assertEqual(d.schema("two"), Primitive("f8"))
            self.assertEqual(d["two"], 3.14)

            d["three"] = [1, 2, 3, 4, 5]
            self.assertEqual(d.schema("three"), List(Primitive("uint8")))
            self.assertEqual(d["three"], [1, 2, 3, 4, 5])

            d["four"] = u"hello"
            self.assertEqual(d.schema("four"), List(Primitive("uint8"), name="UTF8String"))
            self.assertEqual(d["four"], u"hello")

            d["five"] = ["one", b"two", u"three"]
            self.assertEqual(d.schema("five"), List(List(Primitive("uint8"), nullable=True, name="UTF8String")))
            self.assertEqual(d["five"], [u"one", u"two", u"three"])

        finally:
            d.close()
            shutil.rmtree(tmpdir)
