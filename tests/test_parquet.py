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

from oamap.proxy import tojson
from oamap.source.parquet import ParquetFile

class TestParquet(unittest.TestCase):
    def runTest(self):
        pass

    def test_record_primitives(self):
        with ParquetFile(open("tests/samples/record-primitives.parquet", "rb")) as f:
            self.assertEqual(
                tojson(f()),
                [{"u1": False, "u4": 1, "u8": 1, "f4": 1.100000023841858, "f8": 1.1, "raw": b"one", "utf8": "one"},
                 {"u1": True,  "u4": 2, "u8": 2, "f4": 2.200000047683716, "f8": 2.2, "raw": b"two", "utf8": "two"},
                 {"u1": True,  "u4": 3, "u8": 3, "f4": 3.299999952316284, "f8": 3.3, "raw": b"three", "utf8": "three"},
                 {"u1": False, "u4": 4, "u8": 4, "f4": 4.400000095367432, "f8": 4.4, "raw": b"four", "utf8": "four"},
                 {"u1": False, "u4": 5, "u8": 5, "f4": 5.5,               "f8": 5.5, "raw": b"five", "utf8": "five"}])

    def test_nullable_record_primitives_simple(self):
        with ParquetFile(open("tests/samples/nullable-record-primitives-simple.parquet", "rb")) as f:
            self.assertEqual(
                tojson(f()),
                [{"u4": None, "u8": 1},
                 {"u4": None, "u8": 2},
                 {"u4": None, "u8": 3},
                 {"u4": None, "u8": 4},
                 {"u4": None, "u8": 5}])

    def test_nullable_record_primitives(self):
        with ParquetFile(open("tests/samples/nullable-record-primitives.parquet", "rb")) as f:
            self.assertEqual(
                tojson(f()),
                [{"u1": None,  "u4": 1,    "u8": None, "f4": 1.100000023841858, "f8": None, "raw": b"one",   "utf8": "one"},
                 {"u1": True,  "u4": None, "u8": 2,    "f4": 2.200000047683716, "f8": None, "raw": None,     "utf8": None},
                 {"u1": None,  "u4": None, "u8": 3,    "f4": None,              "f8": None, "raw": b"three", "utf8": None},
                 {"u1": False, "u4": None, "u8": 4,    "f4": None,              "f8": 4.4,  "raw": None,     "utf8": None},
                 {"u1": None,  "u4": 5,    "u8": None, "f4": None,              "f8": 5.5,  "raw": None,     "utf8": "five"}])

    def test_nullable_levels(self):
        with ParquetFile(open("tests/samples/nullable-levels.parquet", "rb")) as f:
            self.assertEqual(
                tojson(f()),
                [{"whatever": {"r0": {"r1": {"r2": {"r3": 1}}}}},
                 {"whatever": {"r0": {"r1": {"r2": {"r3": None}}}}},
                 {"whatever": {"r0": {"r1": {"r2": None}}}},
                 {"whatever": {"r0": None}},
                 {"whatever": None},
                 {"whatever": {"r0": None}},
                 {"whatever": {"r0": {"r1": {"r2": None}}}},
                 {"whatever": {"r0": {"r1": {"r2": {"r3": None}}}}},
                 {"whatever": {"r0": {"r1": {"r2": {"r3": 1}}}}}])

    def test_list_lengths(self):
        with ParquetFile(open("tests/samples/list-lengths.parquet", "rb")) as f:
            self.assertEqual(
                tojson(f()),
                [{"list3": [[[0, 1, 2], [], [], [3, 4]]]},
                 {"list3": [[[5, 6]], [], [], [[7, 8]]]},
                 {"list3": [[[9, 10, 11], []], []]}])

    def test_list_depths_simple(self):
        with ParquetFile(open("tests/samples/list-depths-simple.parquet", "rb")) as f:
            self.assertEqual(
                tojson(f()),
                [{"list0": 1, "list1": [1]},
                 {"list0": 2, "list1": [1, 2]},
                 {"list0": 3, "list1": [1, 2, 3]},
                 {"list0": 4, "list1": [1, 2, 3, 4]},
                 {"list0": 5, "list1": [1, 2, 3, 4, 5]}])

    def test_list_depths(self):
        with ParquetFile(open("tests/samples/list-depths.parquet", "rb")) as f:
            self.assertEqual(
                tojson(f()),
                [{"list0": 1, "list1": [], "list2": [], "list3": []},
                 {"list0": 2, "list1": [2], "list2": [[]], "list3": [[]]},
                 {"list0": 3, "list1": [2, 3], "list2": [[3]], "list3": [[[]]]},
                 {"list0": 4, "list1": [2, 3, 4], "list2": [[3, 4]], "list3": [[[4]]]},
                 {"list0": 5, "list1": [2, 3, 4, 5], "list2": [[3, 4, 5]], "list3": [[[4, 5]]]}])

    def test_nullable_list_depths(self):
        with ParquetFile(open("tests/samples/nullable-list-depths.parquet", "rb")) as f:
            self.assertEqual(
                tojson(f()),
                [{"list0": 1, "list1": [], "list2": [], "list3": []},
                 {"list0": 2, "list1": [2], "list2": [[]], "list3": [[]]},
                 {"list0": 3, "list1": [2, 3], "list2": [[3]], "list3": [[[]]]},
                 {"list0": 4, "list1": [2, 3, 4], "list2": [[3, 4]], "list3": [[[4]]]},
                 {"list0": 5, "list1": [2, 3, 4, 5], "list2": [[3, 4, 5]], "list3": [[[4, 5]]]}])

    def test_list_depths_strings(self):
        with ParquetFile(open("tests/samples/list-depths-strings.parquet", "rb")) as f:
            self.assertEqual(
                tojson(f()),
                [{"list0": "one", "list1": [], "list2": [], "list3": []},
                 {"list0": "two", "list1": ["two"], "list2": [[]], "list3": [[]]},
                 {"list0": "three", "list1": ["two", "three"], "list2": [["three"]], "list3": [[[]]]},
                 {"list0": "four", "list1": ["two", "three", "four"], "list2": [["three", "four"]], "list3": [[["four"]]]},
                 {"list0": "five", "list1": ["two", "three", "four", "five"], "list2": [["three", "four", "five"]], "list3": [[["four", "five"]]]}])

    def test_nullable_list_depths_strings(self):
        with ParquetFile(open("tests/samples/nullable-list-depths-strings.parquet", "rb")) as f:
            self.assertEqual(
                tojson(f()),
                [{"list0": "one", "list1": [], "list2": [], "list3": []},
                 {"list0": "two", "list1": ["two"], "list2": [[]], "list3": [[]]},
                 {"list0": "three", "list1": ["two", "three"], "list2": [["three"]], "list3": [[[]]]},
                 {"list0": "four", "list1": ["two", "three", "four"], "list2": [["three", "four"]], "list3": [[["four"]]]},
                 {"list0": "five", "list1": ["two", "three", "four", "five"], "list2": [["three", "four", "five"]], "list3": [[["four", "five"]]]}])

    def test_nonnullable_depths(self):
        with ParquetFile(open("tests/samples/nonnullable-depths.parquet", "rb")) as f:
            self.assertEqual(
                tojson(f()),
                [{"whatever": {"r0": [{"r1": [{"r2": [0, 1, 2, 3]}]}]}},
                 {"whatever": {"r0": [{"r1": [{"r2": []}]}]}},
                 {"whatever": {"r0": [{"r1": []}]}},
                 {"whatever": {"r0": []}},
                 {"whatever": {"r0": []}},
                 {"whatever": {"r0": [{"r1": []}]}},
                 {"whatever": {"r0": [{"r1": [{"r2": []}]}]}},
                 {"whatever": {"r0": [{"r1": [{"r2": [0, 1, 2, 3]}]}]}}])

    def test_nullable_depths(self):
        with ParquetFile(open("tests/samples/nullable-depths.parquet", "rb")) as f:
            self.assertEqual(
                tojson(f()),
                [{"whatever": {"r0": [{"r1": [{"r2": [0, 1, 2, 3]}]}]}},
                 {"whatever": {"r0": [{"r1": [{"r2": []}]}]}},
                 {"whatever": {"r0": [{"r1": []}]}},
                 {"whatever": {"r0": []}},
                 {"whatever": None},
                 {"whatever": {"r0": []}},
                 {"whatever": {"r0": [{"r1": []}]}},
                 {"whatever": {"r0": [{"r1": [{"r2": []}]}]}},
                 {"whatever": {"r0": [{"r1": [{"r2": [0, 1, 2, 3]}]}]}}])

    def test_list_depths_records(self):
        with ParquetFile(open("tests/samples/list-depths-records.parquet", "rb")) as f:
            self.assertEqual(
                tojson(f()),
                [{"list0": {"one": 1, "two": 1.100000023841858, "three": "one"}, "list1": [], "list2": [], "list3": []},
                 {"list0": {"one": 2, "two": 2.200000047683716, "three": "two"}, "list1": [{"one": 2, "two": 2.200000047683716, "three": "two"}], "list2": [[]], "list3": [[]]},
                 {"list0": {"one": 3, "two": 3.299999952316284, "three": "three"}, "list1": [{"one": 2, "two": 2.200000047683716, "three": "two"}, {"one": 3, "two": 3.299999952316284, "three": "three"}], "list2": [[{"one": 3, "two": 3.299999952316284, "three": "three"}]], "list3": [[[]]]},
                 {"list0": {"one": 4, "two": 4.400000095367432, "three": "four"}, "list1": [{"one": 2, "two": 2.200000047683716, "three": "two"}, {"one": 3, "two": 3.299999952316284, "three": "three"}, {"one": 4, "two": 4.400000095367432, "three": "four"}], "list2": [[{"one": 3, "two": 3.299999952316284, "three": "three"}, {"one": 4, "two": 4.400000095367432, "three": "four"}]], "list3": [[[{"one": 4, "two": 4.400000095367432, "three": "four"}]]]},
                 {"list0": {"one": 5, "two": 5.5, "three": "five"}, "list1": [{"one": 2, "two": 2.200000047683716, "three": "two"}, {"one": 3, "two": 3.299999952316284, "three": "three"}, {"one": 4, "two": 4.400000095367432, "three": "four"}, {"one": 5, "two": 5.5, "three": "five"}], "list2": [[{"one": 3, "two": 3.299999952316284, "three": "three"}, {"one": 4, "two": 4.400000095367432, "three": "four"}, {"one": 5, "two": 5.5, "three": "five"}]], "list3": [[[{"one": 4, "two": 4.400000095367432, "three": "four"}, {"one": 5, "two": 5.5, "three": "five"}]]]}])

    def test_nullable_list_depths_records(self):
        with ParquetFile(open("tests/samples/nullable-list-depths-records.parquet", "rb")) as f:
            self.assertEqual(
                tojson(f()),
                [{"list0": {"one": 1, "two": 1.100000023841858, "three": "one"}, "list1": [], "list2": [], "list3": []},
                 {"list0": {"one": 2, "two": 2.200000047683716, "three": "two"}, "list1": [{"one": 2, "two": 2.200000047683716, "three": "two"}], "list2": [[]], "list3": [[]]},
                 {"list0": {"one": 3, "two": 3.299999952316284, "three": "three"}, "list1": [{"one": 2, "two": 2.200000047683716, "three": "two"}, {"one": 3, "two": 3.299999952316284, "three": "three"}], "list2": [[{"one": 3, "two": 3.299999952316284, "three": "three"}]], "list3": [[[]]]},
                 {"list0": {"one": 4, "two": 4.400000095367432, "three": "four"}, "list1": [{"one": 2, "two": 2.200000047683716, "three": "two"}, {"one": 3, "two": 3.299999952316284, "three": "three"}, {"one": 4, "two": 4.400000095367432, "three": "four"}], "list2": [[{"one": 3, "two": 3.299999952316284, "three": "three"}, {"one": 4, "two": 4.400000095367432, "three": "four"}]], "list3": [[[{"one": 4, "two": 4.400000095367432, "three": "four"}]]]},
                 {"list0": {"one": 5, "two": 5.5, "three": "five"}, "list1": [{"one": 2, "two": 2.200000047683716, "three": "two"}, {"one": 3, "two": 3.299999952316284, "three": "three"}, {"one": 4, "two": 4.400000095367432, "three": "four"}, {"one": 5, "two": 5.5, "three": "five"}], "list2": [[{"one": 3, "two": 3.299999952316284, "three": "three"}, {"one": 4, "two": 4.400000095367432, "three": "four"}, {"one": 5, "two": 5.5, "three": "five"}]], "list3": [[[{"one": 4, "two": 4.400000095367432, "three": "four"}, {"one": 5, "two": 5.5, "three": "five"}]]]}])

    def test_list_depths_records_list(self):
        with ParquetFile(open("tests/samples/list-depths-records-list.parquet", "rb")) as f:
            self.assertEqual(
                tojson(f()),
                [{"list0": {"one": 1, "two": 1.100000023841858, "three": []}, "list1": [], "list2": [], "list3": []},
                 {"list0": {"one": 2, "two": 2.200000047683716, "three": [2]}, "list1": [{"one": 2, "two": 2.200000047683716, "three": [2]}], "list2": [[]], "list3": [[]]},
                 {"list0": {"one": 3, "two": 3.299999952316284, "three": [3, 3]}, "list1": [{"one": 2, "two": 2.200000047683716, "three": [2]}, {"one": 3, "two": 3.299999952316284, "three": [3, 3]}], "list2": [[{"one": 3, "two": 3.299999952316284, "three": [3, 3]}]], "list3": [[[]]]},
                 {"list0": {"one": 4, "two": 4.400000095367432, "three": [4, 4, 4]}, "list1": [{"one": 2, "two": 2.200000047683716, "three": [2]}, {"one": 3, "two": 3.299999952316284, "three": [3, 3]}, {"one": 4, "two": 4.400000095367432, "three": [4, 4, 4]}], "list2": [[{"one": 3, "two": 3.299999952316284, "three": [3, 3]}, {"one": 4, "two": 4.400000095367432, "three": [4, 4, 4]}]], "list3": [[[{"one": 4, "two": 4.400000095367432, "three": [4, 4, 4]}]]]},
                 {"list0": {"one": 5, "two": 5.5, "three": [5, 5, 5, 5]}, "list1": [{"one": 2, "two": 2.200000047683716, "three": [2]}, {"one": 3, "two": 3.299999952316284, "three": [3, 3]}, {"one": 4, "two": 4.400000095367432, "three": [4, 4, 4]}, {"one": 5, "two": 5.5, "three": [5, 5, 5, 5]}], "list2": [[{"one": 3, "two": 3.299999952316284, "three": [3, 3]}, {"one": 4, "two": 4.400000095367432, "three": [4, 4, 4]}, {"one": 5, "two": 5.5, "three": [5, 5, 5, 5]}]], "list3": [[[{"one": 4, "two": 4.400000095367432, "three": [4, 4, 4]}, {"one": 5, "two": 5.5, "three": [5, 5, 5, 5]}]]]}])

    def test_nullable_list_depths_records_list(self):
        with ParquetFile(open("tests/samples/nullable-list-depths-records-list.parquet", "rb")) as f:
            self.assertEqual(
                tojson(f()),
                [{"list0": {"one": 1, "two": 1.100000023841858, "three": []}, "list1": [], "list2": [], "list3": []},
                 {"list0": {"one": 2, "two": 2.200000047683716, "three": [2]}, "list1": [{"one": 2, "two": 2.200000047683716, "three": [2]}], "list2": [[]], "list3": [[]]},
                 {"list0": {"one": 3, "two": 3.299999952316284, "three": [3]}, "list1": [{"one": 2, "two": 2.200000047683716, "three": [2]}, {"one": 3, "two": 3.299999952316284, "three": [3]}], "list2": [[{"one": 3, "two": 3.299999952316284, "three": [3]}]], "list3": [[[]]]},
                 {"list0": {"one": 4, "two": 4.400000095367432, "three": [4, 4, 4]}, "list1": [{"one": 2, "two": 2.200000047683716, "three": [2]}, {"one": 3, "two": 3.299999952316284, "three": [3]}, {"one": 4, "two": 4.400000095367432, "three": [4, 4, 4]}], "list2": [[{"one": 3, "two": 3.299999952316284, "three": [3]}, {"one": 4, "two": 4.400000095367432, "three": [4, 4, 4]}]], "list3": [[[{"one": 4, "two": 4.400000095367432, "three": [4, 4, 4]}]]]},
                 {"list0": {"one": 5, "two": 5.5, "three": [5, 5, 5, 5]}, "list1": [{"one": 2, "two": 2.200000047683716, "three": [2]}, {"one": 3, "two": 3.299999952316284, "three": [3]}, {"one": 4, "two": 4.400000095367432, "three": [4, 4, 4]}, {"one": 5, "two": 5.5, "three": [5, 5, 5, 5]}], "list2": [[{"one": 3, "two": 3.299999952316284, "three": [3]}, {"one": 4, "two": 4.400000095367432, "three": [4, 4, 4]}, {"one": 5, "two": 5.5, "three": [5, 5, 5, 5]}]], "list3": [[[{"one": 4, "two": 4.400000095367432, "three": [4, 4, 4]}, {"one": 5, "two": 5.5, "three": [5, 5, 5, 5]}]]]}])
