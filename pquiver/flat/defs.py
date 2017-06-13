import struct

from pquiver.typesystem.naming import ArrayName

class Array(object):
    def __init__(self, dtype, length):
        self._dtype = dtype
        self._length = length

    @property
    def dtype(self):
        return self._dtype

    @property
    def length(self):
        return self._length

class ArrayInMemory(Array):
    def __init__(self, array, dtype, length):
        self._array = array
        super(ArrayInMemory, self).__init__(dtype, length)

    @property
    def array(self):
        return self._array

    def byindex(self, index):
        if index < 0 or index >= self._length:
            raise IndexError("index {0} out of bounds for ArrayInMemory".format(index))
        else:
            return self._array[index]

    class Iterator(object):
        def __init__(self, array, length):
            self._array = array
            self._length = length
            self._index = 0

        def __next__(self):
            if self._index < self._length:
                out = self._array[self._index]
                self._index += 1
                return out
            else:
                raise StopIteration

        next = __next__

    def __iter__(self):
        return self.Iterator(self._array, self._length)

class ArrayInMemoryPages(Array):
    def __init__(self, arrays, dtype, length):
        assert len(arrays) > 0
        for a in arrays:
            assert len(a.shape) == 1
        self._arrays = arrays
        super(ArrayInMemoryPages, self).__init__(dtype, length)

    @property
    def pages(self):
        return self._arrays

    def byindex(self, index):
        if index < 0 or index >= self._length:
            raise IndexError("index {0} out of bounds for ArrayInMemoryPages".format(index))
        for array in self._arrays:
            if index >= self._arrays.shape[0]:
                index -= self._arrays.shape[0]
            else:
                return self._arrays[index]
        assert False, "index reduced to {0} after {1} for length {2}".format(index, sum(a.shape[0] for a in self._arrays), self._length)

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
            
class ArrayStream(Array):
    class Iterator(object):
        def __init__(self, stream, itemsize, length, cast):
            self._stream = stream
            self._itemsize = itemsize
            self._length = length
            self._cast = cast
            self._index = 0

        def __next__(self):
            if self._index < self._length:
                self._index += 1
                return self._cast(self._stream._read(self._itemsize))
            else:
                raise StopIteration

        next = __next__

    def __init__(self, stream, dtype, length):
        self._stream = stream
        super(ArrayStream, self).__init__(dtype, length)

    @property
    def stream(self):
        return self._stream

    def __iter__(self):
        cast = None

        if self._dtype.kind == "c":
            if self._dtype.itemsize == 8:
                format = self._dtype.byteorder + "ff"
                cast = lambda bytes: complex(*struct.unpack(format, bytes))
            elif self._dtype.itemsize == 16:
                format = self._dtype.byteorder + "dd"
                cast = lambda bytes: complex(*struct.unpack(format, bytes))

        elif self._dtype.kind == "f":
            if self._dtype.itemsize == 4:
                format = self._dtype.byteorder + "f"
                cast = lambda bytes: struct.unpack(format, bytes)[0]
            elif self._dtype.itemsize == 8:
                format = self._dtype.byteorder + "d"
                cast = lambda bytes: struct.unpack(format, bytes)[0]

        elif self._dtype.kind == "i":
            if self._dtype.itemsize == 1:
                cast = lambda bytes: struct.unpack("b", bytes)[0]
            elif self._dtype.itemsize == 2:
                format = self._dtype.byteorder + "h"
                cast = lambda bytes: struct.unpack(format, bytes)[0]
            elif self._dtype.itemsize == 4:
                format = self._dtype.byteorder + "i"
                cast = lambda bytes: struct.unpack(format, bytes)[0]
            elif self._dtype.itemsize == 8:
                format = self._dtype.byteorder + "q"
                cast = lambda bytes: struct.unpack(format, bytes)[0]

        elif self._dtype.kind == "u":
            if self._dtype.itemsize == 1:
                cast = lambda bytes: struct.unpack("B", bytes)[0]
            elif self._dtype.itemsize == 2:
                format = self._dtype.byteorder + "H"
                cast = lambda bytes: struct.unpack(format, bytes)[0]
            elif self._dtype.itemsize == 4:
                format = self._dtype.byteorder + "I"
                cast = lambda bytes: struct.unpack(format, bytes)[0]
            elif self._dtype.itemsize == 8:
                format = self._dtype.byteorder + "Q"
                cast = lambda bytes: struct.unpack(format, bytes)[0]

        if cast is None:
            import numpy
            cast = lambda bytes: numpy.asscalar(numpy.array(map(ord, bytes), dtype=numpy.uint8).view(self._dtype.itemsize))

        return self.Iterator(self._stream, self._dtype.itemsize, self._length, cast)

class ArrayGroup(object):
    def __init__(self, prefix, arrays):
        # give it a dict from str names to Arrays
        self._arrays = tuple((ArrayName.parse(prefix, n), arrays[n]) for n in sorted(arrays))
        
    @property
    def numArrays(self):
        return len(self._arrays)

    @property
    def pairs(self):
        return self._arrays

    @property
    def names(self):
        return [n for n, a in self._arrays]

    @property
    def strnames(self):
        return [str(n) for n, a in self._arrays]

    @property
    def arrays(self):
        return [a for n, a in self._arrays]

    @property
    def asdict(self):
        return dict(self._arrays)

    @property
    def asstrdict(self):
        return dict((str(n), a) for n, a in self._arrays)

    def byname(self, name):
        for n, a in self._arrays:
            if n == name:
                return a
        raise KeyError("name {0} not found in ArrayGroup".format(name))

    def bystrname(self, name):
        for n, a in self._arrays:
            if str(n) == name:
                return a
        raise KeyError("name \"{0}\" not found in ArrayGroup".format(name))

    def byindex(self, index):
        if index < 0 or index >= len(self._arrays):
            raise IndexError("index {0} out of bounds for ArrayGroup".format(index))
        else:
            return self._arrays[index][1]
