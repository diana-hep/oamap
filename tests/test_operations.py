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

    def test_project(self):
        data = Record({"one": "int"}).fromdata({"one": 1})
        self.assertEqual(project(data, "one"), 1)

        data = List(Record({"one": "int"})).fromdata([{"one": 1}, {"one": 2}, {"one": 3}])
        self.assertEqual(project(data, "one"), [1, 2, 3])

        data = List(Record({"hey": Record({"one": "int"})})).fromdata([{"hey": {"one": 1}}, {"hey": {"one": 2}}, {"hey": {"one": 3}}])
        self.assertEqual(project(data, "hey/one"), [1, 2, 3])

        data = List(Record({"hey": List(Record({"one": "int"}))})).fromdata([{"hey": [{"one": 1}, {"one": 2}, {"one": 3}]}, {"hey": []}, {"hey": [{"one": 4}, {"one": 5}]}])
        self.assertEqual(project(data, "hey/one"), [[1, 2, 3], [], [4, 5]])

    def test_keep(self):
        data = Record({"x1": "int", "x2": "float", "y1": List("bool")}).fromdata({"x1": 1, "x2": 2.2, "y1": [False, True]})
        self.assertEqual(set(data.fields), set(["x1", "x2", "y1"]))
        self.assertEqual(set(keep(data, "x*").fields), set(["x1", "x2"]))

        data = List(Record({"x1": "int", "x2": "float", "y1": List("bool")})).fromdata([{"x1": 1, "x2": 1.1, "y1": []}, {"x1": 2, "x2": 2.2, "y1": [False]}, {"x1": 3, "x2": 3.3, "y1": [False, True]}])
        self.assertEqual(set(data[0].fields), set(["x1", "x2", "y1"]))
        self.assertEqual(set(keep(data, "x*")[0].fields), set(["x1", "x2"]))

        data = List(Record({"hey": Record({"x1": "int", "x2": "float", "y1": List("bool")})})).fromdata([{"hey": {"x1": 1, "x2": 1.1, "y1": []}}, {"hey": {"x1": 2, "x2": 2.2, "y1": [False]}}, {"hey": {"x1": 3, "x2": 3.3, "y1": [False, True]}}])
        self.assertEqual(set(data[0].hey.fields), set(["x1", "x2", "y1"]))
        self.assertEqual(set(keep(data, "hey/x*")[0].hey.fields), set(["x1", "x2"]))

        data = List(Record({"hey": List(Record({"x1": "int", "x2": "float", "y1": List("bool")}))})).fromdata([{"hey": [{"x1": 1, "x2": 1.1, "y1": []}, {"x1": 2, "x2": 2.2, "y1": [False]}, {"x1": 3, "x2": 3.3, "y1": [False, True]}]}, {"hey": []}, {"hey": [{"x1": 4, "x2": 4.4, "y1": [False, True, False]}, {"x1": 5, "x2": 5.5, "y1": [False, True, False, True]}]}])
        self.assertEqual(set(data[0].hey[0].fields), set(["x1", "x2", "y1"]))
        self.assertEqual(set(keep(data, "hey/x*")[0].hey[0].fields), set(["x1", "x2"]))

    def test_drop(self):
        data = Record({"x1": "int", "x2": "float", "y1": List("bool")}).fromdata({"x1": 1, "x2": 2.2, "y1": [False, True]})
        self.assertEqual(set(data.fields), set(["x1", "x2", "y1"]))
        self.assertEqual(set(drop(data, "x*").fields), set(["y1"]))

        data = List(Record({"x1": "int", "x2": "float", "y1": List("bool")})).fromdata([{"x1": 1, "x2": 1.1, "y1": []}, {"x1": 2, "x2": 2.2, "y1": [False]}, {"x1": 3, "x2": 3.3, "y1": [False, True]}])
        self.assertEqual(set(data[0].fields), set(["x1", "x2", "y1"]))
        self.assertEqual(set(drop(data, "x*")[0].fields), set(["y1"]))

        data = List(Record({"hey": Record({"x1": "int", "x2": "float", "y1": List("bool")})})).fromdata([{"hey": {"x1": 1, "x2": 1.1, "y1": []}}, {"hey": {"x1": 2, "x2": 2.2, "y1": [False]}}, {"hey": {"x1": 3, "x2": 3.3, "y1": [False, True]}}])
        self.assertEqual(set(data[0].hey.fields), set(["x1", "x2", "y1"]))
        self.assertEqual(set(drop(data, "hey/x*")[0].hey.fields), set(["y1"]))

        data = List(Record({"hey": List(Record({"x1": "int", "x2": "float", "y1": List("bool")}))})).fromdata([{"hey": [{"x1": 1, "x2": 1.1, "y1": []}, {"x1": 2, "x2": 2.2, "y1": [False]}, {"x1": 3, "x2": 3.3, "y1": [False, True]}]}, {"hey": []}, {"hey": [{"x1": 4, "x2": 4.4, "y1": [False, True, False]}, {"x1": 5, "x2": 5.5, "y1": [False, True, False, True]}]}])
        self.assertEqual(set(data[0].hey[0].fields), set(["x1", "x2", "y1"]))
        self.assertEqual(set(drop(data, "hey/x*")[0].hey[0].fields), set(["y1"]))

    def test_split_merge(self):
        data = Record({"hey": List(Record({"x1": "int", "x2": "float", "y1": List("bool")}))}).fromdata({"hey": [{"x1": 1, "x2": 1.1, "y1": []}, {"x1": 2, "x2": 2.2, "y1": [False]}, {"x1": 3, "x2": 3.3, "y1": [False, True]}]})
        self.assertEqual(data.hey[0].x1, 1)
        self.assertEqual(data.hey[0].x2, 1.1)
        self.assertEqual(data.hey[0].y1, [])
        new1 = split(data, "hey/x*")
        self.assertEqual(new1.x1[0], 1)
        self.assertEqual(new1.x2[0], 1.1)
        new2 = split(data, "hey/y1")
        self.assertEqual(new2.y1[0], [])

        undo1 = merge(new1, "hey", "x*")
        self.assertEqual(undo1.hey[0].x1, 1)
        self.assertEqual(undo1.hey[0].x2, 1.1)
        self.assertEqual(undo1.hey[0].y1, [])
        undo2 = merge(new2, "hey", "y1")
        self.assertEqual(undo2.hey[0].x1, 1)
        self.assertEqual(undo2.hey[0].x2, 1.1)
        self.assertEqual(undo2.hey[0].y1, [])

        undo3 = merge(new1, "horses", "x*")
        self.assertEqual(undo3.horses[0].x1, 1)
        self.assertEqual(undo3.horses[0].x2, 1.1)
        self.assertEqual(undo3.hey[0].y1, [])
        undo4 = merge(new2, "horses", "y1")
        self.assertEqual(undo4.hey[0].x1, 1)
        self.assertEqual(undo4.hey[0].x2, 1.1)
        self.assertEqual(undo4.horses[0].y1, [])

        data = List(Record({"hey": List(Record({"x1": "int", "x2": "float", "y1": List("bool")}))})).fromdata([{"hey": [{"x1": 1, "x2": 1.1, "y1": []}, {"x1": 2, "x2": 2.2, "y1": [False]}, {"x1": 3, "x2": 3.3, "y1": [False, True]}]}, {"hey": []}, {"hey": [{"x1": 4, "x2": 4.4, "y1": [False, True, False]}, {"x1": 5, "x2": 5.5, "y1": [False, True, False, True]}]}])
        self.assertEqual(data[0].hey[0].x1, 1)
        self.assertEqual(data[0].hey[0].x2, 1.1)
        self.assertEqual(data[0].hey[0].y1, [])
        new1 = split(data, "hey/x*")
        self.assertEqual(new1[0].x1[0], 1)
        self.assertEqual(new1[0].x2[0], 1.1)
        new2 = split(data, "hey/y1")
        self.assertEqual(new2[0].y1[0], [])

        undo1 = merge(new1, "hey", "x*")
        self.assertEqual(undo1[0].hey[0].x1, 1)
        self.assertEqual(undo1[0].hey[0].x2, 1.1)
        self.assertEqual(undo1[0].hey[0].y1, [])
        undo2 = merge(new2, "hey", "y1")
        self.assertEqual(undo2[0].hey[0].x1, 1)
        self.assertEqual(undo2[0].hey[0].x2, 1.1)
        self.assertEqual(undo2[0].hey[0].y1, [])

        undo3 = merge(new1, "horses", "x*")
        self.assertEqual(undo3[0].horses[0].x1, 1)
        self.assertEqual(undo3[0].horses[0].x2, 1.1)
        self.assertEqual(undo3[0].hey[0].y1, [])
        undo4 = merge(new2, "horses", "y1")
        self.assertEqual(undo4[0].hey[0].x1, 1)
        self.assertEqual(undo4[0].hey[0].x2, 1.1)
        self.assertEqual(undo4[0].horses[0].y1, [])

    def test_parent(self):
        data = List(Record({"hey": List(Record({"one": "int"}))})).fromdata([{"hey": [{"one": 1}, {"one": 2}, {"one": 3}]}, {"hey": []}, {"hey": [{"one": 4}, {"one": 5}]}])
        new = parent(data, "up", "hey")
        for x in new[0].hey:
            self.assertEqual(x.up._index, 0)
        for x in new[1].hey:
            self.assertEqual(x.up._index, 1)
        for x in new[2].hey:
            self.assertEqual(x.up._index, 2)

    def test_index(self):
        data = List(Record({"hey": List(Record({"one": "int"}))})).fromdata([{"hey": [{"one": 1}, {"one": 2}, {"one": 3}]}, {"hey": []}, {"hey": [{"one": 4}, {"one": 5}]}])
        new = index(data, "ind", "hey")
        self.assertEqual(new[0].hey[0].ind, 0)
        self.assertEqual(new[0].hey[1].ind, 1)
        self.assertEqual(new[0].hey[2].ind, 2)
        self.assertEqual(new[2].hey[0].ind, 0)
        self.assertEqual(new[2].hey[1].ind, 1)

    def test_tomask(self):
        nan = float("nan")

        data = Record({"one": "float"}).fromdata({"one": nan})
        self.assertTrue(math.isnan(data.one))
        data = tomask(data, "one", nan)
        self.assertEqual(data.one, None)

        data = List(Record({"one": "float"})).fromdata([{"one": nan}, {"one": 2}, {"one": 3}])
        self.assertTrue(math.isnan(data[0].one))
        self.assertEqual(data[1].one, 2)
        self.assertEqual(data[2].one, 3)
        data = tomask(data, "one", nan)
        self.assertEqual(data[0].one, None)
        data = tomask(data, "one", 2)
        self.assertEqual(data[1].one, None)
        data = tomask(data, "one", 2, 3)
        self.assertEqual(data[2].one, None)

        data = List(Record({"hey": Record({"one": "float"})})).fromdata([{"hey": {"one": nan}}, {"hey": {"one": 2}}, {"hey": {"one": 3}}])
        self.assertTrue(math.isnan(data[0].hey.one))
        self.assertEqual(data[1].hey.one, 2)
        self.assertEqual(data[2].hey.one, 3)
        data = tomask(data, "hey/one", nan)
        self.assertEqual(data[0].hey.one, None)
        data = tomask(data, "hey/one", 2)
        self.assertEqual(data[1].hey.one, None)
        data = tomask(data, "hey/one", 2, 3)
        self.assertEqual(data[2].hey.one, None)

        data = List(Record({"hey": List(Record({"one": "float"}))})).fromdata([{"hey": [{"one": nan}, {"one": 2}, {"one": 3}]}, {"hey": []}, {"hey": [{"one": 4}, {"one": 5}]}])
        self.assertTrue(math.isnan(data[0].hey[0].one))
        self.assertEqual(data[0].hey[1].one, 2)
        self.assertEqual(data[0].hey[2].one, 3)
        data = tomask(data, "hey/one", nan)
        self.assertEqual(data[0].hey[0].one, None)
        data = tomask(data, "hey/one", 2)
        self.assertEqual(data[0].hey[1].one, None)
        data = tomask(data, "hey/one", 2, 3)
        self.assertEqual(data[0].hey[2].one, None)
        
