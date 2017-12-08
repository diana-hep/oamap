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

class PrimitiveType(type):
    def __new__(cls, arrays, index):
        try:
            return arrays[cls.data][index]

        except KeyError as err:
            raise KeyError("could not find primitive data {0}".format(repr(cls.data)))

        except IndexError as err:
            raise IndexError(err.message + " when instantiating primitive from data {0}".format(repr(cls.data)))

class MaskedPrimitiveType(type):
    def __new__(cls, arrays, index):
        try:
            if arrays[cls.mask][index]:
                return None
            else:
                return arrays[cls.data][index]

        except KeyError as err:
            raise KeyError("could not find primitive data {0} and mask {1}".format(repr(cls.data), repr(cls.mask)))

        except IndexError as err:
            raise IndexError(err.message + " when instantiating primitive from data {0} and mask {1}".format(repr(cls.data), repr(cls.mask)))

class ListProxy(object):
    def __init__(self, contents, arrays, start, stop):
        self._contents = contents
        self._arrays = arrays
        self._start = start
        self._stop = stop

    def __getitem__(self, index):
        return self._contents(self._arrays, self._start + index)

    def __len__(self):
        return self._stop - self._start

class ListType(type):
    def __new__(cls, arrays, index):
        return ListProxy(cls.contents, arrays, arrays[cls.starts][index], arrays[cls.stops][index])
