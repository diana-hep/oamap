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

"""Substitutions for parts of fastparquet that we need to do differently.

This file (only one in the _fastparquet directory) is under OAMap's license.
"""

import os

import numpy

from oamap.util import OrderedDict

try:
    import thriftpy
    import thriftpy.protocol
except ImportError:
    thriftpy = None
    parquet_thrift = None
else:
    THRIFT_FILE = os.path.join(os.path.dirname(__file__), "parquet.thrift")
    parquet_thrift = thriftpy.load(THRIFT_FILE, module_name="parquet_thrift")

def unpack_byte_array(array, count):
    data = numpy.empty(len(array) - 4*count, numpy.uint8)
    size = numpy.empty(count, numpy.int32)

    i = 0
    datai = 0
    sizei = 0
    while sizei < count:
        if i + 4 > len(array):
            raise RuntimeError("ran out of input")
        itemlen = array[i] + (array[i + 1] << 8) + (array[i + 2] << 16) + (array[i + 3] << 24)
        i += 4

        if i + itemlen > len(array):
            raise RuntimeError("ran out of input")
        data[datai : datai + itemlen] = array[i : i + itemlen]
        size[sizei] = itemlen

        i += itemlen
        datai += itemlen
        sizei += 1

    return data, size

try:
    import numba
except ImportError:
    pass
else:
    njit = numba.jit(nopython=True, nogil=True)
    unpack_byte_array = njit(unpack_byte_array)
