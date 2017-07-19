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

import struct

class FillableDisk(object):
    def __init__(self, file, dtype, headersize=246):
        if hasattr(file, "write") and hasattr(file, "seek"):
            self.file = file
        else:
            self.file = open(file, "wb")

        self.dtype = dtype
        self.headersize = headersize
        self.length = 0

        self.file.write("\x93NUMPY")

        if self.headersize < 2**16:
            self.file.write(struct.pack("<bbH", 1, 0, self.headersize))
        elif self.headersize < 2**32:
            self.file.write(struct.pack("<bbI", 2, 0, self.headersize))
        else:
            assert self.headersize < 2**32

        self.file.write(" " * self.headersize)

    def fill(self, value):
        self.file.write(self.dtype.type(value))
        self.length += 1

    def finalize(self):
        header = "{{'descr': '{0}', 'fortran_order': False, 'shape': ({1},), }}".format(self.dtype.str, self.length)
        assert len(header) < self.headersize

        if self.headersize < 2**16:
            self.file.seek(6 + 2 + 2)
        else:
            self.file.seek(6 + 2 + 4)

        self.file.write(header)
        self.file.close()
