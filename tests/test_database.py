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

    def test_data(self):
        db = InMemoryDatabase()
        db.fromdata("one", Record({"x": List("int32"), "y": List("float64")}), {"x": [1, 2, 3, 4, 5], "y": [1.1, 2.2, 3.3]})

        one = db.data.one
        self.assertEqual(one().x[0], 1)
        self.assertEqual(one().x[1], 2)
        self.assertEqual(one().x[2], 3)
        self.assertEqual(one().y[0], 1.1)
        self.assertEqual(one().y[1], 2.2)
        self.assertEqual(one().y[2], 3.3)

        # recasting
        db.data.two = one.project("x")
        two = db.data.two
        self.assertEqual(two[0], 1)
        self.assertEqual(two[1], 2)
        self.assertEqual(two[2], 3)
        self.assertEqual(two[3], 4)
        self.assertEqual(two[4], 5)

        db.data.two = one.drop("y")
        two = db.data.two
        self.assertEqual(two().x[0], 1)
        self.assertEqual(two().x[1], 2)
        self.assertEqual(two().x[2], 3)
        self.assertEqual(two().x[3], 4)
        self.assertEqual(two().x[4], 5)

        db.data.two = one.drop("y").keep("x")
        two = db.data.two
        self.assertEqual(two().x[0], 1)
        self.assertEqual(two().x[1], 2)
        self.assertEqual(two().x[2], 3)
        self.assertEqual(two().x[3], 4)
        self.assertEqual(two().x[4], 5)

        # transformation
        db.data.three = one.filter(lambda x: x % 2 == 0, at="x")
        three = db.data.three
        self.assertEqual(three().x, [2, 4])

        db.data.three = one.filter(lambda x: x > 1, at="x").filter(lambda x: x < 5, at="x")
        three = db.data.three
        self.assertEqual(three().x, [2, 3, 4])

        # action
        table = one.map(lambda x: x**2, at="x")
        self.assertEqual(table.result().tolist(), [1, 4, 9, 16, 25])

        summary = one.reduce(0, lambda x, tally: x + tally, at="x")
        self.assertEqual(summary.result(), sum([1, 2, 3, 4, 5]))

    def test_dataset(self):
        db = InMemoryDatabase()
        db.fromdata("one", List(Record({"x": "int32", "y": "float64"})), [{"x": 1, "y": 1.1}, {"x": 2, "y": 2.2}, {"x": 3, "y": 3.3}], [{"x": 4, "y": 4.4}, {"x": 5, "y": 5.5}, {"x": 6, "y": 6.6}])
        one = db.data.one
        self.assertEqual(one[0].x, 1)
        self.assertEqual(one[1].x, 2)
        self.assertEqual(one[2].x, 3)
        self.assertEqual(one[3].x, 4)
        self.assertEqual(one[4].x, 5)
        self.assertEqual(one[5].x, 6)
        self.assertEqual([obj.x for obj in one], [1, 2, 3, 4, 5, 6])
        self.assertEqual([obj.y for obj in one], [1.1, 2.2, 3.3, 4.4, 5.5, 6.6])
        self.assertEqual(oamap.operations.project(one.partition(0), "x"), [1, 2, 3])
        self.assertEqual(oamap.operations.project(one.partition(1), "x"), [4, 5, 6])

        # recasting
        db.data.two = one.project("x")
        two = db.data.two
        self.assertEqual(two.partition(0), [1, 2, 3])
        self.assertEqual(two.partition(1), [4, 5, 6])
        self.assertEqual([x for x in two], [1, 2, 3, 4, 5, 6])

        db.data.two = one.drop("y").project("x")
        two = db.data.two
        self.assertEqual([x for x in two], [1, 2, 3, 4, 5, 6])
        self.assertEqual(two.partition(0), [1, 2, 3])
        self.assertEqual(two.partition(1), [4, 5, 6])

        # transformation
        db.data.three = one.filter(lambda obj: obj.x % 2 == 0)
        three = db.data.three
        self.assertEqual([obj.x for obj in three], [2, 4, 6])
        self.assertEqual([obj.y for obj in three], [2.2, 4.4, 6.6])
        self.assertEqual(oamap.operations.project(three.partition(0), "x"), [2])
        self.assertEqual(oamap.operations.project(three.partition(1), "x"), [4, 6])

        db.data.three = one.filter(lambda obj: obj.x > 1).filter(lambda obj: obj.x < 6)
        three = db.data.three

        self.assertEqual([obj.x for obj in three], [2, 3, 4, 5])
        self.assertEqual([obj.y for obj in three], [2.2, 3.3, 4.4, 5.5])
        self.assertEqual(oamap.operations.project(three.partition(0), "x"), [2, 3])
        self.assertEqual(oamap.operations.project(three.partition(1), "x"), [4, 5])

        # action
        table = one.map(lambda obj: None if obj.x % 2 == 0 else (obj.x, obj.y, obj.x + obj.y))
        self.assertEqual(table.result().tolist(), [(1, 1.1, 2.1), (3, 3.3, 6.3), (5, 5.5, 10.5)])

        summary = one.reduce(0, lambda obj, tally: obj.x + tally)
        self.assertEqual(summary.result(), sum([1, 2, 3, 4, 5, 6]))

        # print
        # print "one"
        # for n, x in db._backends[db._namespace]._arrays[0].items():
        #     print db._backends[db._namespace]._refcounts[0][n], n, x

        del db.data.one
        # print "two"
        # for n, x in db._backends[db._namespace]._arrays[0].items():
        #     print db._backends[db._namespace]._refcounts[0][n], n, x

        del db.data.two
        # print "three"
        # for n, x in db._backends[db._namespace]._arrays[0].items():
        #     print db._backends[db._namespace]._refcounts[0][n], n, x

        del db.data.three
        # print "done"
        # for n, x in db._backends[db._namespace]._arrays[0].items():
        #     print db._backends[db._namespace]._refcounts[0][n], n, x

        self.assertEqual(len(db._backends[db._namespace]._refcounts.get(0, {})), 0)
        self.assertEqual(len(db._backends[db._namespace]._refcounts.get(1, {})), 0)
