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

import math

import unittest

from oamap.schema import *
from oamap.database import *
from oamap.dataset import *
import oamap.operations

class TestDatabase(unittest.TestCase):
    def runTest(self):
        pass

    def test_dataset(self):
        backend = DictBackend({0: {"object-L-Fx-Di8": [1, 2, 1], "object-L-Fy-Di8": [4, 5, 6]},
                               1: {"object-L-Fx-Di8": [5, 1, 2], "object-L-Fy-Di8": [7, 6, 5]}},
                              {0: {"object-L-Fx-Di8": 1, "object-L-Fy-Di8": 1},
                               1: {"object-L-Fx-Di8": 1, "object-L-Fy-Di8": 1}})
        dataset = {"name": "object", "schema": List(Record({"x": "int", "y": "int"})).tojson(), "offsets": [0, 3, 6]}
        db = InMemoryDatabase(backends={"": backend}, namespace="", datasets={"one": dataset})

        one = db.data.one
        self.assertEqual(one[0].x, 1)
        self.assertEqual(one[1].x, 2)
        self.assertEqual(one[2].x, 1)
        self.assertEqual(one[3].x, 5)
        self.assertEqual(one[4].x, 1)
        self.assertEqual(one[5].x, 2)
        self.assertEqual([obj.x for obj in one], [1, 2, 1, 5, 1, 2])
        self.assertEqual([obj.y for obj in one], [4, 5, 6, 7, 6, 5])
        self.assertEqual(oamap.operations.project(one.partition(0), "x"), [1, 2, 1])
        self.assertEqual(oamap.operations.project(one.partition(1), "x"), [5, 1, 2])

        # # recasting
        # db.data.two = one.split("x", "y")
        # two = db.data.two
        # self.assertEqual([obj.x for obj in one], [1, 2, 1, 5, 1, 2])
        # self.assertEqual([obj.y for obj in one], [4, 5, 6, 7, 6, 5])

