import ast
import struct
import zipfile

import numpy

from plour.flat.defs import Array
from plour.flat.defs import ArrayInMemory
from plour.flat.defs import ArrayStream
from plour.flat.defs import ArrayGroup

def npzipheader(stream):
    assert stream.read(6) == "\x93NUMPY"

    version = struct.unpack("bb", stream.read(2))
    if version[0] == 1:
        headerlen, = struct.unpack("<H", stream.read(2))
    else:
        headerlen, = struct.unpack("<I", stream.read(4))

    header = stream.read(headerlen)
    return ast.literal_eval(header)

def npzipinfo(stream):
    header = npzipheader(stream)
    assert len(headerdata["shape"]) == 1
    return numpy.dtype(headerdata["descr"]), headerdata["shape"][0]

class NumpyInMemory(ArrayInMemory):
    def __init__(self, array):
        assert len(array.shape) == 1
        super(NumpyInMemory, self).__init__(array, array.dtype, array.shape[0])

    @staticmethod
    def fromzip(file, names):
        if len(names) == 1:
            assert not names[0].ispage
            array = numpy.load(file)[names[0]]

        else:
            assert [n.pagenumber() for n in names] == list(range(len(names)))
            zf = zipfile.ZipFile(file)

            offsets = [0]
            for name in names:
                dtype, l = npzipinfo(zf[name + ".npy"])
                offsets.append(offsets[-1] + l)

            array = numpy.empty(length, dtype=dtype)

            np = numpy.load(file)
            for name, start, end in zip(names, offsets[:-1], offsets[1:]):
                array[start:end] = np[name]

        return NumpyInMemory(array)

class NumpyInMemoryPages(ArrayInMemoryPages):
    def __init__(self, arrays):
        assert len(arrays) > 0
        super(NumpyInMemoryPages, self).__init__(arrays, arrays[0].dtype, sum(a.shape[0] for a in arrays))

    @staticmethod
    def fromzip(file, names):
        if len(names) == 1:
            assert not names[0].ispage
            arrays = [numpy.load(file)[names[0]]]

        else:
            assert [n.pagenumber() for n in names] == list(range(len(names)))
            np = numpy.load(file)
            arrays = [np[n] for n in names]

        return NumpyInMemoryPages(arrays)

class NumpyFillable(ArrayInMemoryPages):
    def __init__(self, dtype, chunksize=1024**2):    # 1 MB
        assert chunksize > 0
        self._arrays = [numpy.empty(chunksize // dtype.itemsize, dtype=dtype)]
        self._length = 0
        self._lastlength = 0

    @property
    def length(self):
        return self._length

    @property
    def concatenated(self):
        return numpy.concatenate(self._arrays)

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

    def __iter__(self):
        return self.Iterator(self._arrays, self._length)

class NumpyZipStream(ArrayStream):
    def __init__(self, stream):
        dtype, length = npzipinfo(stream)
        super(NumpyStream, self).__init__(stream, dtype, length)

class NumpyInMemoryGroup(ArrayGroup):
    def __init__(self, prefix, arrays):
        # give it a dict from str names to Numpy arrays
        super(NumpyInMemoryGroup, self).__init__(prefix, dict((n, NumpyInMemory(a)) for n, a in arrays.items()))

    @staticmethod
    def fromzip(prefix, file, concatenate=True):
        zf = zipfile.ZipFile(file)
        names = {}
        for n in [x.name[:-4] for x in zf.infolist() if x.name.startswith(prefix) and x.name.endswith(".npy")]:
            full = ArrayName.parse(prefix, n)
            unpaged = full.droppage()

            if unpaged not in names:
                names[unpaged] = []
            names[unpaged].append(full)

        arrays = {}
        for unpaged, ns in names.items():
            if concatenate:
                arrays[unpaged] = NumpyInMemory.fromzip(file, sorted(ns), concatenate)
            else:
                arrays[unpaged] = NumpyInMemoryPages.fromzip(file, sorted(ns), concatenate)

        return NumpyInMemoryGroup(prefix, arrays)

class NumpyFillableGroup(ArrayGroup):
    def __init__(self, prefix, dtypes, chunksize=1024**2):    # 1 MB
        super(NumpyFillableGroup, self).__init__(prefix, dict((n, NumpyFillable(d, chunksize)) for n, d in dtypes.items()))

    def reset(self):
        for a in self.arrays:
            a.reset()

    def write(self, file, compress=True, concatenate=True):
        out = {}
        for n, a in self.pairs:
            assert not n.ispage
            if concatenate:
                out[str(n)] = a.concatenated
            else:
                for i, page in enumerate(a.pages):
                    out[str(n.page(i))] = page

        if compress:
            numpy.savez_compressed(file, **out)
        else:
            numpy.savez(file, **out)
