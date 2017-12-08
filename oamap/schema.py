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

from oamap.types import PrimitiveType
from oamap.types import MaskedPrimitiveType
from oamap.types import ListType
from oamap.types import MaskedListType

if sys.version_info[0] > 2:
    basestring = str

class Schema(object):
    def __init__(self, *args, **kwds):
        raise TypeError("Kind cannot be instantiated directly")

    @property
    def nullable(self):
        return self._nullable

    @nullable.setter
    def nullable(self, value):
        if value is not True and value is not False:
            raise TypeError("nullable must be True or False")
        self._nullable = value

    @property
    def mask(self):
        return self._mask

    @mask.setter
    def mask(self, value):
        if not (value is None or isinstance(value, basestring)):
            raise TypeError("mask must be None or an array name (string)")
        self._mask = value

class Primitive(Schema):
    def __init__(self, dtype, dims=(), nullable=False, data=None, mask=None):
        self.dtype = dtype
        self.dims = dims
        self.nullable = nullable
        self.data = data
        self.mask = mask

    def __repr__(self):
        args = [repr(self.dtype)]
        if self.dims != ():
            args.append("dims=" + repr(self.dims))
        if self.nullable is not False:
            args.append("nullable=" + repr(self.nullable))
        if self.data is not None:
            args.append("data=" + repr(self.data))
        if self.mask is not None:
            args.append("mask=" + repr(self.mask))
        return "Primitive(" + ", ".join(args) + ")"

    def __call__(self, prefix="object", delimiter="-"):
        if self.data is None:
            data = prefix
        else:
            data = self.data

        if not self.nullable:
            return type("PrimitiveType", (PrimitiveType,), {"data": data})

        else:
            if self.mask is None:
                mask = prefix + delimiter + "M"
            else:
                mask = self.mask
            return type("MaskedPrimitiveType", (MaskedPrimitiveType,), {"data": data, "mask": mask})

    @property
    def dtype(self):
        return self._dtype

    @dtype.setter
    def dtype(self, value):
        if not isinstance(value, numpy.dtype):
            value = numpy.dtype(value)
        self._dtype = value

    @property
    def dims(self):
        return self._dims

    @dims.setter
    def dims(self, value):
        if not isinstance(value, tuple) or not all(isinstance(x, numbers.Integral) and x >= 0 for x in value):
            raise TypeError("dims must be a tuple of non-negative integers")
        self._dims = value

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        if not (value is None or isinstance(value, basestring)):
            raise TypeError("data must be None or an array name (string)")
        self._data = value

class List(Schema):
    def __init__(self, contents, nullable=False, starts=None, stops=None, mask=None):
        self.contents = contents
        self.nullable = nullable
        self.starts = starts
        self.stops = stops
        self.mask = mask

    def __repr__(self):
        args = [repr(self.contents)]
        if self.starts is not None:
            args.append("starts=" + repr(self.starts))
        if self.stops is not None:
            args.append("stops=" + repr(self.stops))
        if self.mask is not None:
            args.append("mask=" + repr(self.mask))
        return "List(" + ", ".join(args) + ")"

    def __call__(self, prefix="object", delimiter="-"):
        if self.starts is None:
            starts = prefix + delimiter + "B"
        else:
            starts = self.starts

        if self.stops is None:
            stops = prefix + delimiter + "E"
        else:
            stops = self.stops

        if not self.nullable:
            return type("ListType", (ListType,), {"contents": self.contents(prefix + delimiter + "L"), "starts": starts, "stops": stops})

        else:
            if self.mask is None:
                mask = prefix + delimiter + "M"
            else:
                mask = self.mask

            return type("MaskedListType", (MaskedListType,), {"contents": self.contents(prefix + delimiter + "L"), "starts": starts, "stops": stops, "mask": mask})

    @property
    def contents(self):
        return self._contents

    @contents.setter
    def contents(self, value):
        if not isinstance(value, Schema):
            raise TypeError("contents must be a Schema")
        self._contents = value

    @property
    def starts(self):
        return self._starts

    @starts.setter
    def starts(self, value):
        if not (value is None or isinstance(value, basestring)):
            raise TypeError("starts must be None or an array name (string)")
        self._starts = value

    @property
    def stops(self):
        return self._stops

    @stops.setter
    def stops(self, value):
        if not (value is None or isinstance(value, basestring)):
            raise TypeError("stops must be None or an array name (string)")
        self._stops = value
