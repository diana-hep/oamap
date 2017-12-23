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

import sys

import numpy

if sys.version_info[0] > 2:
    xrange = range

class FillColumn(object):
    def __init__(self, dtype, dims=()):
        raise NotImplementedError
    def append(self, value):
        raise NotImplementedError
    def __len__(self):
        raise NotImplementedError
    def __getitem__(self, index):
        raise NotImplementedError
    def flush(self):
        pass
    def close(self):
        pass

################################################################ FillList

class FillList(FillColumn):
    def __init__(self, dtype, dims=()):
        self.dtype = dtype
        self.dims = dims
        self._array = []
        self._index = 0

    def append(self, value):
        if self._index < len(self._array): self._array[self._index] = value
        else: self._array.append(value)

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
                out = numpy.empty((length,) + self.dims, dtype=self.dtype)
                out[:] = self._array[start:stop:step]
                return out

        else:
            return self._array[index]
        
################################################################ FillArray

class FillArray(FillColumn):
    # Numpy arrays and list items have 96+8 byte (80+8 byte) overhead in Python 2 (Python 3)
    # compared to 8192 1-byte values (8-byte values), this is 1% overhead (0.1% overhead)
    def __init__(self, dtype, dims=(), chunksize=8192):
        self.dtype = dtype
        self.dims = dims
        self.chunksize = chunksize
        self._arrays = [numpy.empty((self.chunksize,) + self.dims, dtype=self.dtype)]
        self._indexinchunk = 0
        self._chunkindex = 0

    def append(self, value):
        if self._indexinchunk >= len(self._arrays[self._chunkindex]):
            self._arrays.append(numpy.empty((self.chunksize,) + self.dims, dtype=self.dtype))
            self._indexinchunk = 0
            self._chunkindex += 1
                
        self._arrays[self._chunkindex][self._indexinchunk] = value
        self._indexinchunk += 1

    def __len__(self):
        return max(0, self._chunkindex - 1)*self.chunksize + self._indexinchunk

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
                out = numpy.empty((length,) + self.dims, dtype=self.dtype)
                outi = 0

                start_chunkindex, start_indexinchunk = divmod(start, self.chunksize)
                stop_chunkindex,  stop_indexinchunk  = divmod(stop,  self.chunksize)
                if step > 0:
                    stop_chunkindex += 1
                else:
                    stop_chunkindex -= 1

                offset = 0
                for chunkindex in xrange(start_chunkindex, stop_chunkindex, 1 if step > 0 else -1):
                    if chunkindex == start_chunkindex:
                        if step > 0:
                            begin, end = start_indexinchunk, self.chunksize
                        else:
                            begin, end = start_indexinchunk, self.chunksize - offset
                    elif chunkindex == stop_chunkindex:
                        if step > 0:
                            begin, end = offset, stop_indexinchunk
                        else:
                            begin, end = 0, stop_indexinchunk
                    else:
                        if step > 0:
                            begin, end = offset, self.chunksize
                        else:
                            begin, end = 0, self.chunksize - offset

                    array = self._arrays[chunkindex][begin:end:step]
                    offset = (end - begin) % step
                    out[outi : outi + len(array)] = array
                    outi += len(array)

                return out

        else:
            lenself = len(self)
            normalindex = index if index >= 0 else index + lenself
            if not 0 <= normalindex < lenself:
                raise IndexError("index {0} is out of bounds for size {1}".format(index, lenself))

            chunkindex, indexinchunk = divmod(index, self.chunksize)
            return self._arrays[chunkindex][indexinchunk]

################################################################ FillFile

class FillFile(FillColumn):
    pass
