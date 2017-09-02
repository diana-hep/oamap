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

class LazyArray(object):
    def __init__(self):
        self.array = None

    def _load(self):
        raise NotImplementedError("LazyArray must be subclassed")

    def __getitem__(self, i):
        if self.array is None: self._load()
        return self.array[i]

    def __len__(self):
        if self.array is None: self._load()
        return len(self.array)

    def cumsum(self, axis=None, dtype=None, out=None):
        if self.array is None: self._load()
        return self.array.cumsum(axis=axis, dtype=dtype, out=out)

    def size2offset(self):
        return LazyOffsetArray(self)

    def offset2begin(self):
        return LazyBeginArray(self)

    def offset2end(self):
        return LazyEndArray(self)

class LazyOffsetArray(LazyArray):
    def __init__(self, sizearray):
        super(LazyOffsetArray, self).__init__()
        self.sizearray = sizearray

    def _load(self):
        self.array = numpy.empty(len(self.sizearray) + 1, dtype=numpy.int64)
        self.array[0] = 0
        self.sizearray.cumsum(out=self.array[1:])

class LazyBeginArray(LazyArray):
    def __init__(self, offsetarray):
        super(LazyBeginArray, self).__init__()
        self.offsetarray = offsetarray

    def _load(self):
        self.array = self.offsetarray[:-1]

class LazyEndArray(LazyArray):
    def __init__(self, offsetarray):
        super(LazyEndArray, self).__init__()
        self.offsetarray = offsetarray

    def _load(self):
        self.array = self.offsetarray[1:]
