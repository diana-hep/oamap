import ast
import struct
import zipfile

from shredtypes.flat.defs import *

try:
    import numpy
except ImportError:
    pass
else:

    class NumpyInMemory(ArrayInMemory):
        def __init__(self, array):
            assert len(array.shape) == 1
            super(NumpyInMemory, self).__init__(array, array.dtype, array.shape[0])

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

    class NumpyZipGroup(ArrayGroup):
        def __init__(self, filelike):
            self._zipfile = zipfile.ZipFile(filelike)
            self._names = sorted(x[:-4] for x in zf.infolist() if x.endswith(".npy"))

        def byname(self, name):
            return NumpyStream(self._zipfile.open(name + ".npy"))

        def byindex(self, index):
            return self.byname(self._names[index])

    del numpy

del ast
del struct
del zipfile
