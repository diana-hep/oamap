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

import oamap.proxy
from oamap.schema import *

class TestProxy(unittest.TestCase):
    def runTest(self):
        pass

    def test_ListProxy_slicing(self):
        range100 = list(range(100))
        proxy100 = List(Primitive("i8"))({"object-B": [0], "object-E": [100], "object-L-Di8": range100})
        self.assertEqual(range100, proxy100)
        for start1 in [None, 0, 5, 95, 110, -1, -5, -95, -110]:
            for stop1 in [None, 0, 5, 95, 110, -1, -5, -95, -110]:
                for step1 in [None, 1, 2, 5, 90, 110, -1, -2, -5, -90, -110]:
                    sliced_range100 = range100[start1:stop1:step1]
                    sliced_proxy100 = proxy100[start1:stop1:step1]
                    self.assertEqual(sliced_range100, sliced_proxy100)
                    if len(sliced_range100) > 0:
                        for start2 in [None, 0, 5, -1, -5]:
                            for stop2 in [None, 0, 5, -1, -5]:
                                for step2 in [None, 1, 3, -1, -3]:
                                    self.assertEqual(sliced_range100[start2:stop2:step2], sliced_proxy100[start2:stop2:step2])

    def test_PartitionedListProxy_slicing(self):
        range100 = list(range(100))
        proxy100 = oamap.proxy.PartitionedListProxy([list(range(0, 10)), list(range(10, 20)), list(range(20, 25)), list(range(25, 50)), list(range(50, 100))])

        self.assertEqual(range100, proxy100)
        for start1 in [None, 0, 5, 95, 110, -1, -5, -95, -110]:
            for stop1 in [None, 0, 5, 95, 110, -1, -5, -95, -110]:
                for step1 in [None, 1, 2, 5, 90, 110, -1, -2, -5, -90, -110]:
                    sliced_range100 = range100[start1:stop1:step1]
                    sliced_proxy100 = proxy100[start1:stop1:step1]
                    self.assertEqual(sliced_range100, sliced_proxy100)
                    if len(sliced_range100) > 0:
                        for start2 in [None, 0, 5, -1, -5]:
                            for stop2 in [None, 0, 5, -1, -5]:
                                for step2 in [None, 1, 3, -1, -3]:
                                    self.assertEqual(sliced_range100[start2:stop2:step2], sliced_proxy100[start2:stop2:step2])

    def test_Primitive(self):
        self.assertEqual(Primitive("f8")({"object-Df8": [3.14]}), 3.14)
        self.assertEqual(Primitive("f8", dims=(2, 2))({"object-Df8-2-2": [[[1, 2], [3, 4]]]}).tolist(), [[1, 2], [3, 4]])
        self.assertEqual(Primitive("f8", nullable=True)({"object-Df8": [], "object-M": [-1]}), None)
        self.assertEqual(Primitive("f8", nullable=True)({"object-Df8": [3.14], "object-M": [0]}), 3.14)

    def test_List(self):
        self.assertEqual(List(Primitive("f8"))({"object-B": [0], "object-E": [5], "object-L-Df8": [1.1, 2.2, 3.3, 4.4, 5.5]}), [1.1, 2.2, 3.3, 4.4, 5.5])
        self.assertEqual(len(List(Primitive("f8"))({"object-B": [0], "object-E": [5], "object-L-Df8": [1.1, 2.2, 3.3, 4.4, 5.5]})), 5)
        self.assertEqual(List(List(Primitive("f8")))({"object-B": [0], "object-E": [3], "object-L-B": [0, 2, 2], "object-L-E": [2, 2, 5], "object-L-L-Df8": [1.1, 2.2, 3.3, 4.4, 5.5]}), [[1.1, 2.2], [], [3.3, 4.4, 5.5]])
        self.assertEqual(len(List(List(Primitive("f8")))({"object-B": [0], "object-E": [3], "object-L-B": [0, 2, 2], "object-L-E": [2, 2, 5], "object-L-L-Df8": [1.1, 2.2, 3.3, 4.4, 5.5]})), 3)
        self.assertEqual(list(map(len, List(List(Primitive("f8")))({"object-B": [0], "object-E": [3], "object-L-B": [0, 2, 2], "object-L-E": [2, 2, 5], "object-L-L-Df8": [1.1, 2.2, 3.3, 4.4, 5.5]}))), [2, 0, 3])
        self.assertEqual(List(List(Primitive("f8")), nullable=True)({"object-B": [], "object-E": [], "object-L-B": [], "object-L-E": [], "object-L-L-Df8": [], "object-M": [-1]}), None)
        self.assertEqual(List(List(Primitive("f8")), nullable=True)({"object-B": [0], "object-E": [3], "object-L-B": [0, 2, 2], "object-L-E": [2, 2, 5], "object-L-L-Df8": [1.1, 2.2, 3.3, 4.4, 5.5], "object-M": [0]}), [[1.1, 2.2], [], [3.3, 4.4, 5.5]])
        self.assertEqual(List(List(Primitive("f8"), nullable=True))({"object-B": [0], "object-E": [3], "object-L-B": [0, 2], "object-L-E": [2, 2], "object-L-L-Df8": [1.1, 2.2], "object-L-M": [0, 1, -1]}), [[1.1, 2.2], [], None])
        self.assertEqual(List(List(Primitive("f8"), nullable=True), nullable=True)({"object-B": [0], "object-E": [3], "object-L-B": [0, 2], "object-L-E": [2, 2], "object-L-L-Df8": [1.1, 2.2], "object-M": [0], "object-L-M": [0, 1, -1]}), [[1.1, 2.2], [], None])

    def test_List_slices(self):
        x = List(List(Primitive("f8")))({"object-B": [0], "object-E": [3], "object-L-B": [0, 2, 2], "object-L-E": [2, 2, 5], "object-L-L-Df8": [1.1, 2.2, 3.3, 4.4, 5.5]})

        self.assertEqual(x[0], [1.1, 2.2])
        self.assertEqual(x[1], [])
        self.assertEqual(x[2], [3.3, 4.4, 5.5])
        self.assertEqual(x[-1], [3.3, 4.4, 5.5])
        self.assertEqual(x[-2], [])
        self.assertEqual(x[-3], [1.1, 2.2])
        self.assertRaises(IndexError, lambda: x[3])
        self.assertRaises(IndexError, lambda: x[-4])

        self.assertEqual(x[0:1], [[1.1, 2.2]])
        self.assertEqual(x[0:2], [[1.1, 2.2], []])
        self.assertEqual(x[0:3], [[1.1, 2.2], [], [3.3, 4.4, 5.5]])
        self.assertEqual(x[:], [[1.1, 2.2], [], [3.3, 4.4, 5.5]])
        self.assertEqual(x[:10], [[1.1, 2.2], [], [3.3, 4.4, 5.5]])
        self.assertEqual(x[1:3], [[], [3.3, 4.4, 5.5]])
        self.assertEqual(x[2:3], [[3.3, 4.4, 5.5]])
        self.assertEqual(x[3:3], [])
        self.assertEqual(x[-3:1], [[1.1, 2.2]])
        self.assertEqual(x[-3:2], [[1.1, 2.2], []])
        self.assertEqual(x[-3:3], [[1.1, 2.2], [], [3.3, 4.4, 5.5]])
        self.assertEqual(x[-2:3], [[], [3.3, 4.4, 5.5]])
        self.assertEqual(x[-1:3], [[3.3, 4.4, 5.5]])
        self.assertEqual(x[-1:-1], [])
        self.assertEqual(x[-10:3], [[1.1, 2.2], [], [3.3, 4.4, 5.5]])
        self.assertEqual(x[::2], [[1.1, 2.2], [3.3, 4.4, 5.5]])
        self.assertEqual(x[1::2], [[]])

        x = List(List(Primitive("f8"), nullable=True))({"object-B": [0], "object-E": [3], "object-L-B": [0, 2], "object-L-E": [2, 5], "object-L-M": [0, -1, 1], "object-L-L-Df8": [1.1, 2.2, 3.3, 4.4, 5.5]})

        self.assertEqual(x[1], None)
        self.assertEqual(x[-2], None)
        self.assertEqual(x[0:2], [[1.1, 2.2], None])
        self.assertEqual(x[0:3], [[1.1, 2.2], None, [3.3, 4.4, 5.5]])
        self.assertEqual(x[:], [[1.1, 2.2], None, [3.3, 4.4, 5.5]])
        self.assertEqual(x[:10], [[1.1, 2.2], None, [3.3, 4.4, 5.5]])
        self.assertEqual(x[1:3], [None, [3.3, 4.4, 5.5]])
        self.assertEqual(x[3:3], [])
        self.assertEqual(x[-3:2], [[1.1, 2.2], None])
        self.assertEqual(x[-3:3], [[1.1, 2.2], None, [3.3, 4.4, 5.5]])
        self.assertEqual(x[-2:3], [None, [3.3, 4.4, 5.5]])
        self.assertEqual(x[-1:-1], [])
        self.assertEqual(x[-10:3], [[1.1, 2.2], None, [3.3, 4.4, 5.5]])
        self.assertEqual(x[1::2], [None])

    def test_Union(self):
        self.assertEqual(Union([Primitive("i8"), Primitive("f8")])({"object-T": [0], "object-O": [0], "object-U0-Di8": [1], "object-U1-Df8": []}), 1)
        self.assertEqual(List(Union([Primitive("i8"), Primitive("f8")]))({"object-B": [0], "object-E": [7], "object-L-T": [0, 0, 1, 1, 1, 0, 0], "object-L-O": [0, 1, 0, 1, 2, 2, 3], "object-L-U0-Di8": [1, 2, 3, 4], "object-L-U1-Df8": [1.1, 2.2, 3.3]}), [1, 2, 1.1, 2.2, 3.3, 3, 4])

        self.assertEqual(list(List(Union([Primitive("i8"), Primitive("f8")], nullable=True))({"object-L-U1-Df8": [1.1, 3.3], "object-L-T": [0, 1, 1, 0], "object-E": [7], "object-L-O": [0, 0, 1, 1], "object-L-M": [0, -1, 1, -1, 2, 3, -1], "object-L-U0-Di8": [1, 3], "object-B": [0]})), [1, None, 1.1, None, 3.3, 3, None])
        self.assertEqual(List(Union([Primitive("i8", nullable=True), Primitive("f8")]))({"object-L-U0-M": [0, -1, 1, -1], "object-L-T": [0, 0, 1, 1, 1, 0, 0], "object-E": [7], "object-L-O": [0, 1, 0, 1, 2, 2, 3], "object-L-U1-Df8": [1.1, 2.2, 3.3], "object-L-U0-Di8": [1, 3], "object-B": [0]}), [1, None, 1.1, 2.2, 3.3, 3, None])

        self.assertEqual(List(Union([Primitive("i8"), List(Primitive("f8"))]))({"object-B": [0], "object-E": [2], "object-L-T": [0, 1], "object-L-O": [0, 0], "object-L-U0-Di8": [3], "object-L-U1-B": [0], "object-L-U1-E": [3], "object-L-U1-L-Df8": [1.1, 2.2, 3.3]}), [3, [1.1, 2.2, 3.3]])

    def test_Record(self):
        x = Record({"x": Primitive("i8"), "y": Primitive("f8")})({"object-Fx-Di8": [3], "object-Fy-Df8": [3.14]})
        self.assertEqual(x.x, 3)
        self.assertEqual(x.y, 3.14)

        x = List(Record({"x": Primitive("i8"), "y": Primitive("f8")}))({"object-B": [0], "object-E": [3], "object-L-Fx-Di8": [1, 2, 3], "object-L-Fy-Df8": [1.1, 2.2, 3.3]})
        self.assertEqual(x[0].x, 1)
        self.assertEqual(x[1].x, 2)
        self.assertEqual(x[2].x, 3)
        self.assertEqual(x[0].y, 1.1)
        self.assertEqual(x[1].y, 2.2)
        self.assertEqual(x[2].y, 3.3)

        x = List(Record({"x": Primitive("i8"), "y": Primitive("f8", nullable=True)}))({"object-B": [0], "object-E": [3], "object-L-Fx-Di8": [1, 2, 3], "object-L-Fy-Df8": [2.2], "object-L-Fy-M": [-1, 0, -1]})
        self.assertEqual(x[0].x, 1)
        self.assertEqual(x[1].x, 2)
        self.assertEqual(x[2].x, 3)
        self.assertEqual(x[0].y, None)
        self.assertEqual(x[1].y, 2.2)
        self.assertEqual(x[2].y, None)

        x = List(Record({"x": Primitive("i8"), "y": Primitive("f8")}, nullable=True))({"object-B": [0], "object-E": [3], "object-L-M": [0, -1, 1], "object-L-Fx-Di8": [1, 3], "object-L-Fy-Df8": [1.1, 3.3]})
        self.assertEqual(x[0].x, 1)
        self.assertEqual(x[1], None)
        self.assertEqual(x[2].x, 3)
        self.assertEqual(x[0].y, 1.1)
        self.assertEqual(x[1], None)
        self.assertEqual(x[2].y, 3.3)

        x = Record({"x": Primitive("i8"), "y": List(Primitive("f8"))})({"object-Fx-Di8": [3], "object-Fy-B": [0], "object-Fy-E": [3], "object-Fy-L-Df8": [1.1, 2.2, 3.3]})
        self.assertEqual(x.x, 3)
        self.assertEqual(x.y, [1.1, 2.2, 3.3])

        x = Record({"x": Primitive("i8"), "y": Union([Primitive("i8"), Primitive("f8")])})({"object-Fx-Di8": [3], "object-Fy-T": [0], "object-Fy-O": [0], "object-Fy-U0-Di8": [1], "object-Fy-U1-Df8": [1.1]})
        self.assertEqual(x.x, 3)
        self.assertEqual(x.y, 1)

        x = Record({"x": Primitive("i8"), "y": List(Union([Primitive("i8"), Primitive("f8")]))})({"object-Fx-Di8": [3], "object-Fy-B": [0], "object-Fy-E": [3], "object-Fy-L-T": [0, 1, 1], "object-Fy-L-O": [0, 0, 1], "object-Fy-L-U0-Di8": [1], "object-Fy-L-U1-Df8": [1.1, 2.2]})
        self.assertEqual(x.x, 3)
        self.assertEqual(x.y, [1, 1.1, 2.2])

        x = List(Union([Primitive("i8"), Record({"x": Primitive("i8"), "y": Primitive("f8")})]))({"object-B": [0], "object-E": [4], "object-L-T": [0, 1, 1, 0], "object-L-O": [0, 0, 1, 1], "object-L-U0-Di8": [99, 98], "object-L-U1-Fx-Di8": [1, 2], "object-L-U1-Fy-Df8": [1.1, 2.2]})
        self.assertEqual(x[0], 99)
        self.assertEqual(x[1].x, 1)
        self.assertEqual(x[1].y, 1.1)
        self.assertEqual(x[2].x, 2)
        self.assertEqual(x[2].y, 2.2)
        self.assertEqual(x[3], 98)

    def test_Tuple(self):
        x = Tuple((Primitive("i8"), Primitive("f8")))({"object-F0-Di8": [3], "object-F1-Df8": [3.14]})
        self.assertEqual(x[0], 3)
        self.assertEqual(x[1], 3.14)

        x = List(Tuple((Primitive("i8"), Primitive("f8"))))({"object-B": [0], "object-E": [3], "object-L-F0-Di8": [1, 2, 3], "object-L-F1-Df8": [1.1, 2.2, 3.3]})
        self.assertEqual(x[0][0], 1)
        self.assertEqual(x[1][0], 2)
        self.assertEqual(x[2][0], 3)
        self.assertEqual(x[0][1], 1.1)
        self.assertEqual(x[1][1], 2.2)
        self.assertEqual(x[2][1], 3.3)

        x = List(Tuple((Primitive("i8"), Primitive("f8", nullable=True))))({"object-B": [0], "object-E": [3], "object-L-F0-Di8": [1, 2, 3], "object-L-F1-Df8": [2.2], "object-L-F1-M": [-1, 0, -1]})
        self.assertEqual(x[0][0], 1)
        self.assertEqual(x[1][0], 2)
        self.assertEqual(x[2][0], 3)
        self.assertEqual(x[0][1], None)
        self.assertEqual(x[1][1], 2.2)
        self.assertEqual(x[2][1], None)

        x = List(Tuple((Primitive("i8"), Primitive("f8")), nullable=True))({"object-B": [0], "object-E": [3], "object-L-M": [0, -1, 1], "object-L-F0-Di8": [1, 3], "object-L-F1-Df8": [1.1, 3.3]})
        self.assertEqual(x[0][0], 1)
        self.assertEqual(x[1], None)
        self.assertEqual(x[2][0], 3)
        self.assertEqual(x[0][1], 1.1)
        self.assertEqual(x[1], None)
        self.assertEqual(x[2][1], 3.3)

        x = Tuple((Primitive("i8"), List(Primitive("f8"))))({"object-F0-Di8": [3], "object-F1-B": [0], "object-F1-E": [3], "object-F1-L-Df8": [1.1, 2.2, 3.3]})
        self.assertEqual(x[0], 3)
        self.assertEqual(x[1], [1.1, 2.2, 3.3])

        x = Tuple((Primitive("i8"), Union([Primitive("i8"), Primitive("f8")])))({"object-F0-Di8": [3], "object-F1-T": [0], "object-F1-O": [0], "object-F1-U0-Di8": [1], "object-F1-U1-Df8": [1.1]})
        self.assertEqual(x[0], 3)
        self.assertEqual(x[1], 1)

        x = Tuple((Primitive("i8"), List(Union([Primitive("i8"), Primitive("f8")]))))({"object-F0-Di8": [3], "object-F1-B": [0], "object-F1-E": [3], "object-F1-L-T": [0, 1, 1], "object-F1-L-O": [0, 0, 1], "object-F1-L-U0-Di8": [1], "object-F1-L-U1-Df8": [1.1, 2.2]})
        self.assertEqual(x[0], 3)
        self.assertEqual(x[1], [1, 1.1, 2.2])

        x = List(Union([Primitive("i8"), Tuple((Primitive("i8"), Primitive("f8")))]))({"object-B": [0], "object-E": [4], "object-L-T": [0, 1, 1, 0], "object-L-O": [0, 0, 1, 1], "object-L-U0-Di8": [99, 98], "object-L-U1-F0-Di8": [1, 2], "object-L-U1-F1-Df8": [1.1, 2.2]})
        self.assertEqual(x[0], 99)
        self.assertEqual(x[1][0], 1)
        self.assertEqual(x[1][1], 1.1)
        self.assertEqual(x[2][0], 2)
        self.assertEqual(x[2][1], 2.2)
        self.assertEqual(x[3], 98)

    def test_Pointer(self):
        self.assertEqual(Pointer(Primitive("f8"))({"object-P": [3], "object-X-Df8": [0.0, 1.1, 2.2, 3.3, 4.4]}), 3.3)

        tree = Pointer(None)
        tree.target = List(tree)

        self.assertEqual(tree({"object-P": [0], "object-X-B": [0], "object-X-E": [0], "object-X-L-P-object-X-Df8": []}), [])

        self.assertEqual(repr(tree({"object-P": [0], "object-X-B": [0], "object-X-E": [1], "object-X-L-P-object-X": [0]})), "[[...]]")

        self.assertEqual(tree({"object-P": [0, 1], "object-X-B": [0, 1], "object-X-E": [1, 1], "object-X-L-P-object-X": [1]}), [[]])
        self.assertEqual(tree({"object-P": [0, 1], "object-X-B": [0, 2], "object-X-E": [2, 2], "object-X-L-P-object-X": [1, 1]}), [[], []])

        linkedlist = Record({"label": Primitive("i8")})
        linkedlist["next"] = Pointer(linkedlist)

        x = linkedlist({"object-Flabel-Di8": [0, 1, 2], "object-Fnext-P-object": [1, 2, 0]})
        self.assertEqual(x.label, 0)
        self.assertEqual(x.next.label, 1)
        self.assertEqual(x.next.next.label, 2)
        self.assertEqual(x.next.next.next.label, 0)

        linkedlist = Record({"label": Primitive("i8")})
        linkedlist["next"] = Pointer(linkedlist, nullable=True)

        x = linkedlist({"object-Flabel-Di8": [0, 1, 2], "object-Fnext-P-object": [1, 2], "object-Fnext-M": [0, 1, -1]})
        self.assertEqual(x.label, 0)
        self.assertEqual(x.next.label, 1)
        self.assertEqual(x.next.next.label, 2)
        self.assertEqual(x.next.next.next, None)
