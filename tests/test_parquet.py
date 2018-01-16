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
        f = ParquetFile(open("tests/samples/record-primitives.parquet", "rb"))
        self.assertEqual(
            tojson(f[:]),
            [{"u1": False, "u4": 1, "u8": 1, "f4": 1.100000023841858, "f8": 1.1, "raw": b"one", "utf8": "one"},
             {"u1": True,  "u4": 2, "u8": 2, "f4": 2.200000047683716, "f8": 2.2, "raw": b"two", "utf8": "two"},
             {"u1": True,  "u4": 3, "u8": 3, "f4": 3.299999952316284, "f8": 3.3, "raw": b"three", "utf8": "three"},
             {"u1": False, "u4": 4, "u8": 4, "f4": 4.400000095367432, "f8": 4.4, "raw": b"four", "utf8": "four"},
             {"u1": False, "u4": 5, "u8": 5, "f4": 5.5,               "f8": 5.5, "raw": b"five", "utf8": "five"}])

    def test_nullable_record_primitives_simple(self):
        f = ParquetFile(open("tests/samples/nullable-record-primitives-simple.parquet", "rb"))
        self.assertEqual(
            tojson(f[:]),
            [{"u4": None, "u8": 1},
             {"u4": None, "u8": 2},
             {"u4": None, "u8": 3},
             {"u4": None, "u8": 4},
             {"u4": None, "u8": 5}])

    def test_nullable_record_primitives(self):
        f = ParquetFile(open("tests/samples/nullable-record-primitives.parquet", "rb"))
        self.assertEqual(
            tojson(f[:]),
            [{"u1": None,  "u4": 1,    "u8": None, "f4": 1.100000023841858, "f8": None, "raw": b"one",   "utf8": "one"},
             {"u1": True,  "u4": None, "u8": 2,    "f4": 2.200000047683716, "f8": None, "raw": None,     "utf8": None},
             {"u1": None,  "u4": None, "u8": 3,    "f4": None,              "f8": None, "raw": b"three", "utf8": None},
             {"u1": False, "u4": None, "u8": 4,    "f4": None,              "f8": 4.4,  "raw": None,     "utf8": None},
             {"u1": None,  "u4": 5,    "u8": None, "f4": None,              "f8": 5.5,  "raw": None,     "utf8": "five"}])

    def test_nullable_levels(self):
        "tests/samples/nullable-levels.parquet"

    def test_list_lengths(self):
        "tests/samples/list-lengths.parquet"

    def test_list_depths_simple(self):
        "tests/samples/list-depths-simple.parquet"

    def test_list_depths(self):
        "tests/samples/list-depths.parquet"

    def test_nullable_list_depths(self):
        "tests/samples/nullable-list-depths.parquet"

    def test_list_depths_strings(self):
        "tests/samples/list-depths-strings.parquet"

    def test_nullable_list_depths_strings(self):
        "tests/samples/nullable-list-depths-strings.parquet"

    def test_nonnullable_depths(self):
        "tests/samples/nonnullable-depths.parquet"

    def test_nullable_depths(self):
        "tests/samples/nullable-depths.parquet"

    def test_list_depths_records(self):
        "tests/samples/list-depths-records.parquet"

    def test_nullable_list_depths_records(self):
        "tests/samples/nullable-list-depths-records.parquet"

    def test_list_depths_records_list(self):
        "tests/samples/list-depths-records-list.parquet"

    def test_nullable_list_depths_records_list(self):
        "tests/samples/nullable-list-depths-records-list.parquet"

