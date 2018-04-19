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
from collections import namedtuple

import unittest

try:
    import numba
except ImportError:
    numba = None

from oamap.schema import *
from oamap.operations import *

Triple = namedtuple("Triple", ["one", "two", "three"])

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
        data = List(Record({"x1": "int", "x2": "float", "y1": List("bool")})).fromdata([{"x1": 1, "x2": 1.1, "y1": []}, {"x1": 2, "x2": 2.2, "y1": [False]}, {"x1": 3, "x2": 3.3, "y1": [False, True]}])
        self.assertEqual(data[0].x1, 1)
        self.assertEqual(data[0].x2, 1.1)
        self.assertEqual(data[0].y1, [])
        new1 = split(data, "x*")
        self.assertEqual(new1.x1[0], 1)
        self.assertEqual(new1.x2[0], 1.1)
        self.assertEqual(new1.original[0].y1, [])
        new2 = split(data, "y1")
        self.assertEqual(new2.original[0].x1, 1)
        self.assertEqual(new2.original[0].x2, 1.1)
        self.assertEqual(new2.y1[0], [])
        new3 = split(data, "*")
        self.assertEqual(new3.x1[0], 1)
        self.assertEqual(new3.x2[0], 1.1)
        self.assertEqual(new3.y1[0], [])

        undo1 = merge(new1, "original", "x*")
        self.assertEqual(undo1.original[0].x1, 1)
        self.assertEqual(undo1.original[0].x2, 1.1)
        self.assertEqual(undo1.original[0].y1, [])
        undo2 = merge(new2, "original", "y1")
        self.assertEqual(undo2.original[0].x1, 1)
        self.assertEqual(undo2.original[0].x2, 1.1)
        self.assertEqual(undo2.original[0].y1, [])
        undo3 = merge(new3, "original", "*")
        self.assertEqual(undo3.original[0].x1, 1)
        self.assertEqual(undo3.original[0].x2, 1.1)
        self.assertEqual(undo3.original[0].y1, [])

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
        
    def test_flatten(self):
        data = List(List("int")).fromdata([[1, 2, 3], [], [4, 5]])
        self.assertEqual(flatten(data), [1, 2, 3, 4, 5])

        data = Record({"x": List(List("int"))}).fromdata({"x": [[1, 2, 3], [], [4, 5]]})
        self.assertEqual(flatten(data, "x").x, [1, 2, 3, 4, 5])

        data = List(Record({"x": List(List("int"))})).fromdata([{"x": [[1, 2, 3], [], [4, 5]]}, {"x": []}, {"x": [[], [], []]}])
        new = flatten(data, "x")
        self.assertEqual(new[0].x, [1, 2, 3, 4, 5])
        self.assertEqual(new[1].x, [])
        self.assertEqual(new[2].x, [])

    def test_filter(self):
        data = List("int").fromdata([1, 2, 3, 4, 5])
        fcn = lambda x, y: x % 2 == y
        self.assertEqual(filter(data, fcn, 0, numba=False), [2, 4])
        self.assertEqual(filter(data, fcn, 0, numba={"nopython": True}), [2, 4])
        self.assertEqual(filter(data, fcn, 1, numba=False), [1, 3, 5])
        self.assertEqual(filter(data, fcn, 1, numba={"nopython": True}), [1, 3, 5])

        data = List("int").fromdata([1, 2, 3, 4, 5])
        self.assertEqual(filter(filter(data, lambda x: x > 1, numba=False), lambda x: x < 5, numba=False), [2, 3, 4])
        self.assertEqual(filter(filter(data, lambda x: x > 1, numba={"nopython": True}), lambda x: x < 5, numba={"nopython": True}), [2, 3, 4])

        data = List(List("int")).fromdata([[1, 2, 3], [], [4, 5]])
        self.assertEqual(filter(data, lambda obj: len(obj) > 0, numba=False), [[1, 2, 3], [4, 5]])
        self.assertEqual(filter(data, lambda obj: len(obj) > 0, numba={"nopython": True}), [[1, 2, 3], [4, 5]])

        data = List(Record({"x": "int"})).fromdata([{"x": 1}, {"x": 2}, {"x": 3}, {"x": 4}, {"x": 5}])
        self.assertEqual(len(filter(data, lambda obj: obj.x % 2 == 0, numba=False)), 2)
        self.assertEqual(len(filter(data, lambda obj: obj.x % 2 == 0, numba={"nopython": True})), 2)

        data = Record({"hey": List("int")}).fromdata({"hey": [1, 2, 3, 4, 5]})
        fcn = lambda x, y: x % 2 == y
        self.assertEqual(filter(data, fcn, 0, at="hey", numba=False).hey, [2, 4])
        self.assertEqual(filter(data, fcn, 0, at="hey", numba={"nopython": True}).hey, [2, 4])
        self.assertEqual(filter(data, fcn, 1, at="hey", numba=False).hey, [1, 3, 5])
        self.assertEqual(filter(data, fcn, 1, at="hey", numba={"nopython": True}).hey, [1, 3, 5])

        data = Record({"hey": List(List("int"))}).fromdata({"hey": [[1, 2, 3], [], [4, 5]]})
        self.assertEqual(filter(data, lambda obj: len(obj) > 0, at="hey", numba=False).hey, [[1, 2, 3], [4, 5]])
        self.assertEqual(filter(data, lambda obj: len(obj) > 0, at="hey", numba={"nopython": True}).hey, [[1, 2, 3], [4, 5]])

        data = Record({"hey": List(Record({"x": "int"}))}).fromdata({"hey": [{"x": 1}, {"x": 2}, {"x": 3}, {"x": 4}, {"x": 5}]})
        self.assertEqual(len(filter(data, lambda obj: obj.x % 2 == 0, at="hey", numba=False).hey), 2)
        self.assertEqual(len(filter(data, lambda obj: obj.x % 2 == 0, at="hey", numba={"nopython": True}).hey), 2)

    def test_define(self):
        data = Record({"x": "int"}).fromdata({"x": 5})
        fcn = lambda obj, y: obj.x + y
        self.assertEqual(define(data, "z", fcn, 10, numba=False).z, 15)
        self.assertEqual(define(data, "z", fcn, 10, numba={"nopython": True}).z, 15)

        data = List(Record({"x": "int"})).fromdata([{"x": 1}, {"x": 2}, {"x": 3}])
        new = define(data, "z", lambda obj: obj.x + 10, numba=False)
        self.assertEqual([obj.z for obj in new], [11, 12, 13])
        new = define(data, "z", lambda obj: obj.x + 10, numba={"nopython": True})
        self.assertEqual([obj.z for obj in new], [11, 12, 13])

        data = List(List(Record({"x": "int"}))).fromdata([[], [{"x": 1}, {"x": 2}, {"x": 3}], []])
        new = define(data, "z", lambda obj: obj.x + 10, numba=False)
        self.assertEqual(len(new[0]), 0)
        self.assertEqual([obj.z for obj in new[1]], [11, 12, 13])
        self.assertEqual(len(new[2]), 0)
        new = define(data, "z", lambda obj: obj.x + 10, numba={"nopython": True})
        self.assertEqual(len(new[0]), 0)
        self.assertEqual([obj.z for obj in new[1]], [11, 12, 13])
        self.assertEqual(len(new[2]), 0)

        data = List(Record({"hey": List(Record({"x": "int"}))})).fromdata([{"hey": []}, {"hey": [{"x": 1}, {"x": 2}, {"x": 3}]}, {"hey": []}])
        new = define(data, "z", lambda obj: obj.x + 10, at="hey", numba=False)
        self.assertEqual(len(new[0].hey), 0)
        self.assertEqual([obj.z for obj in new[1].hey], [11, 12, 13])
        self.assertEqual(len(new[2].hey), 0)
        new = define(data, "z", lambda obj: obj.x + 10, at="hey", numba={"nopython": True})
        self.assertEqual(len(new[0].hey), 0)
        self.assertEqual([obj.z for obj in new[1].hey], [11, 12, 13])
        self.assertEqual(len(new[2].hey), 0)

        data = List(Record({"hey": List(Record({"x": "int"}))})).fromdata([{"hey": []}, {"hey": [{"x": 1}, {"x": 2}, {"x": 3}]}, {"hey": []}])
        new = define(data, "z", lambda obj: None if obj.x % 2 == 0 else obj.x + 10, at="hey", numba=False)
        self.assertEqual([obj.z for obj in new[1].hey], [11, None, 13])
        new = define(data, "z", lambda obj: None if obj.x % 2 == 0 else obj.x + 10, at="hey", numba={"nopython": True})
        self.assertEqual([obj.z for obj in new[1].hey], [11, None, 13])
        
    def test_map(self):
        data = List(Record({"x": "int"})).fromdata([{"x": 1}, {"x": 2}, {"x": 3}])
        fcn = lambda obj, y: obj.x + y
        new = map(data, fcn, 10, numba=False)
        self.assertEqual(new.tolist(), [11, 12, 13])
        self.assertEqual(new.dtype, numpy.dtype(numpy.float64))
        new = map(data, fcn, 10, numba={"nopython": True})
        self.assertEqual(new.tolist(), [11, 12, 13])
        if numba is None:
            self.assertEqual(new.dtype, numpy.dtype(numpy.float64))
        else:
            self.assertEqual(new.dtype, numpy.dtype(numpy.int64))

        data = List(Record({"x": "int"})).fromdata([{"x": 1}, {"x": 2}, {"x": 3}])
        new = map(data, lambda obj: None if obj.x % 2 == 0 else obj.x + 10, numba=False)
        self.assertEqual(new.tolist(), [11, 13])
        self.assertEqual(new.dtype, numpy.dtype(numpy.float64))
        new = map(data, lambda obj: None if obj.x % 2 == 0 else obj.x + 10, numba={"nopython": True})
        self.assertEqual(new.tolist(), [11, 13])
        if numba is None:
            self.assertEqual(new.dtype, numpy.dtype(numpy.float64))
        else:
            self.assertEqual(new.dtype, numpy.dtype(numpy.int64))

        data = Record({"hey": List(Record({"x": "int", "y": "float"}))}).fromdata({"hey": [{"x": 1, "y": 1.1}, {"x": 2, "y": 2.2}, {"x": 3, "y": 3.3}]})
        new = map(data, lambda obj: (obj.x, obj.y, obj.x + obj.y), at="hey", numba=False)
        self.assertTrue(new.tolist(), [(1, 1.1, 2.1), (2, 2.2, 4.2), (3, 3.3, 6.3)])
        self.assertEqual(new.dtype[0], numpy.dtype(numpy.float64))
        self.assertEqual(new.dtype[1], numpy.dtype(numpy.float64))
        self.assertEqual(new.dtype[2], numpy.dtype(numpy.float64))
        self.assertEqual(new.dtype.names, ("f0", "f1", "f2"))
        new = map(data, lambda obj: (obj.x, obj.y, obj.x + obj.y), at="hey", numba={"nopython": True})
        self.assertTrue(new.tolist(), [(1, 1.1, 2.1), (2, 2.2, 4.2), (3, 3.3, 6.3)])
        if numba is None:
            self.assertEqual(new.dtype[0], numpy.dtype(numpy.float64))
        else:
            self.assertEqual(new.dtype[0], numpy.dtype(numpy.int64))
        self.assertEqual(new.dtype[1], numpy.dtype(numpy.float64))
        self.assertEqual(new.dtype[2], numpy.dtype(numpy.float64))
        self.assertEqual(new.dtype.names, ("f0", "f1", "f2"))

        data = List(Record({"hey": List(Record({"x": "int", "y": "float"}))})).fromdata([{"hey": [{"x": 1, "y": 1.1}, {"x": 2, "y": 2.2}, {"x": 3, "y": 3.3}]}, {"hey": []}, {"hey": [{"x": 4, "y": 4.4}, {"x": 5, "y": 5.5}]}])
        new = map(data, lambda obj: (obj.x, obj.y, obj.x + obj.y), at="hey", numba=False)
        self.assertTrue(new.tolist(), [(1, 1.1, 2.1), (2, 2.2, 4.2), (3, 3.3, 6.3), (4, 4.4, 8.4), (5, 5.5, 10.5)])
        self.assertEqual(new.dtype[0], numpy.dtype(numpy.float64))
        self.assertEqual(new.dtype[1], numpy.dtype(numpy.float64))
        self.assertEqual(new.dtype[2], numpy.dtype(numpy.float64))
        self.assertEqual(new.dtype.names, ("f0", "f1", "f2"))
        new = map(data, lambda obj: (obj.x, obj.y, obj.x + obj.y), at="hey", numba={"nopython": True})
        self.assertTrue(new.tolist(), [(1, 1.1, 2.1), (2, 2.2, 4.2), (3, 3.3, 6.3), (4, 4.4, 8.4), (5, 5.5, 10.5)])
        if numba is None:
            self.assertEqual(new.dtype[0], numpy.dtype(numpy.float64))
        else:
            self.assertEqual(new.dtype[0], numpy.dtype(numpy.int64))
        self.assertEqual(new.dtype[1], numpy.dtype(numpy.float64))
        self.assertEqual(new.dtype[2], numpy.dtype(numpy.float64))
        self.assertEqual(new.dtype.names, ("f0", "f1", "f2"))

        data = List(Record({"hey": List(Record({"x": "int", "y": "float"}))})).fromdata([{"hey": [{"x": 1, "y": 1.1}, {"x": 2, "y": 2.2}, {"x": 3, "y": 3.3}]}, {"hey": []}, {"hey": [{"x": 4, "y": 4.4}, {"x": 5, "y": 5.5}]}])
        new = map(data, lambda obj: Triple(obj.x, obj.y, obj.x + obj.y), at="hey", numba=False)
        self.assertTrue(new.tolist(), [(1, 1.1, 2.1), (2, 2.2, 4.2), (3, 3.3, 6.3), (4, 4.4, 8.4), (5, 5.5, 10.5)])
        self.assertEqual(new.dtype[0], numpy.dtype(numpy.float64))
        self.assertEqual(new.dtype[1], numpy.dtype(numpy.float64))
        self.assertEqual(new.dtype[2], numpy.dtype(numpy.float64))
        self.assertEqual(new.dtype.names, ("one", "two", "three"))
        new = map(data, lambda obj: Triple(obj.x, obj.y, obj.x + obj.y), at="hey", numba={"nopython": True})
        self.assertTrue(new.tolist(), [(1, 1.1, 2.1), (2, 2.2, 4.2), (3, 3.3, 6.3), (4, 4.4, 8.4), (5, 5.5, 10.5)])
        if numba is None:
            self.assertEqual(new.dtype[0], numpy.dtype(numpy.float64))
        else:
            self.assertEqual(new.dtype[0], numpy.dtype(numpy.int64))
        self.assertEqual(new.dtype[1], numpy.dtype(numpy.float64))
        self.assertEqual(new.dtype[2], numpy.dtype(numpy.float64))
        self.assertEqual(new.dtype.names, ("one", "two", "three"))

        data = List(Record({"hey": List(Record({"x": "int", "y": "float"}))})).fromdata([{"hey": [{"x": 1, "y": 1.1}, {"x": 2, "y": 2.2}, {"x": 3, "y": 3.3}]}, {"hey": []}, {"hey": [{"x": 4, "y": 4.4}, {"x": 5, "y": 5.5}]}])
        new = map(data, lambda obj: None if obj.x % 2 == 0 else (obj.x, obj.y, obj.x + obj.y), at="hey", numba=False)
        self.assertTrue(new.tolist(), [(1, 1.1, 2.1), (3, 3.3, 6.3), (5, 5.5, 10.5)])
        self.assertEqual(new.dtype[0], numpy.dtype(numpy.float64))
        self.assertEqual(new.dtype[1], numpy.dtype(numpy.float64))
        self.assertEqual(new.dtype[2], numpy.dtype(numpy.float64))
        self.assertEqual(new.dtype.names, ("f0", "f1", "f2"))
        new = map(data, lambda obj: None if obj.x % 2 == 0 else (obj.x, obj.y, obj.x + obj.y), at="hey", numba={"nopython": True})
        self.assertTrue(new.tolist(), [(1, 1.1, 2.1), (3, 3.3, 6.3), (5, 5.5, 10.5)])
        if numba is None:
            self.assertEqual(new.dtype[0], numpy.dtype(numpy.float64))
        else:
            self.assertEqual(new.dtype[0], numpy.dtype(numpy.int64))
        self.assertEqual(new.dtype[1], numpy.dtype(numpy.float64))
        self.assertEqual(new.dtype[2], numpy.dtype(numpy.float64))
        self.assertEqual(new.dtype.names, ("f0", "f1", "f2"))

        data = List(Record({"hey": List(Record({"x": "int", "y": "float"}))})).fromdata([{"hey": [{"x": 1, "y": 1.1}, {"x": 2, "y": 2.2}, {"x": 3, "y": 3.3}]}, {"hey": []}, {"hey": [{"x": 4, "y": 4.4}, {"x": 5, "y": 5.5}]}])
        new = map(data, lambda obj: None if obj.x % 2 == 0 else Triple(obj.x, obj.y, obj.x + obj.y), at="hey", numba=False)
        self.assertTrue(new.tolist(), [(1, 1.1, 2.1), (3, 3.3, 6.3), (5, 5.5, 10.5)])
        self.assertEqual(new.dtype[0], numpy.dtype(numpy.float64))
        self.assertEqual(new.dtype[1], numpy.dtype(numpy.float64))
        self.assertEqual(new.dtype[2], numpy.dtype(numpy.float64))
        self.assertEqual(new.dtype.names, ("one", "two", "three"))
        new = map(data, lambda obj: None if obj.x % 2 == 0 else Triple(obj.x, obj.y, obj.x + obj.y), at="hey", numba={"nopython": True})
        self.assertTrue(new.tolist(), [(1, 1.1, 2.1), (3, 3.3, 6.3), (5, 5.5, 10.5)])
        if numba is None:
            self.assertEqual(new.dtype[0], numpy.dtype(numpy.float64))
        else:
            self.assertEqual(new.dtype[0], numpy.dtype(numpy.int64))
        self.assertEqual(new.dtype[1], numpy.dtype(numpy.float64))
        self.assertEqual(new.dtype[2], numpy.dtype(numpy.float64))
        self.assertEqual(new.dtype.names, ("one", "two", "three"))

    def test_reduce(self):
        data = List("int").fromdata([1, 2, 3, 4, 5])
        fcn = lambda x, tally, y: x + tally + y
        self.assertEqual(reduce(data, 0, fcn, 0, numba=False), 15)
        self.assertEqual(reduce(data, 0, fcn, 1, numba=False), 20)
        self.assertEqual(reduce(data, 0, fcn, 0, numba={"nopython": True}), 15)
        self.assertEqual(reduce(data, 0, fcn, 1, numba={"nopython": True}), 20)

        data = List(Record({"x": "int"})).fromdata([{"x": 1}, {"x": 2}, {"x": 3}, {"x": 4}, {"x": 5}])
        self.assertEqual(reduce(data, 0, lambda obj, tally: obj.x + tally, numba=False), 15)
        self.assertEqual(reduce(data, 0, lambda obj, tally: obj.x + tally, numba={"nopython": True}), 15)

        data = Record({"hey": List(Record({"x": "int"}))}).fromdata({"hey": [{"x": 1}, {"x": 2}, {"x": 3}, {"x": 4}, {"x": 5}]})
        self.assertEqual(reduce(data, 0, lambda obj, tally: obj.x + tally, at="hey", numba=False), 15)
        self.assertEqual(reduce(data, 0, lambda obj, tally: obj.x + tally, at="hey", numba={"nopython": True}), 15)

        data = List(Record({"hey": List(Record({"x": "int"}))})).fromdata([{"hey": [{"x": 1}, {"x": 2}, {"x": 3}]}, {"hey": []}, {"hey": [{"x": 4}, {"x": 5}]}])
        self.assertEqual(reduce(data, 0, lambda obj, tally: obj.x + tally, at="hey", numba=False), 15)
        self.assertEqual(reduce(data, 0, lambda obj, tally: obj.x + tally, at="hey", numba={"nopython": True}), 15)
