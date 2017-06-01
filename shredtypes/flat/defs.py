import struct

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

class Cursor(object):
    def __init__(self, data, size):
        self.data = data
        self.size = size
        self.dataindex = 0
        self.sizeindex = 0

class ArrayGroup(object):
    def __init__(self, **arrays):
        self._namespace = arrays.copy()
        self._names = sorted(self._namespace)
        self._values = [self._namespace[x] for x in self._names]

    @property
    def num(self):
        return len(self._names)

    @property
    def names(self):
        return self._names

    def byname(self, name):
        return self._namespace[name]

    def byindex(self, index):
        return self._values[self._order[index]]

    def cursor(self, dataname, sizename):
        return Cursor(self.byname(dataname), self.byname(sizename))
