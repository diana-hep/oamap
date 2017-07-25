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
from plur.compile.code import fcn2syntaxtree, rewrite, compilefcn, callfcn

from plur.thirdparty.meta import dump_python_source

class TestCompile(unittest.TestCase):
    def runTest(self):
        pass

    def test_rewrite(self):
        def same(data, fcn, testsets, debug=False):
            arrays = toarrays("prefix", data)
            tpe = columns2type(dict((n, a.dtype) for n, a in arrays.items()), "prefix")
            if debug:
                print("\nTYPE: {0}".format(tpe))

            code, arrayparams, enclosedfcns, encloseddata = rewrite(fcn, (tpe,))
            if debug:
                print("\nBEFORE:\n{0}\nAFTER:\n{1}".format(
                    dump_python_source(fcn2syntaxtree(fcn)), dump_python_source(code)))

            newfcn = compilefcn(code)

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

        same(3, (lambda x, y: x + y), [1.1, 2.2, 3.3])
        same([3, 2, 1], (lambda x, i, y: x[i] + y), [(i, y) for i in range(3) for y in [1.1, 2.2, 3.3]])
        same([[], [1, 2], [3, 4, 5]], (lambda x, i, j, y: x[i][j] + y), [(i, j, y) for i, j in [(1, 0), (1, 1), (2, 0), (2, 1), (2, 2)] for y in [1.1, 2.2, 3.3]])

        def check_only_union(data):
            arrays = toarrays("prefix", data, Union(boolean, float64))
            tpe = columns2type(dict((n, a.dtype) for n, a in arrays.items()), "prefix")
            fcn = lambda x: x
            code, arrayparams, enclosedfcns, encloseddata = rewrite(fcn, (tpe,))
            # print("\nBEFORE:\n{0}\nAFTER:\n{1}".format(
            #     dump_python_source(fcn2syntaxtree(fcn)), dump_python_source(code)))
            # for x in arrayparams:
            #     print("{0}\t{1}".format(x, arrays[x]))
            # print("")
            # print(tpe)
            # print("")
            self.assertEqual(callfcn(arrays, compilefcn(code), arrayparams), data)

        check_only_union(False)
        check_only_union(3.14)
        check_only_union(True)
        check_only_union(99.9)

        same([False, 3.14, True, 99.9], lambda x, i: x[i], [0, 1, 2, 3])
        same([[False, True], [1.1, 2.2]], lambda x, i, j: x[i][j], [(0, 0), (0, 1), (1, 0), (1, 1)])
