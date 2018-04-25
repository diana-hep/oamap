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
import tempfile
import shutil

import unittest

import oamap.backend.root
import oamap.database

class TestBackendRoot(unittest.TestCase):
    def runTest(self):
        pass

    def test_database(self):
        dataset = oamap.backend.root.dataset("tests/samples/mc10events.root", "Events")

        self.assertEqual(repr(dataset[0].Electron[0].pt), "28.555809")

        db = oamap.database.InMemoryDatabase()

        db.data.one = dataset

        self.assertEqual(repr(db.data.one[0].Electron[0].pt), "28.555809")

    # def test_transform(self):
    #     dataset = oamap.backend.root.dataset("tests/samples/mc10events.root", "Events")

    #     print dataset[0].Electron[0].pt * math.sinh(dataset[0].Electron[0].eta)

    #     db = oamap.database.InMemoryDatabase.writable(oamap.database.DictBackend())
    #     db.data.one = dataset.define("pz", lambda x: x.pt * math.sinh(x.eta), at="Electron")

    #     print db.data.one[0].Electron[0].pz

