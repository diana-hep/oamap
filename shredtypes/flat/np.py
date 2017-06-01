import ast
import struct
import zipfile

from shredtypes.flat.defs import *

import numpy

class NumpyInMemory(ArrayInMemory):
    def __init__(self, array):
        assert len(array.shape) == 1
        super(NumpyInMemory, self).__init__(array, array.dtype, array.shape[0])

class NumpyFillable(ArrayInMemory):
    def __init__(self, dtype, chunksize=1024**2):    # 1 MB
        assert chunksize > 0
        self._arrays = [numpy.empty(chunksize // dtype.itemsize, dtype=dtype)]
        self._length = 0
        self._lastlength = 0

    @property
    def length(self):
        return self._length

    def append(self, value):
        arraylength = self._arrays[0].shape[0]
        if self._lastlength >= arraylength:
            self._arrays.append(numpy.empty(arraylength, dtype=self._arrays[0].dtype))
            self._lastlength = 0

        self._arrays[-1][self._lastlength] = value
        self._lastlength += 1
        self._length += 1

    @property
    def contiguous(self):
        arrays = list(self._arrays)
        arrays[-1] = arrays[-1][:self._lastlength]
        return numpy.concatenate(arrays)

    class Iterator(object):
        def __init__(self, arrays, length):
            self._arrays = arrays
            self._countdown = length
            self._arrayindex = 0
            self._index = 0

        def __next__(self):
            if self._countdown == 0:
                raise StopIteration
            self._countdown -= 1

            array = self._arrays[self._arrayindex]
            if self._index >= array.shape[0]:
                self._arrayindex += 1
                self._index = 0
                array = self._arrays[self._arrayindex]

            out = array[self._index]
            self._index += 1
            return out

        next = __next__

    def __iter__(self):
        return self.Iterator(self._arrays, self._length)

class NumpyStream(ArrayStream):
    def __init__(self, stream):
        assert stream.read(6) == "\x93NUMPY"

        version = struct.unpack("bb", stream.read(2))
        if version[0] == 1:
            headerlen, = struct.unpack("<H", stream.read(2))
        else:
            headerlen, = struct.unpack("<I", stream.read(4))

        header = stream.read(headerlen)
        headerdata = ast.literal_eval(header)

        dtype = numpy.dtype(headerdata["descr"])
        assert len(headerdata["shape"]) == 1

        super(NumpyStream, self).__init__(stream, dtype, headerdata["shape"][0])

class NumpyInMemoryGroup(ArrayGroup):
    def __init__(self, **arrays):
        super(NumpyGroup, self).__init__(dict((n, NumpyInMemory(v)) for n, v in arrays.items()))

class NumpyFillableGroup(ArrayGroup):
    chunksize = 1024**2   # 1 MB

    def __init__(self, **dtypes):
        self._dtypes = dtypes
        self.reset()

    def reset(self):
        super(NumpyFillableGroup, self).__init__(dict(n, NumpyFillable(d, self.chunksize)) for n, d in self._dtypes.items())

    def write(self, file, compress=True):
        arrays = dict((n, self.byname(n).contiguous) for n in self.names)
        if compress:
            numpy.savez_compressed(file, arrays)
        else:
            numpy.savez(file, arrays)

class NumpyZipGroup(ArrayGroup):
    def __init__(self, filelike):
        self._zipfile = zipfile.ZipFile(filelike)
        self._names = sorted(x[:-4] for x in zf.infolist() if x.endswith(".npy"))

    def byname(self, name):
        return NumpyStream(self._zipfile.open(name + ".npy"))

    def byindex(self, index):
        return self.byname(self._names[index])
