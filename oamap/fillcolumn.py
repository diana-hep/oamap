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
import struct
import sys

import numpy

if sys.version_info[0] > 2:
    xrange = range

class FillColumn(object):
    def __init__(self, dtype, dims):
        raise NotImplementedError
    def append(self, value):
        raise NotImplementedError
    def extend(self, values):
        raise NotImplementedError
    def flush(self):
        pass
    def __len__(self):
        raise NotImplementedError
    def __getitem__(self, index):
        raise NotImplementedError
    def close(self):
        pass

################################################################ FillList

class FillList(FillColumn):
    def __init__(self, dtype, dims):
        self.dtype = dtype
        self.dims = dims
        self._data = []
        self._index = 0

    def append(self, value):
        # possibly correct for a previous exception (to ensure same semantics as FillArray, FillFile)
        if self._index < len(self._data):
            del self._data[self._index:]

        self._data.append(value)

        # no exceptions? acknowledge the new data point
        self._index += 1

    def extend(self, values):
        if self._index < len(self._data):
            del self._data[self._index:]

        self._data.extend(values)

        self._index += len(values)
        
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
                out[:] = self._data[start:stop:step]
                return out

        else:
            return self._data[index]
        
################################################################ FillArray

class FillArray(FillColumn):
    # Numpy arrays and list items have 96+8 byte (80+8 byte) overhead in Python 2 (Python 3)
    # compared to 8192 1-byte values (8-byte values), this is 1% overhead (0.1% overhead)
    def __init__(self, dtype, dims, chunksize=8192):
        self.dtype = dtype
        self.dims = dims
        self.chunksize = chunksize
        self._data = [numpy.empty((self.chunksize,) + self.dims, dtype=self.dtype)]
        self._indexinchunk = 0
        self._chunkindex = 0

    def append(self, value):
        # possibly add a new chunk
        if self._indexinchunk >= len(self._data[self._chunkindex]):
            while len(self._data) <= self._chunkindex + 1:
                self._data.append(numpy.empty((self.chunksize,) + self.dims, dtype=self.dtype))
            self._indexinchunk = 0
            self._chunkindex += 1

        self._data[self._chunkindex][self._indexinchunk] = value

        # no exceptions? acknowledge the new data point
        self._indexinchunk += 1

    def extend(self, values):
        chunkindex = self._chunkindex
        indexinchunk = self._indexinchunk

        while len(values) > 0:
            if indexinchunk >= len(self._data[chunkindex]):
                while len(self._data) <= chunkindex + 1:
                    self._data.append(numpy.empty((self.chunksize,) + self.dims, dtype=self.dtype))
                indexinchunk = 0
                chunkindex += 1

            tofill = min(len(values), self.chunksize - indexinchunk)
            self._data[chunkindex][indexinchunk : indexinchunk + tofill] = values[:tofill]
            indexinchunk += tofill
            values = values[tofill:]

        self._chunkindex = chunkindex
        self._indexinchunk = indexinchunk

    def __len__(self):
        return self._chunkindex*self.chunksize + self._indexinchunk

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
                    if step > 0:
                        if chunkindex == start_chunkindex:
                            begin = start_indexinchunk
                        else:
                            begin = offset
                        if chunkindex == stop_chunkindex - 1:
                            end = stop_indexinchunk
                        else:
                            end = self.chunksize

                    else:
                        if chunkindex == start_chunkindex:
                            begin = start_indexinchunk
                        else:
                            begin = self.chunksize - offset
                        if chunkindex == stop_chunkindex + 1:
                            end = stop_indexinchunk
                        else:
                            end = 0

                    array = self._data[chunkindex][begin:end:step]

                    offset = (end - begin) % step
                    out[outi : outi + len(array)] = array
                    outi += len(array)
                    if outi >= len(out):
                        break

                return out

        else:
            lenself = len(self)
            normalindex = index if index >= 0 else index + lenself
            if not 0 <= normalindex < lenself:
                raise IndexError("index {0} is out of bounds for size {1}".format(index, lenself))

            chunkindex, indexinchunk = divmod(index, self.chunksize)
            return self._data[chunkindex][indexinchunk]

################################################################ FillFile

class FillFile(FillColumn):
    def __init__(self, dtype, dims, filename, flushsize=8192, lendigits=16):
        if not isinstance(dtype, numpy.dtype):
            dtype = numpy.dtype(dtype)
        self._data = numpy.empty((flushsize,) + dims, dtype=dtype)
        self._index = 0
        self._indexinchunk = 0
        self._indexflushed = 0
        self._filename = filename

        magic = b"\x93NUMPY\x01\x00"
        header1 = "{{'descr': {0}, 'fortran_order': False, 'shape': (".format(repr(self.dtype)).encode("ascii")
        header2 = "{0}, }}".format(repr((10**lendigits - 1,) + self.dims)).encode("ascii")[1:]

        unpaddedlen = len(magic) + 2 + len(header1) + len(header2)
        paddedlen = int(math.ceil(float(unpaddedlen) / dtype.itemsize)) * dtype.itemsize
        header2 = header2 + b" " * (paddedlen - unpaddedlen)
        self._lenpos = len(magic) + 2 + len(header1)
        self._datapos = len(magic) + 2 + len(header1) + len(header2)
        assert self._datapos % dtype.itemsize == 0

        self._file = open(filename, "r+b", 0)
        self._file.truncate(0)
        self._formatter = "{0:%dd}" % lendigits
        self._file.write(magic)
        self._file.write(struct.pack("<H", len(header1) + len(header2)))
        self._file.write(header1)
        self._file.write(self._formatter.format(self._index).encode("ascii"))
        self._file.write(header2[lendigits:])
        
    @property
    def dtype(self):
        return self._data.dtype

    @property
    def dims(self):
        return self._data.shape[1:]

    def append(self, value):
        self._data[self._indexinchunk] = value

        # no exceptions? acknowledge the new data point
        self._index += 1
        self._indexinchunk += 1

        # possibly flush to file
        if self._indexinchunk >= len(self._data):
            self.flush()

    def extend(self, values):
        index = self._index
        indexinchunk = self._indexinchunk
        indexflushed = self._indexflushed

        while len(values) > 0:
            tofill = min(len(values), len(self._data) - indexinchunk)
            self._data[indexinchunk : indexinchunk + tofill] = values[:tofill]
            index += tofill
            indexinchunk += tofill
            values = values[tofill:]

            self._file.seek(self._datapos + indexflushed*self.dtype.itemsize)
            self._file.write(self._data[:indexinchunk].tostring())
            indexinchunk = 0
            indexflushed = index
            
        self._file.seek(self._lenpos)
        self._file.write(self._formatter.format(index).encode("ascii"))
        self._index = index
        self._indexinchunk = 0
        self._indexflushed = indexflushed
            
    def flush(self):
        self._file.seek(self._datapos + self._indexflushed*self.dtype.itemsize)
        self._file.write(self._data[:self._indexinchunk].tostring())
        self._file.seek(self._lenpos)
        self._file.write(self._formatter.format(self._index).encode("ascii"))
        self._indexinchunk = 0
        self._indexflushed = self._index

    def __len__(self):
        return self._index

    def __getitem__(self, value):
        if isinstance(value, slice):
            array = numpy.memmap(self._filename, self.dtype, "r", self._datapos, (len(self),) + self.dims, "C")
            return array[value]

        else:
            lenself = len(self)
            normalindex = index if index >= 0 else index + lenself
            if not 0 <= normalindex < lenself:
                raise IndexError("index {0} is out of bounds for size {1}".format(index, lenself))

            if not self._file.closed:
                itemsize = self.dtype.itemsize
                self._file.seek(self._datapos + normalindex*itemsize)
                return numpy.fromstring(self._file.read(itemsize), self.dtype)[0]
            else:
                return self[normalindex : normalindex + 1][0]

    def close(self):
        if hasattr(self, "_file"):
            self.flush()
            self._file.close()

    def __del__(self):
        self.close()

    def __enter__(self, *args, **kwds):
        return self

    def __exit__(self, *args, **kwds):
        self.close()
