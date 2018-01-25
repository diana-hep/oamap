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

import os
import math
import struct
import sys

import numpy

import oamap.generator

if sys.version_info[0] > 2:
    xrange = range

class Fillable(object):
    def __init__(self, dtype):
        raise NotImplementedError

    def __len__(self):
        return self._len

    def forefront(self):
        return self._chunkindex*self.chunksize + self._indexinchunk

    def append(self, value):
        raise NotImplementedError

    def extend(self, values):
        raise NotImplementedError

    def update(self):
        self._len = self.forefront()

    def revert(self):
        self._chunkindex, self._indexinchunk = divmod(self._len, self.chunksize)

    def close(self):
        pass

    def __getitem__(self, index):
        raise NotImplementedError

    def __array__(self, dtype=None, copy=False, order="K", subok=False, ndmin=0):
        if dtype is None:
            dtype = self.dtype
        elif not isinstance(dtype, numpy.dtype):
            dtype = numpy.dtype(dtype)

        if dtype == self.dtype and not copy and not subok and ndmin == 0:
            return self[:]
        else:
            return numpy.array(self[:], dtype=dtype, copy=copy, order=order, subok=subok, ndmin=ndmin)

################################################################ make fillables

def _makefillables(generator, fillables, makefillable):
    if isinstance(generator, oamap.generator.Masked):
        fillables[generator.mask] = makefillable(generator.mask, generator.maskdtype)

    if isinstance(generator, oamap.generator.PrimitiveGenerator):
        if generator.dtype is None:
            raise ValueError("dtype is unknown (None) for Primitive generator at {0}".format(repr(generator.data)))
        fillables[generator.data] = makefillable(generator.data, generator.dtype)

    elif isinstance(generator, oamap.generator.ListGenerator):
        fillables[generator.starts] = makefillable(generator.starts, generator.posdtype)
        fillables[generator.stops]  = makefillable(generator.stops,  generator.posdtype)
        _makefillables(generator.content, fillables, makefillable)

    elif isinstance(generator, oamap.generator.UnionGenerator):
        fillables[generator.tags]    = makefillable(generator.tags,    generator.tagdtype)
        fillables[generator.offsets] = makefillable(generator.offsets, generator.offsetdtype)
        for possibility in generator.possibilities:
            _makefillables(possibility, fillables, makefillable)

    elif isinstance(generator, oamap.generator.RecordGenerator):
        for field in generator.fields.values():
            _makefillables(field, fillables, makefillable)

    elif isinstance(generator, oamap.generator.TupleGenerator):
        for field in generator.types:
            _makefillables(field, fillables, makefillable)

    elif isinstance(generator, oamap.generator.PointerGenerator):
        fillables[generator.positions] = makefillable(generator.positions, generator.posdtype)
        if not generator._internal:
            _makefillables(generator.target, fillables, makefillable)

    elif isinstance(generator, oamap.generator.ExtendedGenerator):
        _makefillables(generator.generic, fillables, makefillable)

    else:
        raise AssertionError("unrecognized generator type: {0}".format(generator))

def arrays(generator, chunksize=8192):
    if not isinstance(generator, oamap.generator.Generator):
        generator = generator.generator()
    fillables = {}
    _makefillables(generator, fillables, lambda name, dtype: FillableArray(dtype, chunksize=chunksize))
    return fillables

def files(generator, directory, chunksize=8192, lendigits=16):
    if not isinstance(generator, oamap.generator.Generator):
        generator = generator.generator()
    if not os.path.exists(directory):
        os.mkdir(directory)
    fillables = {}
    _makefillables(generator, fillables, lambda name, dtype: FillableFile(os.path.join(directory, name), dtype, chunksize=chunksize, lendigits=lendigits))
    return fillables

def numpyfiles(generator, directory, chunksize=8192, lendigits=16):
    if not isinstance(generator, oamap.generator.Generator):
        generator = generator.generator()
    if not os.path.exists(directory):
        os.mkdir(directory)
    fillables = {}
    _makefillables(generator, fillables, lambda name, dtype: FillableNumpyFile(os.path.join(directory, name), dtype, chunksize=chunksize, lendigits=lendigits))
    return fillables

################################################################ FillableArray

class FillableArray(Fillable):
    # Numpy arrays and list items have 96+8 byte (80+8 byte) overhead in Python 2 (Python 3)
    # compared to 8192 1-byte values (8-byte values), this is 1% overhead (0.1% overhead)
    def __init__(self, dtype, chunksize=8192):
        if not isinstance(dtype, numpy.dtype):
            dtype = numpy.dtype(dtype)
        self._data = [numpy.empty(chunksize, dtype=dtype)]
        self._len = 0
        self._indexinchunk = 0
        self._chunkindex = 0

    @property
    def dtype(self):
        return self._data[0].dtype

    @property
    def chunksize(self):
        return self._data[0].shape[0]

    def append(self, value):
        if self._indexinchunk >= len(self._data[self._chunkindex]):
            while len(self._data) <= self._chunkindex + 1:
                self._data.append(numpy.empty(self.chunksize, dtype=self.dtype))
            self._indexinchunk = 0
            self._chunkindex += 1

        self._data[self._chunkindex][self._indexinchunk] = value
        self._indexinchunk += 1

    def extend(self, values):
        chunkindex = self._chunkindex
        indexinchunk = self._indexinchunk

        while len(values) > 0:
            if indexinchunk >= len(self._data[chunkindex]):
                while len(self._data) <= chunkindex + 1:
                    self._data.append(numpy.empty(self.chunksize, dtype=self.dtype))
                indexinchunk = 0
                chunkindex += 1

            tofill = min(len(values), self.chunksize - indexinchunk)
            self._data[chunkindex][indexinchunk : indexinchunk + tofill] = values[:tofill]
            indexinchunk += tofill
            values = values[tofill:]

        self._chunkindex = chunkindex
        self._indexinchunk = indexinchunk

    def __getitem__(self, index):
        if isinstance(index, slice):
            lenself = len(self)
            step  = 1 if index.step is None else index.step
            if step > 0:
                start = 0       if index.start is None else index.start
                stop  = lenself if index.stop  is None else index.stop
            else:
                start = lenself - 1 if index.start is None else index.start
                stop  = 0           if index.stop  is None else index.stop
                
            if start < 0:
                start += lenself
            if stop < 0:
                stop += lenself

            start = min(lenself, max(0, start))
            stop  = min(lenself, max(0, stop))

            if step == 0:
                raise ValueError("slice step cannot be zero")

            else:
                if step > 0:
                    start_chunkindex = int(math.floor(float(start) / self.chunksize))
                    stop_chunkindex = int(math.ceil(float(stop) / self.chunksize))
                    start_indexinchunk = start - start_chunkindex*self.chunksize
                    stop_indexinchunk = stop - (stop_chunkindex - 1)*self.chunksize
                else:
                    start_chunkindex = int(math.floor(float(start) / self.chunksize))
                    stop_chunkindex = int(math.floor(float(stop) / self.chunksize)) - 1
                    start_indexinchunk = start - start_chunkindex*self.chunksize
                    stop_indexinchunk = stop - (stop_chunkindex + 1)*self.chunksize

                def beginend():
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
                                offset = (begin - self.chunksize) % step
                        else:
                            if chunkindex == start_chunkindex:
                                begin = start_indexinchunk
                            else:
                                begin = self.chunksize - 1 - offset
                            if chunkindex == stop_chunkindex + 1 and index.stop is not None:
                                end = stop_indexinchunk
                            else:
                                end = None
                                offset = (begin - -1) % -step
                        yield chunkindex, begin, end

                length = 0
                for chunkindex, begin, end in beginend():
                    if step > 0:
                        length += int(math.ceil(float(end - begin) / step))
                    elif end is None:
                        length += int(math.ceil(-float(begin + 1) / step))
                    else:
                        length += int(math.ceil(-float(begin - end) / step))

                out = numpy.empty(length, dtype=self.dtype)
                outi = 0

                for chunkindex, begin, end in beginend():
                    array = self._data[chunkindex][begin:end:step]

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

################################################################ FillableFile

class FillableFile(Fillable):
    def __init__(self, filename, dtype, chunksize=8192, lendigits=16):
        if not isinstance(dtype, numpy.dtype):
            dtype = numpy.dtype(dtype)
        self._data = numpy.zeros(chunksize, dtype=dtype)  # 'zeros', not 'empty' for security
        self._len = 0
        self._indexinchunk = 0
        self._chunkindex = 0
        self._filename = filename
        self._openfile(filename, lendigits)

    def _openfile(self, filename, lendigits):
        open(filename, "wb", 0).close()
        self._file = open(filename, "r+b", 0)
        self._datapos = 0
        # a plain file has no header

    @property
    def filename(self):
        return self._file.name

    @property
    def dtype(self):
        return self._data.dtype

    @property
    def chunksize(self):
        return self._data.shape[0]

    def append(self, value):
        self._data[self._indexinchunk] = value
        self._indexinchunk += 1

        if self._indexinchunk == self.chunksize:
            self._flush()
            self._indexinchunk = 0
            self._chunkindex += 1

    def _flush(self):
        self._file.seek(self._datapos + self._chunkindex*self.chunksize*self.dtype.itemsize)
        self._file.write(self._data.tostring())
        
    def extend(self, values):
        chunkindex = self._chunkindex
        indexinchunk = self._indexinchunk

        while len(values) > 0:
            tofill = min(len(values), self.chunksize - indexinchunk)
            self._data[indexinchunk : indexinchunk + tofill] = values[:tofill]
            indexinchunk += tofill
            values = values[tofill:]

            if indexinchunk == self.chunksize:
                self._file.seek(self._datapos + chunkindex*self.chunksize*self.dtype.itemsize)
                self._file.write(self._data.tostring())
                indexinchunk = 0
                chunkindex += 1

        self._chunkindex = chunkindex
        self._indexinchunk = indexinchunk

    def revert(self):
        chunkindex, self._indexinchunk = divmod(self._len, self.chunksize)
        if self._chunkindex != chunkindex:
            self._file.seek(self._datapos + chunkindex*self.chunksize*self.dtype.itemsize)
            olddata = numpy.fromstring(self._file.read(self.chunksize*self.dtype.itemsize), dtype=self.dtype)
            self._data[:len(olddata)] = olddata

        self._chunkindex = chunkindex

    def close(self):
        if hasattr(self, "_file"):
            self._flush()
            self._file.close()

    def __del__(self):
        self.close()

    def __enter__(self, *args, **kwds):
        return self

    def __exit__(self, *args, **kwds):
        self.close()

    def __getitem__(self, value):
        if not self._file.closed:
            self._flush()

        if isinstance(value, slice):
            lenself = len(self)
            if lenself == 0:
                array = numpy.empty(lenself, dtype=self.dtype)
            else:
                array = numpy.memmap(self.filename, self.dtype, "r", self._datapos, lenself, "C")
            if value.start is None and value.stop is None and value.step is None:
                return array
            else:
                return array[value]

        else:
            lenself = len(self)
            normalindex = index if index >= 0 else index + lenself
            if not 0 <= normalindex < lenself:
                raise IndexError("index {0} is out of bounds for size {1}".format(index, lenself))

            if not self._file.closed:
                # since the file's still open, get it from here instead of making a new filehandle
                itemsize = self.dtype.itemsize
                try:
                    self._file.seek(self._datapos + normalindex*itemsize)
                    return numpy.fromstring(self._file.read(itemsize), self.dtype)[0]
                finally:
                    self._file.seek(self._datapos + self._chunkindex*self.chunksize*self.dtype.itemsize)
            else:
                # otherwise, you have to open a new file
                with open(self.filename, "rb") as file:
                    file.seek(self._datapos + normalindex*itemsize)
                    return numpy.fromstring(file.read(itemsize), self.dtype)[0]

################################################################ FillableNumpyFile (FillableFile with a self-describing header)

class FillableNumpyFile(FillableFile):
    def _openfile(self, filename, lendigits):
        magic = b"\x93NUMPY\x01\x00"
        header1 = "{{'descr': {0}, 'fortran_order': False, 'shape': (".format(repr(str(self.dtype))).encode("ascii")
        header2 = "{0}, }}".format(repr((10**lendigits - 1,))).encode("ascii")[1:]

        unpaddedlen = len(magic) + 2 + len(header1) + len(header2)
        paddedlen = int(math.ceil(float(unpaddedlen) / self.dtype.itemsize)) * self.dtype.itemsize
        header2 = header2 + b" " * (paddedlen - unpaddedlen)
        self._lenpos = len(magic) + 2 + len(header1)
        self._datapos = len(magic) + 2 + len(header1) + len(header2)
        assert self._datapos % self.dtype.itemsize == 0

        open(filename, "wb", 0).close()
        self._file = open(filename, "r+b", 0)
        self._formatter = "{0:%dd}" % lendigits
        self._file.write(magic)
        self._file.write(struct.pack("<H", len(header1) + len(header2)))
        self._file.write(header1)
        self._file.write(self._formatter.format(len(self)).encode("ascii"))
        self._file.write(header2[lendigits:])

    def _flush(self):
        super(FillableNumpyFile, self)._flush()
        self._file.seek(self._lenpos)
        self._file.write(self._formatter.format(len(self)).encode("ascii"))
