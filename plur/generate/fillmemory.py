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

class FillableMemory(object):
    def __init__(self, dtype, chunksize=4096):
        self.pages = [numpy.empty(chunksize // dtype.itemsize, dtype=dtype)]
        self.length = 0
        self.lastindex = 0

    def fill(self, value):
        pagelength = self.pages[-1].shape[0]
        if self.lastindex >= pagelength:
            self.pages.append(numpy.empty(pagelength, dtype=self.pages[-1].dtype))
            self.lastindex = 0

        self.pages[-1][self.lastindex] = value
        self.lastindex += 1
        self.length += 1

    def finalize(self):
        return numpy.concatenate(self.pages)[:self.length]

    def __getitem__(self, index):
        if index < 0 or index >= self.length:
            raise IndexError("index {0} out of bounds for FillableMemory".format(index))
        for page in self.pages:
            if index >= page.shape[0]:
                index -= page.shape[0]
            else:
                return page[index]
        assert False, "index reduced to {0} after {1} for length {2}".format(index, sum(x.shape[0] for x in self.pages), self.length)

    def __setitem__(self, index, value):
        if index < 0 or index >= self.length:
            raise IndexError("index {0} out of bounds for FillableMemory".format(index))
        for page in self.pages:
            if index >= page.shape[0]:
                index -= page.shape[0]
            else:
                page[index] = value
        assert False, "index reduced to {0} after {1} for length {2}".format(index, sum(x.shape[0] for x in self.pages), self.length)

    class Iterator(object):
        def __init__(self, pages, length):
            self.pages = pages
            self.countdown = length
            self.pageindex = 0
            self.index = 0

        def __next__(self):
            if self.countdown == 0:
                raise StopIteration
            self.countdown -= 1

            page = self.pages[self.pageindex]
            if self.index >= page.shape[0]:
                self.pageindex += 1
                self.index = 0
                page = self.pages[self.pageindex]

            out = page[self.index]
            self.index += 1
            return out

        next = __next__

    def __iter__(self):
        return self.Iterator(self.pages, self.length)
