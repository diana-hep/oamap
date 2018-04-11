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

import codecs
import importlib
import numbers
import os
import sys
import collections

import numpy

import oamap.schema
import oamap.generator
import oamap.proxy
import oamap.operations

if sys.version_info[0] > 2:
    basestring = str
    unicode = str

################################################################ Namespace

################################################################ Dataset

################################################################ Database

################################################################ quick test

# import oamap.backend.numpyfile

# ns1 = Namespace(oamap.backend.numpyfile.NumpyFile, ("/home/pivarski/diana/oamap",), [("part1",), ("part2",)])
# ns2 = Namespace(oamap.backend.numpyfile.NumpyFile, ("/home/pivarski/diana/oamap",), [("part2",), ("part1",)])

# sch = oamap.schema.List(oamap.schema.List(oamap.schema.Primitive(float, data="data.npy", namespace="DATA"), starts="starts.npy", stops="stops.npy"))

# test = Dataset(None, sch, {"": ns1, "DATA": ns2}, [0, 3, 6])

# db = InMemoryDatabase({"test": test}, backend=oamap.backend.numpyfile.WritableNumpyFile, args=("/home/pivarski/diana/oamap",))
# q = db.datasets.test.filter(lambda x: len(x) > 0)

# db.datasets.q = q
