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

from oamap.schema import *
from oamap.operations import *

class TestOperations(unittest.TestCase):
    def runTest(self):
        pass

    def test_fieldname(self):
        data = Record({"one": "int"}).fromdata({"one": 1})
        self.assertEqual(data.one, 1)
        data = fieldname(data, "two", "one")
        self.assertEqual(data.two, 1)

        data = List(Record({"one": "int"})).fromdata([{"one": 1}, {"one": 2}, {"one": 3}])
        self.assertEqual([x.one for x in data], [1, 2, 3])
        data = fieldname(data, "two", "one")
        self.assertEqual([x.two for x in data], [1, 2, 3])

        data = List(Record({"hey": Record({"one": "int"})})).fromdata([{"hey": {"one": 1}}, {"hey": {"one": 2}}, {"hey": {"one": 3}}])
        self.assertEqual([x.hey.one for x in data], [1, 2, 3])
        data = fieldname(data, "two", "hey/one")
        self.assertEqual([x.hey.two for x in data], [1, 2, 3])

        data = List(Record({"hey": List(Record({"one": "int"}))})).fromdata([{"hey": [{"one": 1}, {"one": 2}, {"one": 3}]}, {"hey": []}, {"hey": [{"one": 4}, {"one": 5}]}])
        self.assertEqual([y.one for x in data for y in x.hey], [1, 2, 3, 4, 5])
        data = fieldname(data, "two", "hey/one")
        self.assertEqual([y.two for x in data for y in x.hey], [1, 2, 3, 4, 5])

    def test_recordname(self):
        data = Record({"one": "int"}).fromdata({"one": 1})
        self.assertEqual(data.name, None)
        data = recordname(data, "Event")
        self.assertEqual(data.name, "Event")

        data = List(Record({"one": "int"})).fromdata([{"one": 1}, {"one": 2}, {"one": 3}])
        self.assertEqual(data[0].name, None)
        data = recordname(data, "Event")
        self.assertEqual(data[0].name, "Event")

        data = List(Record({"hey": Record({"one": "int"})})).fromdata([{"hey": {"one": 1}}, {"hey": {"one": 2}}, {"hey": {"one": 3}}])
        self.assertEqual(data[0].hey.name, None)
        data = recordname(data, "Event", "hey")
        self.assertEqual(data[0].hey.name, "Event")

        data = List(Record({"hey": List(Record({"one": "int"}))})).fromdata([{"hey": [{"one": 1}, {"one": 2}, {"one": 3}]}, {"hey": []}, {"hey": [{"one": 4}, {"one": 5}]}])
        self.assertEqual(data[0].hey[0].name, None)
        data = recordname(data, "Event", "hey")
        self.assertEqual(data[0].hey[0].name, "Event")

