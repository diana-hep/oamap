import ast
import struct
import zipfile

import numpy

from pquiver.flat.defs import Array
from pquiver.flat.defs import ArrayInMemory
from pquiver.flat.defs import ArrayStream
from pquiver.flat.defs import ArrayGroup

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
            self._arrays.append(numpy.empty(arraylength, dtype=self._arrays[-1].dtype))
            self._lastlength = 0

        self._arrays[-1][self._lastlength] = value
        self._lastlength += 1
        self._last += 1

    def reset(self):
        self._arrays = [self._arrays[-1]]
        self._length = 0
        self._lastlength = 0

    class Iterator(object):
        def __init__(self, arrays, length):
            self._arrays = arrays
            self._countdown = 0
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

def numpyheader(stream):
    assert stream.read(6) == "\x93NUMPY"

    version = struct.unpack("bb", stream.read(2))
    if version[0] == 1:
        headerlen, = struct.unpack("<H", stream.read(2))
    else:
        headerlen, = struct.unpack("<I", stream.read(4))

    header = stream.read(headerlen)
    return ast.literal_eval(header)

def numpydtypelen(stream):
    header = numpyheader(stream)
    assert len(headerdata["shape"]) == 1
    return numpy.dtype(headerdata["descr"]), headerdata["shape"][0]

class NumpyStream(ArrayStream):
    def __init__(self, stream):
        dtype, length = numpydtypelen(stream)
        super(NumpyStream, self).__init__(stream, dtype, length)

class NumpyInMemoryGroup(ArrayGroup):
    def __init__(self, prefix, arrays):
        # give it a dict from str names to Numpy arrays
        super(NumpyInMemoryGroup, self).__init__(prefix, dict((n, NumpyInMemory(a)) for n, a in arrays.items()))
