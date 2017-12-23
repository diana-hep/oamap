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


class FillColumn(object): pass

################################################################ FillList

class FillList(FillColumn):
    def __init__(self, dtype, dims, nullable):
        self.dtype = dtype
        self.dims = dims
        self.nullable = nullable

        self._data = []
        if self.nullable:
            self._mask = []
        self._index = 0

    def append(self, value):
        if self.nullable:
            if value is None:
                if self._index < len(self._data): self._data[self._index] = 0
                else: self._data.append(0)

                if self._index < len(self._mask): self._mask[self._index] = True
                else: self._mask.append(True)

            else:
                if self._index < len(self._data): self._data[self._index] = value
                else: self._data.append(value)

                if self._index < len(self._mask): self._mask[self._index] = False
                else: self._mask.append(False)

        else:
            if self._index < len(self._data): self._data[self._index] = value
            else: self._data.append(value)

        # no exceptions? acknowledge the new data point
        self._index += 1

    def __len__(self):
        return self._index

    def __getitem__(self, index):
        if isinstance(index, slice):
            lenself = len(self)
            start = 0       if index.start is None else index.start
            stop  = lenself if index.stop  is None else index.stop
            step  = 1       if index.step  is None else index.step
            if start < 0:
                start += lenself
            if stop < 0:
                stop += lenself
                
            start = min(lenself, max(0, start))
            stop  = min(lenself, max(0, stop))

            if step == 0:
                raise ValueError("slice step cannot be zero")
            else:
                length = (stop - start) // step
                data = numpy.empty((length,) + self.dims, dtype=self.dtype)
                data[:] = self._data[start:stop:step]
                if self.nullable:
                    mask = numpy.empty(length, dtype=numpy.bool_)
                    mask[:] = self._mask[start:stop:step]
                    return numpy.ma.MaskedArray(data, mask, fill_value=0)
                else:
                    return data

        else:
            if self.nullable and self._mask[index]:
                return None
            else:
                return self._data[index]





        
################################################################ FillArray

class FillArray(object):
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
                self._data[self._chunkindex][self._indexinchunk] = 0
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


