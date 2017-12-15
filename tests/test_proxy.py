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

class TestProxy(unittest.TestCase):
    def runTest(self):
        pass

    def test_Primitive(self):
        self.assertEqual(Primitive("f8")()({"object": [3.14]}), 3.14)
        self.assertEqual(Primitive("f8")()({"object": [[[1, 2], [3, 4]]]}), [[1, 2], [3, 4]])
        self.assertEqual(Primitive("f8", nullable=True)()({"object": [3.14], "object-M": [True]}), None)
        self.assertEqual(Primitive("f8", dims=(2, 2), nullable=True)()({"object": [3.14], "object-M": [False]}), 3.14)

    def test_List(self):
        self.assertEqual(List(Primitive("f8"))()({"object-B": [0], "object-E": [5], "object-L": [1.1, 2.2, 3.3, 4.4, 5.5]}), [1.1, 2.2, 3.3, 4.4, 5.5])
        self.assertEqual(len(List(Primitive("f8"))()({"object-B": [0], "object-E": [5], "object-L": [1.1, 2.2, 3.3, 4.4, 5.5]})), 5)
        self.assertEqual(List(List(Primitive("f8")))()({"object-B": [0], "object-E": [3], "object-L-B": [0, 2, 2], "object-L-E": [2, 2, 5], "object-L-L": [1.1, 2.2, 3.3, 4.4, 5.5]}), [[1.1, 2.2], [], [3.3, 4.4, 5.5]])
        self.assertEqual(len(List(List(Primitive("f8")))()({"object-B": [0], "object-E": [3], "object-L-B": [0, 2, 2], "object-L-E": [2, 2, 5], "object-L-L": [1.1, 2.2, 3.3, 4.4, 5.5]})), 3)
        self.assertEqual(list(map(len, List(List(Primitive("f8")))()({"object-B": [0], "object-E": [3], "object-L-B": [0, 2, 2], "object-L-E": [2, 2, 5], "object-L-L": [1.1, 2.2, 3.3, 4.4, 5.5]}))), [2, 0, 3])
        self.assertEqual(List(List(Primitive("f8")), nullable=True)()({"object-B": [0], "object-E": [3], "object-L-B": [0, 2, 2], "object-L-E": [2, 2, 5], "object-L-L": [1.1, 2.2, 3.3, 4.4, 5.5], "object-M": [True]}), None)
        self.assertEqual(List(List(Primitive("f8")), nullable=True)()({"object-B": [0], "object-E": [3], "object-L-B": [0, 2, 2], "object-L-E": [2, 2, 5], "object-L-L": [1.1, 2.2, 3.3, 4.4, 5.5], "object-M": [False]}), [[1.1, 2.2], [], [3.3, 4.4, 5.5]])
        self.assertEqual(List(List(Primitive("f8"), nullable=True))()({"object-B": [0], "object-E": [3], "object-L-B": [0, 2, 2], "object-L-E": [2, 2, 5], "object-L-L": [1.1, 2.2, 3.3, 4.4, 5.5], "object-L-M": [False, False, True]}), [[1.1, 2.2], [], None])
        self.assertEqual(List(List(Primitive("f8"), nullable=True), nullable=True)()({"object-B": [0], "object-E": [3], "object-L-B": [0, 2, 2], "object-L-E": [2, 2, 5], "object-L-L": [1.1, 2.2, 3.3, 4.4, 5.5], "object-M": [False], "object-L-M": [False, False, True]}), [[1.1, 2.2], [], None])

    def test_List_slices(self):
        x = List(List(Primitive("f8")))()({"object-B": [0], "object-E": [3], "object-L-B": [0, 2, 2], "object-L-E": [2, 2, 5], "object-L-L": [1.1, 2.2, 3.3, 4.4, 5.5]})

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

        x = List(List(Primitive("f8"), nullable=True))()({"object-B": [0], "object-E": [3], "object-L-B": [0, 2, 2], "object-L-E": [2, 2, 5], "object-L-M": [False, True, False], "object-L-L": [1.1, 2.2, 3.3, 4.4, 5.5]})

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
        self.assertEqual(Union([Primitive("i8"), Primitive("f8")])()({"object-G": [0], "object-O": [0], "object-U0": [1], "object-U1": []}), 1)
        self.assertEqual(List(Union([Primitive("i8"), Primitive("f8")]))()({"object-B": [0], "object-E": [7], "object-L-G": [0, 0, 1, 1, 1, 0, 0], "object-L-O": [0, 1, 0, 1, 2, 2, 3], "object-L-U0": [1, 2, 3, 4], "object-L-U1": [1.1, 2.2, 3.3]}), [1, 2, 1.1, 2.2, 3.3, 3, 4])
        self.assertEqual(list(List(Union([Primitive("i8"), Primitive("f8")], nullable=True))()({"object-B": [0], "object-E": [7], "object-L-G": [0, 0, 1, 1, 1, 0, 0], "object-L-O": [0, 1, 0, 1, 2, 2, 3], "object-L-M": [False, True, False, True, False, False, True], "object-L-U0": [1, 2, 3, 4], "object-L-U1": [1.1, 2.2, 3.3]})), [1, None, 1.1, None, 3.3, 3, None])
        self.assertEqual(List(Union([Primitive("i8", nullable=True), Primitive("f8")]))()({"object-B": [0], "object-E": [7], "object-L-G": [0, 0, 1, 1, 1, 0, 0], "object-L-O": [0, 1, 0, 1, 2, 2, 3], "object-L-U0": [1, 2, 3, 4], "object-L-U0-M": [False, True, False, True], "object-L-U1": [1.1, 2.2, 3.3]}), [1, None, 1.1, 2.2, 3.3, 3, None])

        self.assertEqual(List(Union([Primitive("i8"), List(Primitive("f8"))]))()({"object-B": [0], "object-E": [2], "object-L-G": [0, 1], "object-L-O": [0, 0], "object-L-U0": [3], "object-L-U1-B": [0], "object-L-U1-E": [3], "object-L-U1-L": [1.1, 2.2, 3.3]}), [3, [1.1, 2.2, 3.3]])

    def test_Record(self):
        x = Record({"x": Primitive("i8"), "y": Primitive("f8")})()({"object-Fx": [3], "object-Fy": [3.14]})
        self.assertEqual(x.x, 3)
        self.assertEqual(x.y, 3.14)

        x = List(Record({"x": Primitive("i8"), "y": Primitive("f8")}))()({"object-B": [0], "object-E": [3], "object-L-Fx": [1, 2, 3], "object-L-Fy": [1.1, 2.2, 3.3]})
        self.assertEqual(x[0].x, 1)
        self.assertEqual(x[1].x, 2)
        self.assertEqual(x[2].x, 3)
        self.assertEqual(x[0].y, 1.1)
        self.assertEqual(x[1].y, 2.2)
        self.assertEqual(x[2].y, 3.3)

        x = List(Record({"x": Primitive("i8"), "y": Primitive("f8", nullable=True)}))()({"object-B": [0], "object-E": [3], "object-L-Fx": [1, 2, 3], "object-L-Fy": [1.1, 2.2, 3.3], "object-L-Fy-M": [True, False, True]})
        self.assertEqual(x[0].x, 1)
        self.assertEqual(x[1].x, 2)
        self.assertEqual(x[2].x, 3)
        self.assertEqual(x[0].y, None)
        self.assertEqual(x[1].y, 2.2)
        self.assertEqual(x[2].y, None)

        x = List(Record({"x": Primitive("i8"), "y": Primitive("f8")}, nullable=True))()({"object-B": [0], "object-E": [3], "object-L-M": [False, True, False], "object-L-Fx": [1, 2, 3], "object-L-Fy": [1.1, 2.2, 3.3]})
        self.assertEqual(x[0].x, 1)
        self.assertEqual(x[1], None)
        self.assertEqual(x[2].x, 3)
        self.assertEqual(x[0].y, 1.1)
        self.assertEqual(x[1], None)
        self.assertEqual(x[2].y, 3.3)

        x = Record({"x": Primitive("i8"), "y": List(Primitive("f8"))})()({"object-Fx": [3], "object-Fy-B": [0], "object-Fy-E": [3], "object-Fy-L": [1.1, 2.2, 3.3]})
        self.assertEqual(x.x, 3)
        self.assertEqual(x.y, [1.1, 2.2, 3.3])

        x = Record({"x": Primitive("i8"), "y": Union([Primitive("i8"), Primitive("f8")])})()({"object-Fx": [3], "object-Fy-G": [0], "object-Fy-O": [0], "object-Fy-U0": [1], "object-Fy-U1": [1.1]})
        self.assertEqual(x.x, 3)
        self.assertEqual(x.y, 1)

        x = Record({"x": Primitive("i8"), "y": List(Union([Primitive("i8"), Primitive("f8")]))})()({"object-Fx": [3], "object-Fy-B": [0], "object-Fy-E": [3], "object-Fy-L-G": [0, 1, 1], "object-Fy-L-O": [0, 0, 1], "object-Fy-L-U0": [1], "object-Fy-L-U1": [1.1, 2.2]})
        self.assertEqual(x.x, 3)
        self.assertEqual(x.y, [1, 1.1, 2.2])

        x = List(Union([Primitive("i8"), Record({"x": Primitive("i8"), "y": Primitive("f8")})]))()({"object-B": [0], "object-E": [4], "object-L-G": [0, 1, 1, 0], "object-L-O": [0, 0, 1, 1], "object-L-U0": [99, 98], "object-L-U1-Fx": [1, 2], "object-L-U1-Fy": [1.1, 2.2]})
        self.assertEqual(x[0], 99)
        self.assertEqual(x[1].x, 1)
        self.assertEqual(x[1].y, 1.1)
        self.assertEqual(x[2].x, 2)
        self.assertEqual(x[2].y, 2.2)
        self.assertEqual(x[3], 98)

    def test_Tuple(self):
        x = Tuple((Primitive("i8"), Primitive("f8")))()({"object-T0": [3], "object-T1": [3.14]})
        self.assertEqual(x[0], 3)
        self.assertEqual(x[1], 3.14)

        x = List(Tuple((Primitive("i8"), Primitive("f8"))))()({"object-B": [0], "object-E": [3], "object-L-T0": [1, 2, 3], "object-L-T1": [1.1, 2.2, 3.3]})
        self.assertEqual(x[0][0], 1)
        self.assertEqual(x[1][0], 2)
        self.assertEqual(x[2][0], 3)
        self.assertEqual(x[0][1], 1.1)
        self.assertEqual(x[1][1], 2.2)
        self.assertEqual(x[2][1], 3.3)

        x = List(Tuple((Primitive("i8"), Primitive("f8", nullable=True))))()({"object-B": [0], "object-E": [3], "object-L-T0": [1, 2, 3], "object-L-T1": [1.1, 2.2, 3.3], "object-L-T1-M": [True, False, True]})
        self.assertEqual(x[0][0], 1)
        self.assertEqual(x[1][0], 2)
        self.assertEqual(x[2][0], 3)
        self.assertEqual(x[0][1], None)
        self.assertEqual(x[1][1], 2.2)
        self.assertEqual(x[2][1], None)

        x = List(Tuple((Primitive("i8"), Primitive("f8")), nullable=True))()({"object-B": [0], "object-E": [3], "object-L-M": [False, True, False], "object-L-T0": [1, 2, 3], "object-L-T1": [1.1, 2.2, 3.3]})
        self.assertEqual(x[0][0], 1)
        self.assertEqual(x[1], None)
        self.assertEqual(x[2][0], 3)
        self.assertEqual(x[0][1], 1.1)
        self.assertEqual(x[1], None)
        self.assertEqual(x[2][1], 3.3)

        x = Tuple((Primitive("i8"), List(Primitive("f8"))))()({"object-T0": [3], "object-T1-B": [0], "object-T1-E": [3], "object-T1-L": [1.1, 2.2, 3.3]})
        self.assertEqual(x[0], 3)
        self.assertEqual(x[1], [1.1, 2.2, 3.3])

        x = Tuple((Primitive("i8"), Union([Primitive("i8"), Primitive("f8")])))()({"object-T0": [3], "object-T1-G": [0], "object-T1-O": [0], "object-T1-U0": [1], "object-T1-U1": [1.1]})
        self.assertEqual(x[0], 3)
        self.assertEqual(x[1], 1)

        x = Tuple((Primitive("i8"), List(Union([Primitive("i8"), Primitive("f8")]))))()({"object-T0": [3], "object-T1-B": [0], "object-T1-E": [3], "object-T1-L-G": [0, 1, 1], "object-T1-L-O": [0, 0, 1], "object-T1-L-U0": [1], "object-T1-L-U1": [1.1, 2.2]})
        self.assertEqual(x[0], 3)
        self.assertEqual(x[1], [1, 1.1, 2.2])

        x = List(Union([Primitive("i8"), Tuple((Primitive("i8"), Primitive("f8")))]))()({"object-B": [0], "object-E": [4], "object-L-G": [0, 1, 1, 0], "object-L-O": [0, 0, 1, 1], "object-L-U0": [99, 98], "object-L-U1-T0": [1, 2], "object-L-U1-T1": [1.1, 2.2]})
        self.assertEqual(x[0], 99)
        self.assertEqual(x[1][0], 1)
        self.assertEqual(x[1][1], 1.1)
        self.assertEqual(x[2][0], 2)
        self.assertEqual(x[2][1], 2.2)
        self.assertEqual(x[3], 98)

    def test_Pointer(self):
        self.assertEqual(Pointer(Primitive("f8"))()({"object-P": [3], "object-X": [0.0, 1.1, 2.2, 3.3, 4.4]}), 3.3)

        tree = Pointer(None)
        tree.target = List(tree)
        self.assertEqual(tree()({"object-P": [0], "object-X-B": [0], "object-X-E": [0], "object-X-L-P": []}), [])

        print tree()({"object-P": [0], "object-X-B": [0], "object-X-E": [1], "object-X-L-P": [0]})

        self.assertEqual(tree()({"object-P": [0, 1], "object-X-B": [0, 1], "object-X-E": [1, 1], "object-X-L-P": [1]}), [[]])
        self.assertEqual(tree()({"object-P": [0, 1], "object-X-B": [0, 2], "object-X-E": [2, 2], "object-X-L-P": [1, 1]}), [[], []])

        linkedlist = Record({"label": Primitive("i8")})
        linkedlist["next"] = Pointer(linkedlist)
        x = linkedlist()({"object-Flabel": [0, 1, 2], "object-Fnext-P": [1, 2, 0]})
        self.assertEqual(x.label, 0)
        self.assertEqual(x.next.label, 1)
        self.assertEqual(x.next.next.label, 2)
        self.assertEqual(x.next.next.next.label, 0)

        linkedlist = Record({"label": Primitive("i8")})
        linkedlist["next"] = Pointer(linkedlist, nullable=True)
        x = linkedlist()({"object-Flabel": [0, 1, 2], "object-Fnext-P": [1, 2, 0], "object-Fnext-M": [False, False, True]})
        self.assertEqual(x.label, 0)
        self.assertEqual(x.next.label, 1)
        self.assertEqual(x.next.next.label, 2)
        self.assertEqual(x.next.next.next, None)
