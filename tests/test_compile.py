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
from plur.types.columns import arrays2type
from plur.python import *
from plur.compile import *
from plur.compile.code import fcn2syntaxtree, rewrite, compilefcn, callfcn

from plur.thirdparty.meta import dump_python_source

class TestCompile(unittest.TestCase):
    def runTest(self):
        pass

    def test_rewrite(self):
        def same(data, fcn, testsets, debug=False):
            arrays = toarrays("prefix", data)
            tpe = arrays2type(arrays, "prefix")
            if debug:
                print("\n\nDATA: {0}".format(data))
                print("\nTYPE: {0}".format(tpe))

            code, arrayparams, enclosedfcns, encloseddata = rewrite(fcn, (tpe,))
            if debug:
                print("\nBEFORE:\n{0}\nAFTER:\n{1}".format(
                    dump_python_source(fcn2syntaxtree(fcn)), dump_python_source(code)))
                for x in arrayparams:
                    print("{0}\t{1}".format(x, arrays[x]))
                print("")

            newfcn = compilefcn(code, code.name, fcn.__code__.co_filename)

            for otherargs in testsets:
                if not isinstance(otherargs, (list, tuple)):
                    otherargs = (otherargs,)

                out1 = callfcn(arrays, newfcn, arrayparams, *otherargs)
                out2 = fcn(data, *otherargs)
                if debug:
                    print("otherargs == {0} --> {1} vs {2}".format(otherargs, out1, out2))

                if not out1 == out2:
                    raise AssertionError("failed for otherargs == {0}: {1} vs {2}\n{3}\n{4}".format(
                        otherargs, out1, out2, dump_python_source(fcn2syntaxtree(fcn)), dump_python_source(code)))

        same(3, lambda x, y: x + y, [1.1, 2.2, 3.3])
        same([3, 2, 1], lambda x, i, y: x[i] + y, [(i, y) for i in range(3) for y in [1.1, 2.2, 3.3]])
        same([[], [1, 2], [3, 4, 5]], lambda x, i, j, y: x[i][j] + y, [(i, j, y) for i, j in [(1, 0), (1, 1), (2, 0), (2, 1), (2, 2)] for y in [1.1, 2.2, 3.3]])
        same([[[], [1, 2], [3, 4, 5]]], lambda x, i, j, y: x[0][i][j] + y, [(i, j, y) for i, j in [(1, 0), (1, 1), (2, 0), (2, 1), (2, 2)] for y in [1.1, 2.2, 3.3]])

        def check_only_union(data, debug=False):
            arrays = toarrays("prefix", data, Union(boolean, float64))
            tpe = arrays2type(arrays, "prefix")
            fcn = lambda x: x
            code, arrayparams, enclosedfcns, encloseddata = rewrite(fcn, (tpe,))
            if debug:
                print("\nBEFORE:\n{0}\nAFTER:\n{1}".format(
                    dump_python_source(fcn2syntaxtree(fcn)), dump_python_source(code)))
                for x in arrayparams:
                    print("{0}\t{1}".format(x, arrays[x]))
                print("")
                print(tpe)
                print("")
            self.assertEqual(callfcn(arrays, compilefcn(code, code.name, fcn.__code__.co_filename), arrayparams), data)

        check_only_union(False)
        check_only_union(3.14)
        check_only_union(True)
        check_only_union(99.9)

        same([False, 3.14, True, 99.9], lambda x, i: x[i], [0, 1, 2, 3])
        same([[False, True], [1.1, 2.2]], lambda x, i, j: x[i][j], [(0, 0), (0, 1), (1, 0), (1, 1)])

        T = namedtuple("T", ["one", "two"])

        same(T(False, 3.14), lambda x, i: x.one if i == 0 else x.two, [0, 1])

        same([T(False, 1.1), T(True, 2.2), T(False, 3.3)], lambda x, i, j: x[j].one if i == 0 else x[j].two, [(i, j) for j in range(3) for i in range(2)])
        same([[T(False, 1.1), T(True, 2.2), T(False, 3.3)]], lambda x, i, j: x[0][j].one if i == 0 else x[0][j].two, [(i, j) for j in range(3) for i in range(2)])
        same([T([False], 1.1), T([True], 2.2), T([False], 3.3)], lambda x, i, j: x[j].one[0] if i == 0 else x[j].two, [(i, j) for j in range(3) for i in range(2)])
        same([T(False, [1.1]), T(True, [2.2]), T(False, [3.3])], lambda x, i, j: x[j].one if i == 0 else x[j].two[0], [(i, j) for j in range(3) for i in range(2)])
        same([T([False], [1.1]), T([True], [2.2]), T([False], [3.3])], lambda x, i, j: x[j].one[0] if i == 0 else x[j].two[0], [(i, j) for j in range(3) for i in range(2)])

        same([T(False, []), T(True, [1, 2]), T(False, [3, 4, 5])], lambda x, j, k: x[j].two[k], [(1, 0), (1, 1), (2, 0), (2, 1), (2, 2)])
        same([[T(False, []), T(True, [1, 2]), T(False, [3, 4, 5])]], lambda x, j, k: x[0][j].two[k], [(1, 0), (1, 1), (2, 0), (2, 1), (2, 2)])
        same([T(False, [[]]), T(True, [[1, 2]]), T(False, [[3, 4, 5]])], lambda x, j, k: x[j].two[0][k], [(1, 0), (1, 1), (2, 0), (2, 1), (2, 2)])
        same([T(False, []), T(True, [[1, 2]]), T(False, [[3, 4, 5]])], lambda x, j, k: x[j].two[0][k], [(1, 0), (1, 1), (2, 0), (2, 1), (2, 2)])
        same([T(False, []), T(True, [[1], [2]]), T(False, [[3], [4], [5]])], lambda x, j, k: x[j].two[k][0], [(1, 0), (1, 1), (2, 0), (2, 1), (2, 2)])

        same([T(False, []), T(True, [1, 2]), T(False, [3, 4, 5])], lambda x, i, j, k: x[j].one if i == 0 else x[j].two[k], [(0, 1, 0), (0, 1, 1), (0, 2, 0), (0, 2, 1), (0, 2, 2), (1, 1, 0), (1, 1, 1), (1, 2, 0), (1, 2, 1), (1, 2, 2)])

        same([T(False, 1.1), T(True, False), T(False, 3.3)], lambda x, i, j: x[j].one if i == 0 else x[j].two, [(i, j) for j in range(3) for i in range(2)])

        T2 = namedtuple("T2", ["three", "one"])

        def f(x, i):
            if i == 0:
                return x.one.three
            elif i == 1:
                return x.one.one
            elif i == 2:
                return x.two.three
            else:
                return x.two.one

        same(T(T2(False, 3.14), T2(True, 99.9)), f, [0, 1, 2, 3])

        def f(x, i, j):
            if i == 0:
                return x.one[j].three
            elif i == 1:
                return x.one[j].one
            elif i == 2:
                return x.two.three
            else:
                return x.two.one

        same(T([T2(False, 3.14), T2(True, -3.14)], T2(True, 99.9)), f, [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (3, 0)])

        same([T(False, False), T2(99.9, 99.2), T(True, True)], lambda x, i: x[i].one, [0, 1, 2])
        same([T(T(False, True), False), T2(1.1, T2(2.2, 3.3)), T(T(True, False), True)], lambda x, i: x[i].one.one, [0, 1, 2])
        same([T(T(False, True), False), T2(1.1, T(2.2, 3.3)), T(T(True, False), True)], lambda x, i: x[i].one.two, [0, 1, 2])

        same([T([False], False), T2(99.9, [99.2]), T([True], True)], lambda x, i: x[i].one[0], [0, 1, 2])
        same([T(T([False], True), False), T2(1.1, T2(2.2, [3.3])), T(T([True], False), True)], lambda x, i: x[i].one.one[0], [0, 1, 2])
        same([T(T(False, [True]), False), T2(1.1, T(2.2, [3.3])), T(T(True, [False]), True)], lambda x, i: x[i].one.two[0], [0, 1, 2])

        same([T([[False]], False), T2(99.9, [[99.2]]), T([[True]], True)], lambda x, i: x[i].one[0][0], [0, 1, 2])
        same([T([[False, True]], False), T2(99.9, [[99.2, 3.14]]), T([[True, False]], True)], lambda x, i: x[i].one[0][1], [0, 1, 2])

        ####### len

        same([1, 2, 3, 4, 5], lambda x, dummy: len(x), [0])
        same([[], [1, 2], [3, 4, 5]], lambda x, i: len(x[i]), [0, 1, 2])

        same([[], [T(1, 1), T(2, 2)], [T(3, 3), T(4, 4), T(5, 5)]], lambda x, i: len(x[i]), [0, 1, 2])
        same([T([], []), T([1, 2], [1, 2]), T([3, 4, 5], [3, 4, 5])], lambda x, i: len(x[i].one), [0, 1, 2])
        same([T([1], [1]), T2([1, 2], [1, 2]), T([3, 4, 5], [3, 4, 5])], lambda x, i: len(x[i].one), [0, 1, 2])

    def test_local(self):
        data = [[], [1, 2], [3, 4, 5]]
        arrays = toarrays("prefix", data)
        tpe = arrays2type(arrays, "prefix")
        fcn, arrayparams = local(lambda x, i, j: x[i][j], {"x": tpe})
        self.assertEqual(arrayparams, ["prefix-Lo", "prefix-Ld-Lo", "prefix-Ld-Ld"])

        arrayargs = [arrays[x] for x in arrayparams]
        self.assertEqual(fcn(arrayargs, 1, 0), 1)
        self.assertEqual(fcn(arrayargs, 1, 1), 2)
        self.assertEqual(fcn(arrayargs, 2, 0), 3)
        self.assertEqual(fcn(arrayargs, 2, 1), 4)
        self.assertEqual(fcn(arrayargs, 2, 2), 5)

    def test_numba(self):
        try:
            import numba
        except ImportError:
            sys.stderr.write("skipping (Numba is not installed)\n")
            return

        data = [[], [1, 2], [3, 4, 5]]
        arrays = toarrays("prefix", data)
        tpe = arrays2type(arrays, "prefix")
        fcn, arrayparams = local(lambda x, i, j: x[i][j], {"x": tpe}, numba={})
        self.assertEqual(arrayparams, ["prefix-Lo", "prefix-Ld-Lo", "prefix-Ld-Ld"])

        arrayargs = [arrays[x] for x in arrayparams]
        self.assertEqual(fcn(arrayargs, 1, 0), 1)
        self.assertEqual(fcn(arrayargs, 1, 1), 2)
        self.assertEqual(fcn(arrayargs, 2, 0), 3)
        self.assertEqual(fcn(arrayargs, 2, 1), 4)
        self.assertEqual(fcn(arrayargs, 2, 2), 5)
