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

import re
import sys
import numbers
from types import MethodType
try:
    from collections import OrderedDict
except ImportError:
    # simple OrderedDict implementation for Python 2.6
    class OrderedDict(dict):
        def __init__(self, items=(), **kwds):
            items = list(items)
            self._order = [k for k, v in items] + [k for k, v in kwds.items()]
            super(OrderedDict, self).__init__(items)
        def keys(self):
            return self._order
        def values(self):
            return [self[k] for k in self._order]
        def items(self):
            return [(k, self[k]) for k in self._order]
        def __setitem__(self, name, order):
            if name not in self._order:
                self._order.append(name)
            super(OrderedDict, self).__setitem__(name, value)
        def __delitem__(self, name):
            if name in self._order:
                self._order.remove(name)
            super(OrderedDict, self).__delitem__(name)
        def __repr__(self):
            return "OrderedDict([{0}])".format(", ".join("({0}, {1})".format(repr(k), repr(v)) for k, v in self.items()))

import numpy

from oamap.proxy import PrimitiveType
from oamap.proxy import MaskedPrimitiveType
from oamap.proxy import ListType
from oamap.proxy import MaskedListType

if sys.version_info[0] > 2:
    basestring = str

# The "PLURTP" type system: Primitives, Lists, Unions, Records, Tuples, and Pointers

class Schema(object):
    def __init__(self, *args, **kwds):
        raise TypeError("Kind cannot be instantiated directly")

    @property
    def nullable(self):
        return self._nullable

    @nullable.setter
    def nullable(self, value):
        if value is not True and value is not False:
            raise TypeError("nullable must be True or False, not {0}".format(repr(value)))
        self._nullable = value

    @property
    def mask(self):
        return self._mask

    @mask.setter
    def mask(self, value):
        if not (value is None or isinstance(value, basestring)):
            raise TypeError("mask must be None or an array name (string), not {0}".format(repr(value)))
        self._mask = value

    def _labels(self):
        labels = []
        self._collect(set(), labels)
        return labels
        
    def _label(self, labels):
        for index, label in enumerate(labels):
            if label is self:
                return "#{0}".format(index)
        return None

################################################################ Primitives can be any Numpy type

class Primitive(Schema):
    def __init__(self, dtype, dims=(), nullable=False, data=None, mask=None):
        self.dtype = dtype
        self.dims = dims
        self.nullable = nullable
        self.data = data
        self.mask = mask

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
            raise TypeError("dims must be a tuple of non-negative integers, not {0}".format(repr(value)))
        self._dims = value

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        if not (value is None or isinstance(value, basestring)):
            raise TypeError("data must be None or an array name (string), not {0}".format(repr(value)))
        self._data = value

    def __repr__(self, labels=None, shown=None):
        if labels is None:
            labels = self._labels()
            shown = set()
        label = self._label(labels)

        if label is None or id(self) not in shown:
            shown.add(id(self))

            args = [repr(self._dtype)]
            if self._dims != ():
                args.append("dims=" + repr(self._dims))
            if self._nullable is not False:
                args.append("nullable=" + repr(self._nullable))
            if self._data is not None:
                args.append("data=" + repr(self._data))
            if self._mask is not None:
                args.append("mask=" + repr(self._mask))

            if label is None:
                return "Primitive(" + ", ".join(args) + ")"
            else:
                return label + ": Primitive(" + ", ".join(args) + ")"

        else:
            return label

    def _collect(self, collection, labels):
        if id(self) not in collection:
            collection.add(id(self))
        else:
            labels.append(self)

    def __call__(self, prefix="object", delimiter="-"):
        if self._data is None:
            data = prefix
        else:
            data = self._data

        if not self._nullable:
            return type("PrimitiveType", (PrimitiveType,), {"data": data})

        else:
            if self._mask is None:
                mask = prefix + delimiter + "M"
            else:
                mask = self._mask

            return type("MaskedPrimitiveType", (MaskedPrimitiveType,), {"data": data, "mask": mask})

################################################################ Lists may have arbitrary length

class List(Schema):
    def __init__(self, contents, nullable=False, starts=None, stops=None, mask=None):
        self.contents = contents
        self.nullable = nullable
        self.starts = starts
        self.stops = stops
        self.mask = mask

    @property
    def contents(self):
        return self._contents

    @contents.setter
    def contents(self, value):
        if not isinstance(value, Schema):
            raise TypeError("contents must be a Schema, not {0}".format(repr(value)))
        self._contents = value

    @property
    def starts(self):
        return self._starts

    @starts.setter
    def starts(self, value):
        if not (value is None or isinstance(value, basestring)):
            raise TypeError("starts must be None or an array name (string), not {0}".format(repr(value)))
        self._starts = value

    @property
    def stops(self):
        return self._stops

    @stops.setter
    def stops(self, value):
        if not (value is None or isinstance(value, basestring)):
            raise TypeError("stops must be None or an array name (string), not {0}".format(repr(value)))
        self._stops = value

    def __repr__(self, labels=None, shown=None):
        if labels is None:
            labels = self._labels()
            shown = set()
        label = self._label(labels)

        if label is None or id(self) not in shown:
            shown.add(id(self))

            args = [self._contents.__repr__(labels, shown)]
            if self._nullable is not False:
                args.append("nullable=" + repr(self._nullable))
            if self._starts is not None:
                args.append("starts=" + repr(self._starts))
            if self._stops is not None:
                args.append("stops=" + repr(self._stops))
            if self._mask is not None:
                args.append("mask=" + repr(self._mask))

            if label is None:
                return "List(" + ", ".join(args) + ")"
            else:
                return label + ": List(" + ", ".join(args) + ")"

        else:
            return label

    def _collect(self, collection, labels):
        if id(self) not in collection:
            collection.add(id(self))
            self._contents._collect(collection, labels)
        else:
            labels.append(self)

    def __call__(self, prefix="object", delimiter="-"):
        if self._starts is None:
            starts = prefix + delimiter + "B"
        else:
            starts = self._starts

        if self._stops is None:
            stops = prefix + delimiter + "E"
        else:
            stops = self._stops

        if not self._nullable:
            return type("ListType", (ListType,), {"contents": self._contents(prefix + delimiter + "C"), "starts": starts, "stops": stops})

        else:
            if self._mask is None:
                mask = prefix + delimiter + "M"
            else:
                mask = self._mask

            return type("MaskedListType", (MaskedListType,), {"contents": self._contents(prefix + delimiter + "C"), "starts": starts, "stops": stops, "mask": mask})

################################################################ Unions may be one of several types

class Union(Schema):
    def __init__(self, possibilities, nullable=False, tags=None, offsets=None, mask=None):
        self.possibilities = possibilities
        self.nullable = nullable
        self.tags = tags
        self.offsets = offsets
        self.mask = mask

    @property
    def possibilities(self):
        return tuple(self._possibilities)

    @possibilities.setter
    def possibilities(self, value):
        self._extend(value, [])

    def _extend(self, possibilities, start):
        trial = []
        try:
            for i, x in enumerate(value):
                assert isinstance(x, Schema), "possibilities must be an iterable of Schemas; item at {0} is {1}".format(i, x)
                trial.append(x)
        except TypeError:
            raise TypeError("possibilities must be an iterable of Schemas, not {0}".format(repr(value)))
        except AssertionError as err:
            raise TypeError(err.message)
        self._possibilities = start + trial

    def append(self, possibility):
        if not isinstance(possibility, Schema):
            raise TypeError("possibilities must be Schemas, not {0}".format(repr(possibility)))
        self._possibilities.append(possibility)

    def insert(self, index, possibility):
        if not isinstance(possibility, Schema):
            raise TypeError("possibilities must be Schemas, not {0}".format(repr(possibility)))
        self._possibilities.insert(index, possibility)

    def extend(self, possibilities):
        self._extend(possibilities, self._possibilities)

    def __getitem__(self, index):
        return self._possibilities[index]

    def __setitem__(self, index, value):
        if not isinstance(value, Schema):
            raise TypeError("possibilities must be Schemas, not {0}".format(repr(value)))
        self._possibilities[index] = value

    def __repr__(self, labels=None, shown=None):
        if labels is None:
            labels = self._labels()
            shown = set()
        label = self._label(labels)

        if label is None or id(self) not in shown:
            shown.add(id(self))

            args = ["[" + ", ".join(x.__repr__(labels, shown) for x in self._possibilities) + "]"]
            if self._nullable is not False:
                args.append("nullable=" + repr(self._nullable))
            if self._tags is not None:
                args.append("tags=" + repr(self._tags))
            if self._offsets is not None:
                args.append("offsets=" + repr(self._offsets))
            if self._mask is not None:
                args.append("mask=" + repr(self._mask))

            if label is None:
                return "Union(" + ", ".join(args) + ")"
            else:
                return label + ": Union(" + ", ".join(args) + ")"

        else:
            return label

    def _collect(self, collection, labels):
        if id(self) not in collection:
            collection.add(id(self))
            for possibility in self._possibilities:
                possibility._collect(collection, labels)
        else:
            labels.append(self)

    def __call__(self, prefix="object", delimiter="-"):
        if self._tags is None:
            tags = prefix + delimiter + "T"
        else:
            tags = self._tags

        if self._offsets is None:
            offsets = prefix + delimiter + "O"
        else:
            offsets = self._offsets

        if not self._nullable:
            return type("UnionType", (UnionType,), {"possibilities": [x(prefix + delimiter + "U") for x in self._possibilities], "tags": tags, "offsets": offsets})

        else:
            if self._mask is None:
                mask = prefix + delimiter + "M"
            else:
                mask = self._mask

            return type("UnionType", (UnionType,), {"possibilities": [x(prefix + delimiter + "U") for x in self._possibilities], "tags": tags, "offsets": offsets, "mask": mask})

################################################################ Records contain fields of known types

class Record(Schema):
    def __init__(self, fields, nullable=False, mask=None):
        self.fields = fields
        self.nullable = nullable
        self.mask = mask

    @property
    def fields(self):
        return dict(self._fields)

    @fields.setter
    def fields(self, value):
        self._extend(value, [])

    _identifier = re.compile("[a-zA-Z_][a-zA-Z_0-9]*")

    def _extend(self, fields, start):
        trial = []
        try:
            for n, x in fields.items():
                assert isinstance(n, basestring) and self._identifier.match(n) is not None, "fields must be a dict from identifier strings to Schemas; the key {0} is not an identifier (/{1}/)".format(repr(n), self._identifier.pattern)
                assert isinstance(x, Schema), "fields must be a dict from identifier strings to Schemas; the value at identifier {0} is {1}".format(repr(n), x)
                trial.append((n, x))
        except AttributeError:
            raise TypeError("fields must be a dict from strings to Schemas; {0} is not a dict".format(repr(fields)))
        except AssertionError as err:
            raise TypeError(err.message)
        self._fields = OrderedDict(start + trial)

    def __getitem__(self, index):
        return self._fields[index]

    def __setitem__(self, index, value):
        if not isinstance(value, Schema):
            raise TypeError("field values must be Schemas, not {0}".format(repr(value)))
        self._fields[index] = value

    def __repr__(self, labels=None, shown=None):
        if labels is None:
            labels = self._labels()
            shown = set()
        label = self._label(labels)

        if label is None or id(self) not in shown:
            shown.add(id(self))

            args = ["{" + ", ".join( for n, x in self.HERE) + "}"]



            
################################################################ Tuples are like records but with an order instead of field names


################################################################ Pointers redirect to Lists with absolute addresses

