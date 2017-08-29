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
from collections import namedtuple

import numpy

from plur.types import *
from plur.python.data import *
from plur.compile.code import *

class TestIntegration(unittest.TestCase):
    def runTest(self):
        pass

    def same(self, data, fcn, tpe=None, debug=False):
        result = fcn(data)
        if debug:
            print("\nEXPECTING RESULT: {0}\n".format(result))

        if tpe is None:
            arrays = toarrays("prefix", data)
        else:
            arrays = toarrays("prefix", data, tpe)
        tpe = arrays2type(arrays, "prefix")
        proxies = fromarrays("prefix", arrays)

        self.assertEqual(fcn(proxies), result)
        self.assertEqual(run(arrays, fcn, tpe, debug=debug), result)

    def test_primitive(self):
        self.same(3.14, lambda x: x + 99)

    def test_simplelist(self):
        self.same([5, 4, 3, 2, 1], lambda x: x[0] + x[1] + x[2] + x[3] + x[4])
        self.same([5, 4, 3, 2, 1], lambda x: len(x))
        def fcn(xs):
            out = 0
            for x in xs:
                out += x
            return out
        self.same([5, 4, 3, 2, 1], fcn)
        self.same([], fcn, List(float32))
        self.same([], lambda x: len(x), List(float32))

    def test_nestedlist(self):
        self.same([[3, 2, 1], [], [4, 5]], lambda x: x[0][0] + x[0][1] + x[0][2] + x[2][0] + x[2][1])
        self.same([[3, 2, 1], [], [4, 5]], lambda x: len(x))
        self.same([[3, 2, 1], [], [4, 5]], lambda x: len(x[0]))
        self.same([[3, 2, 1], [], [4, 5]], lambda x: len(x[1]))
        self.same([[3, 2, 1], [], [4, 5]], lambda x: len(x[2]))
        def fcn(xss):
            out = 0
            for xs in xss:
                for x in xs:
                    out += x
            return out
        self.same([[3, 2, 1], [], [4, 5]], fcn)
        self.same([[], [], []], fcn, List(List(float32)))
        self.same([], fcn, List(List(float32)))

    def test_record(self):
        onetwo = namedtuple("onetwo", ["one", "two"])
        self.same(onetwo(1, 2.2), lambda x: x.one + x.two)
        self.same([onetwo(1, 1.1), onetwo(2, 2.2)], lambda x: x[0].one + x[0].two + x[1].one + x[1].two)

        three = namedtuple("three", ["one", "two", "three"])
        self.same(three(1, 2.2, [3, 4, 5]), lambda x: x.one + x.two + x.three[0] + x.three[1] + x.three[2])
        self.same([three(1, 1.1, [1, 1, 1]), three(2, 2.2, [])], lambda x: x[0].one + x[0].two + x[0].three[0] + x[0].three[1] + x[0].three[2] + x[1].one + x[1].two)
        self.same([three(1, 1.1, [1, 1, 1]), three(2, 2.2, [99])], lambda x: x[0].one + x[0].two + x[0].three[0] + x[0].three[1] + x[0].three[2] + x[1].one + x[1].two + x[1].three[0])

    def test_reordered(self):
        data = [[3, 2, 1], [], [4, 5]]
        fcn = lambda x: x[0][0]*10000 + x[0][1]*1000 + x[0][2]*100 + x[2][0]*10 + x[2][1]*1
        self.same(data, fcn)

        result = fcn(data)
        arrays = toarrays("prefix", data)

        arrays["prefix-Lb"] = arrays["prefix-Lo"][:-1]
        arrays["prefix-Le"] = arrays["prefix-Lo"][1:]
        del arrays["prefix-Lo"]

        arrays["prefix-Ld-Lb"] = arrays["prefix-Ld-Lo"][:-1]
        arrays["prefix-Ld-Le"] = arrays["prefix-Ld-Lo"][1:]
        del arrays["prefix-Ld-Lo"]

        tpe = arrays2type(arrays, "prefix")
        proxies = fromarrays("prefix", arrays)
        self.assertEqual(fcn(proxies), result)
        self.assertEqual(run(arrays, fcn, tpe), result)
        
        arrays["prefix-Ld-Lb"] = numpy.array([2, 2, 0], dtype=numpy.int64)
        arrays["prefix-Ld-Le"] = numpy.array([5, 2, 2], dtype=numpy.int64)
        arrays["prefix-Ld-Ld"] = numpy.array([4, 5, 3, 2, 1], dtype=numpy.int64)

        tpe = arrays2type(arrays, "prefix")
        proxies = fromarrays("prefix", arrays)
        self.assertEqual(fcn(proxies), result)
        self.assertEqual(run(arrays, fcn, tpe), result)

    def test_rangeerror(self):
        data = [[3, 2, 1], [], [4, 5]]
        def fcn(x):
            return x[3]
        arrays = toarrays("prefix", data)
        tpe = arrays2type(arrays, "prefix")
        proxies = fromarrays("prefix", arrays)
        self.assertRaises(IndexError, lambda: fcn(proxies))
        self.assertRaises(IndexError, lambda: run(arrays, fcn, tpe))
        try:
            import numba
        except ImportError:
            pass
        else:
            self.assertRaises(IndexError, lambda: run(arrays, fcn, tpe, numba=True))

        def fcn(x):
            return x[2][2]
        arrays = toarrays("prefix", data)
        tpe = arrays2type(arrays, "prefix")
        proxies = fromarrays("prefix", arrays)
        self.assertRaises(IndexError, lambda: fcn(proxies))
        self.assertRaises(IndexError, lambda: run(arrays, fcn, tpe))
        try:
            import numba
        except ImportError:
            pass
        else:
            self.assertRaises(IndexError, lambda: run(arrays, fcn, tpe, numba=True))

        def fcn(x):
            return x[1][1]
        arrays = toarrays("prefix", data)
        tpe = arrays2type(arrays, "prefix")
        proxies = fromarrays("prefix", arrays)
        self.assertRaises(IndexError, lambda: fcn(proxies))
        self.assertRaises(IndexError, lambda: run(arrays, fcn, tpe))
        try:
            import numba
        except ImportError:
            pass
        else:
            self.assertRaises(IndexError, lambda: run(arrays, fcn, tpe, numba=True))

    def test_negativeindex(self):
        data = [[3, 2, 1], [], [4, 5]]
        def fcn(x):
            return x[-1][-1]
        arrays = toarrays("prefix", data)
        tpe = arrays2type(arrays, "prefix")
        proxies = fromarrays("prefix", arrays)
        self.assertEqual(fcn(proxies), 5)
        self.assertEqual(run(arrays, fcn, tpe), 5)
        try:
            import numba
        except ImportError:
            pass
        else:
            self.assertEqual(run(arrays, fcn, tpe, numba=True), 5)

        data = [[3, 2, 1], [], [4, 5]]
        def fcn(x):
            return x[-3][-2]
        arrays = toarrays("prefix", data)
        tpe = arrays2type(arrays, "prefix")
        proxies = fromarrays("prefix", arrays)
        self.assertEqual(fcn(proxies), 2)
        self.assertEqual(run(arrays, fcn, tpe), 2)
        try:
            import numba
        except ImportError:
            pass
        else:
            self.assertEqual(run(arrays, fcn, tpe, numba=True), 2)
