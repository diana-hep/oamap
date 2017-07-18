#!/usr/bin/env python

# Copyright 2017 DIANA-HEP
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import ast
import ctypes
import struct

import numpy
import numba

# from rolup.util import *
# from rolup.typesystem import *
# from rolup.typesystem.arrayname import ArrayName

class LibC(object):
    def __init__(self, location):
        self.location = location
        self._libc = None

    def __load(self):
        if self._libc is None:
            self._libc = ctypes.cdll.LoadLibrary(self.location)

            # ssize_t read (int __fd, void *__buf, size_t __nbytes)
            self._read = self._libc.read
            # self._read.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t]
            self._read.argtypes = [ctypes.c_int, ctypes.c_size_t, ctypes.c_size_t]
            self._read.restype = ctypes.c_ssize_t

            # void *malloc (size_t __size)
            self._malloc = self._libc.malloc
            self._malloc.argtypes = [ctypes.c_size_t]
            # self._malloc.restype = ctypes.c_void_p
            self._malloc.restype = ctypes.c_size_t

            # void free (void *__ptr)
            self._free = self._libc.free
            # self._free.argtypes = [ctypes.c_void_p]
            self._free.argtypes = [ctypes.c_size_t]
            self._free.restype = None

    @property
    def read(self):
        self.__load()
        return self._read

    @property
    def malloc(self):
        self.__load()
        return self._malloc

    @property
    def free(self):
        self.__load()
        return self._free

libc = LibC("libc.so.6")

# class NumpyFileReader(object):
#     def __init__(self, file):

file = open("/home/pivarski/test.npy", "rb")

assert file.read(6) == b"\x93NUMPY"

version = struct.unpack("bb", file.read(2))
if version[0] == 1:
    headerlen, = struct.unpack("<H", file.read(2))
else:
    headerlen, = struct.unpack("<I", file.read(4))

header = file.read(headerlen)
headerobj = ast.literal_eval(header)

dtype = numpy.dtype(headerobj["descr"])
length, = headerobj["shape"]   # must be one-dimensional

fileno = numba.types.intc(file.fileno())
itemsize = numba.types.uint64(dtype.itemsize)
info = numpy.array([0, 0], dtype=numpy.uint64)  # bufferptr, buffersize
libc_read = libc.read
libc_malloc = libc.malloc
libc_free = libc.free

@numba.cfunc(numba.types.uint64(numba.types.uint64, numba.types.CPointer(numba.types.uint64)), nopython=True)
def read(numitems, info):
    bufferptr = info[0]
    buffersize = info[1]

    if numitems * itemsize > buffersize:
        if bufferptr != 0:
            libc_free(bufferptr)
        bufferptr = libc_malloc(buffersize)
        buffersize = numitems * itemsize
        info[0] = bufferptr
        info[1] = buffersize
        if bufferptr == 0:
            return False
    
    bytesread = libc_read(fileno, bufferptr, buffersize)
    return bytesread

callme = ctypes.CFUNCTYPE(ctypes.c_uint64, ctypes.c_uint64, ctypes.POINTER(ctypes.c_int64))(read.address)
print callme(100, info.ctypes.data_as(ctypes.POINTER(ctypes.c_int64)))

@numba.cfunc(numba.types.float64(numba.types.uint64, numba.types.CPointer(numba.types.CPointer(numba.types.float64))), nopython=True)
def get(index, info):
    bufferptr = info[0]
    return numba.carray(bufferptr, (index,))[index]

callme2 = ctypes.CFUNCTYPE(ctypes.c_double, ctypes.c_uint64, ctypes.POINTER(ctypes.POINTER(ctypes.c_double)))(get.address)
print callme2(0, info.ctypes.data_as(ctypes.POINTER(ctypes.POINTER(ctypes.c_double))))
