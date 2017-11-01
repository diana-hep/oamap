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
from collections import namedtuple

import numpy

from oamap.frompython import toarrays

class TestCompile(unittest.TestCase):
    def runTest(self):
        pass

    def compare(self, data, function, numba=None, debug=False):
        arrays = toarrays(data)
        if debug:
            print arrays.format()

        python_result = function(data)
        proxy_result = function(arrays.proxy())
        compiled_result = arrays.run(function, numba=numba, debug=debug)

        if debug:
            print("")
            print("python:   {0}".format(python_result))
            print("proxy:    {0}".format(proxy_result))
            print("compiled: {0}".format(compiled_result))

        self.assertEqual(python_result, proxy_result)
        self.assertEqual(python_result, compiled_result)

    def failure(self, data, function, exception, numba=None, onlycompiled=False):
        arrays = toarrays(data)

        if not onlycompiled:
            self.assertRaises(exception, lambda: function(data))
            self.assertRaises(exception, lambda: function(arrays.proxy()))
        self.assertRaises(exception, lambda: arrays.run(function, numba=numba))

    def test_simple(self):
        self.compare([3.14, 2.71, 99.9], lambda x: x)

        def good(x):
            return x
        self.compare([3.14, 2.71, 99.9], good)

        def good2(x):
            return None
        self.compare([3.14, 2.71, 99.9], good2)

    def test_subscript(self):
        self.compare([3.14, 2.71, 99.9], lambda x: x[0])
        self.compare([3.14, 2.71, 99.9], lambda x: x[1])
        self.compare([3.14, 2.71, 99.9], lambda x: x[2])
        self.compare([3.14, 2.71, 99.9], lambda x: x[-1])
        self.compare([3.14, 2.71, 99.9], lambda x: x[-2])
        self.compare([3.14, 2.71, 99.9], lambda x: x[-3])
        self.failure([3.14, 2.71, 99.9], lambda x: x[3], IndexError)
        self.failure([3.14, 2.71, 99.9], lambda x: x[-4], IndexError)
        self.failure(5, lambda x: x[-3], TypeError, onlycompiled=True)

    def test_attribute(self):
        T = namedtuple("T", ["one", "two"])
        self.compare(T(1, 2.2), lambda x: x.one)
        self.compare(T(1, 2.2), lambda x: x.two)
        self.failure(T(1, 2.2), lambda x: x.three, AttributeError)
        self.compare(T(1, 2.2), lambda x: x)

    def test_subscript_attribute(self):
        T = namedtuple("T", ["one", "two"])
        self.compare([T(1, 1.1), T(2, 2.2)], lambda x: x[0].one)
        self.compare([T(1, 1.1), T(2, 2.2)], lambda x: x[0].two)
        self.compare([T(1, 1.1), T(2, 2.2)], lambda x: x[1].one)
        self.compare([T(1, 1.1), T(2, 2.2)], lambda x: x[1].two)
        self.failure([T(1, 1.1), T(2, 2.2)], lambda x: x[2].one, IndexError)
        self.failure([T(1, 1.1), T(2, 2.2)], lambda x: x[1].three, AttributeError)
        self.compare([T(1, 1.1), T(2, 2.2)], lambda x: x[0])
        self.compare([T(1, 1.1), T(2, 2.2)], lambda x: x[1])

    def test_attribute_subscript(self):
        T = namedtuple("T", ["one", "two"])
        self.compare(T([1, 2], 3.3), lambda x: x.one[0])
        self.compare(T([1, 2], 3.3), lambda x: x.one[1])
        self.compare(T([1, 2], 3.3), lambda x: x.two)
        self.failure(T([1, 2], 3.3), lambda x: x.three, AttributeError)
        self.failure(T([1, 2], 3.3), lambda x: x.one[2], IndexError)
        self.compare(T([1, 2], 3.3), lambda x: x.one)

    def test_forloop(self):
        def go(data):
            total = 0
            for x in data:
                total += x
            return total
        self.compare([1, 2, 3, 4, 55], go)

    def test_forloop2(self):
        def go(data):
            total = 0
            for sublist in data:
                for x in sublist:
                    total += x
            return total
        self.compare([[1, 2, 3], [], [4, 55]], go)

    def test_assign(self):
        def go(data):
            x = data[1]
            return x
        self.compare([3.14, 2.71, 99.9], go)

        def go(data):
            x = data[1]
            if False:
                x = data[0]
            return x
        self.compare([3.14, 2.71, 99.9], go)

        def go(data):
            x = None
            if False:
                x = data[0]
            return x
        self.compare([3.14, 2.71, 99.9], go)

        def go(data):
            x = None
            if False:
                x = data[0]
            return x[2]
        self.failure([[1, 2, 3], [], [4, 55]], go, TypeError)

        def go(data):
            x = None
            if True:
                x = data[0]
            return x[2]
        self.compare([[1, 2, 3], [], [4, 55]], go)

    def test_listlen(self):
        self.compare([[1, 2, 3], [], [4, 55]], lambda x: len(x))
        self.compare([[1, 2, 3], [], [4, 55]], lambda x: len(x[0]))
        self.compare([[1, 2, 3], [], [4, 55]], lambda x: len(x[1]))
        self.compare([[1, 2, 3], [], [4, 55]], lambda x: len(x[2]))
