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

import numpy

class ArrayInMemoryPages(object):
    def __init__(self, dtype, chunksize=4096):
        self.pages = [numpy.empty(chunksize // dtype.itemsize, dtype=dtype)]
        self.length = 0
        self.lastindex = 0

    def append(self, value):
        arraylength = self.arrays[-1].shape[0]
        if self.lastindex >= arraylength:
            self.arrays.append(numpy.empty(arraylength, dtype=self.arrays[-1].dtype))
            self.lastindex = 0

        self.arrays[-1][self.lastindex] = value
        self.lastindex += 1
        self.length += 1

    def array(self):
        return numpy.concatenate(self.arrays)[:self.length]

    def __getitem__(self, index):
        if index < 0 or index >= self.length:
            raise IndexError("index {0} out of bounds for ArrayInMemoryPages".format(index))
        for array in self.arrays:
            if index >= array.shape[0]:
                index -= array.shape[0]
            else:
                return array[index]
        assert False, "index reduced to {0} after {1} for length {2}".format(index, sum(x.shape[0] for x in self.arrays), self.length)

    def __setitem__(self, index, value):
        if index < 0 or index >= self.length:
            raise IndexError("index {0} out of bounds for ArrayInMemoryPages".format(index))
        for array in self.arrays:
            if index >= array.shape[0]:
                index -= array.shape[0]
            else:
                array[index] = value
        assert False, "index reduced to {0} after {1} for length {2}".format(index, sum(x.shape[0] for x in self.arrays), self.length)

    class Iterator(object):
        def __init__(self, arrays, length):
            self.arrays = arrays
            self.countdown = length
            self.arrayindex = 0
            self.index = 0

        def __next__(self):
            if self.countdown == 0:
                raise StopIteration
            self.countdown -= 1

            array = self.arrays[self.arrayindex]
            if self.index >= array.shape[0]:
                self.arrayindex += 1
                self.index = 0
                array = self.arrays[self.arrayindex]

            out = array[self.index]
            self.index += 1
            return out

    def __iter__(self):
        return self.Iterator(self.arrays, self.length)
