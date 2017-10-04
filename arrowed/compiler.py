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

import numpy
import numba
from numba.types import *

from arrowed.thirdparty.meta.decompiler.instructions import make_function
from arrowed.thirdparty.meta import dump_python_source

from arrowed.oam import *

################################################################ interface

class Compiled(object):
    def run(self, resolved, args):
        pass

def compile(function, paramtypes, numbaargs={"nopython": True}, debug=False):
    pass

################################################################ functions inserted into code

@numba.njit(int64(numba.optional(int64)))
def nonnegotiable(index):
    if index is None:
        raise TypeError("None found where object required")

@numba.njit(int64(int64[:], int64))
def indexget(start, index):
    return start[index]

@numba.njit(numba.optional(int64)(int64[:], int64[:], int64))
def maybe_indexget(startdata, startmask, index):
    if startmask[index]:
        return None
    else:
        return start[index]

@numba.njit(int64(int64[:], int64[:], int64, int64))
def listget(start, end, outerindex, index):
    offset = start[outerindex]
    size = end[outerindex] - offset
    if index < 0:
        index = size + index
    if index < 0 or index >= size:
        raise IndexError("index out of range")
    return offset + index

@numba.njit(int64(int64[:], int64[:], int64))
def listsize(start, end, index):
    return end[index] - start[index]

@numba.njit(numba.optional(int64)(int64[:], int64[:], int64[:], int64))
def maybe_listsize(startdata, startmask, enddata, index):
    if startmask[index]:
        return None
    else:
        return enddata[index] - startdata[index]


