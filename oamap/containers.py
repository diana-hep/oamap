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

import numpy



################################################################ AppendableArray

class AppendableArray(object):
    # Numpy arrays and list items have 96+8 byte (80+8 byte) overhead in Python 2 (Python 3)
    # compared to 8192 1-byte values (8-byte values), this is 1% overhead (0.1% overhead)
    def __init__(self, dtype, dims, nullable, chunksize=8192):
        self.dtype = dtype
        self.dims = dims
        self.nullable = nullable
        self.chunksize = chunksize
        self._data = [numpy.empty((self.chunksize,) + self.dims, dtype=self.dtype)]
        if self.nullable:
            self._mask = [numpy.empty(self.chunksize, dtype=numpy.bool_)]
        self._indexinchunk = 0
        self._chunkindex = 0

    def append(self, value):
        if self._indexinchunk >= len(self._data[self._chunkindex]):
            self._data.append(numpy.empty((self.chunksize,) + self.dims, dtype=self.dtype))
            if self.nullable:
                self._mask.append(numpy.empty(self.chunksize, dtype=numpy.bool_))
            self._indexinchunk = 0
            self._chunkindex += 1
                
        if self.nullable:
            if value is None:
                self._mask[self._chunkindex][self._indexinchunk] = True
            else:
                self._data[self._chunkindex][self._indexinchunk] = value
                self._mask[self._chunkindex][self._indexinchunk] = False
        else:
            self._data[self._chunkindex][self._indexinchunk] = value

        self._indexinchunk += 1

    def __getitem__(self, index):
        if isinstance(index, slice):
            pass

        else:
            HERE


