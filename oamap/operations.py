#!/usr/bin/env python

# Copyright (c) 2017, DIANA-HEP
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# 
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# 
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sys
import numbers

import numpy

import oamap.schema
import oamap.generator
import oamap.proxy

if sys.version_info[0] < 3:
    range = xrange

################################################################ utilities

def _maybecompile(numba):
    if numba is not None and numba is not False:
        if numba is True:
            numbaopts = {}
        else:
            numbaopts = numba
        import numba as nb
        return lambda fcn: fcn if isinstance(fcn, nb.dispatcher.Dispatcher) else nb.jit(**numbaopts)(fcn)
    else:
        return lambda fcn: fcn

################################################################ project

################################################################ flatten

################################################################ filter

################################################################ quick test

# from oamap.schema import *

# dataset = List("int").fromdata(range(10))

# one = List(Record(dict(x=List("int"), y=List("double")))).fromdata([{"x": [1, 2, 3], "y": [1.1, 2.2]}, {"x": [], "y": []}, {"x": [4, 5], "y": [3.3]}])
# two = List(Record(dict(x=List("int"), y=List("double")))).fromdata([{"x": [1, 2, 3], "y": [1.1, 2.2]}, {"x": [], "y": []}, {"x": [4, 5], "y": [3.3]}])
