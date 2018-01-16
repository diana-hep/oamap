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

import numpy

import oamap.proxy

if sys.version_info[0] > 2:
    basestring = str

# array cache, so that arrays are only loaded once (might be an expensive network operation)
class Cache(object):
    def __init__(self, cachelen):
        self.arraylist = [None] * cachelen
        self.ptr = numpy.zeros(cachelen, dtype=numpy.intp)   # these arrays are only set and used in compiled code
        self.len = numpy.zeros(cachelen, dtype=numpy.intp)

    def entercompiled(self):
        for i, x in enumerate(self.arraylist):
            if x is None:
                self.ptr[i] = 0
                self.len[i] = 0
            else:
                if not isinstance(x, numpy.ndarray):
                    raise TypeError("all arrays must have numpy.ndarray type for use in compiled code")
                self.ptr[i] = x.ctypes.data
                self.len[i] = x.shape[0]
        return self.ptr.ctypes.data, self.len.ctypes.data

# base class of all runtime-object generators (one for each type)
class Generator(object):
    def _getarrays(self, arrays, cache, name2idx, dtypes, dims):
        if hasattr(arrays, "getall"):
            out = arrays.getall(*name2idx)
        else:
            out = dict((name, arrays[name]) for name in name2idx)

        for name, array in out.items():
            if not isinstance(array, numpy.ndarray) or array.dtype != dtypes[name]:
                array = numpy.array(array, dtype=dtypes[name])
            if array.shape[1:] != dims[name]:
                raise TypeError("arrays[{0}].shape[1:] is {1} but expected {2}".format(repr(name), array.shape[1:], dims[name]))

            cache.arraylist[name2idx[name]] = array

    def __init__(self, name, derivedname, schema):
        self.name = name
        self.derivedname = derivedname
        self.schema = schema

    def __call__(self, arrays):
        return self._generate(arrays, 0, Cache(self._cachelen))

# mix-in for all generators of nullable types
class Masked(object):
    maskdtype = numpy.dtype(numpy.int32)
    maskedvalue = -1

    def __init__(self, mask, maskidx):
        self.mask = mask
        self.maskidx = maskidx

    def _generate(self, arrays, index, cache):
        mask = cache.arraylist[self.maskidx]
        if mask is None:
            self._getarrays(arrays, cache, {self.mask: self.maskidx}, {self.mask: self.maskdtype}, {self.mask: ()})
            mask = cache.arraylist[self.maskidx]

        value = mask[index]
        if value == self.maskedvalue:
            return None
        else:
            # otherwise, the value is the index for compactified data
            return self.__class__.__bases__[1]._generate(self, arrays, value, cache)

################################################################ Primitives

class PrimitiveGenerator(Generator):
    def __init__(self, data, dataidx, dtype, dims, name, derivedname, schema):
        self.data = data
        self.dataidx = dataidx
        self.dtype = dtype
        self.dims = dims
        Generator.__init__(self, name, derivedname, schema)

    def _generate(self, arrays, index, cache):
        data = cache.arraylist[self.dataidx]
        if data is None:
            self._getarrays(arrays, cache, {self.data: self.dataidx}, {self.data: self.dtype}, {self.data: self.dims})
            data = cache.arraylist[self.dataidx]
        
        return data[index]

class MaskedPrimitiveGenerator(Masked, PrimitiveGenerator):
    def __init__(self, mask, maskidx, data, dataidx, dtype, dims, name, derivedname, schema):
        Masked.__init__(self, mask, maskidx)
        PrimitiveGenerator.__init__(self, data, dataidx, dtype, dims, name, derivedname, schema)

################################################################ Lists

class ListGenerator(Generator):
    posdtype = numpy.dtype(numpy.int32)

    def __init__(self, starts, startsidx, stops, stopsidx, content, name, derivedname, schema):
        self.starts = starts
        self.startsidx = startsidx
        self.stops = stops
        self.stopsidx = stopsidx
        self.content = content
        Generator.__init__(self, name, derivedname, schema)

    def _generate(self, arrays, index, cache):
        starts = cache.arraylist[self.startsidx]
        stops = cache.arraylist[self.stopsidx]
        if starts is None or stops is None:
            self._getarrays(arrays, cache, {self.starts: self.startsidx, self.stops: self.stopsidx}, {self.starts: self.posdtype, self.stops: self.posdtype}, {self.starts: (), self.stops: ()})
            starts = cache.arraylist[self.startsidx]
            stops = cache.arraylist[self.stopsidx]

        return oamap.proxy.ListProxy(self, arrays, cache, starts[index], 1, stops[index] - starts[index])

class MaskedListGenerator(Masked, ListGenerator):
    def __init__(self, mask, maskidx, starts, startsidx, stops, stopsidx, content, name, derivedname, schema):
        Masked.__init__(self, mask, maskidx)
        ListGenerator.__init__(self, starts, startsidx, stops, stopsidx, content, name, derivedname, schema)

################################################################ Unions

class UnionGenerator(Generator):
    tagdtype = numpy.dtype(numpy.int8)
    offsetdtype = numpy.dtype(numpy.int32)

    def __init__(self, tags, tagsidx, offsets, offsetsidx, possibilities, name, derivedname, schema):
        self.tags = tags
        self.tagsidx = tagsidx
        self.offsets = offsets
        self.offsetsidx = offsetsidx
        self.possibilities = possibilities
        Generator.__init__(self, name, derivedname, schema)

    def _generate(self, arrays, index, cache):
        tags = cache.arraylist[self.tagsidx]
        offsets = cache.arraylist[self.offsetsidx]
        if tags is None or offsets is None:
            self._getarrays(arrays, cache, {self.tags: self.tagsidx, self.offsets: self.offsetsidx}, {self.tags: self.tagdtype, self.offsets: self.offsetdtype}, {self.tags: (), self.offsets: ()})
            tags = cache.arraylist[self.tagsidx]
            offsets = cache.arraylist[self.offsetsidx]

        return self.possibilities[tags[index]]._generate(arrays, offsets[index], cache)

class MaskedUnionGenerator(Masked, UnionGenerator):
    def __init__(self, mask, maskidx, tags, tagsidx, offsets, offsetsidx, possibilities, name, derivedname, schema):
        Masked.__init__(self, mask, maskidx)
        UnionGenerator.__init__(self, tags, tagsidx, offsets, offsetsidx, possibilities, name, derivedname, schema)

################################################################ Records

class RecordGenerator(Generator):
    def __init__(self, fields, name, derivedname, schema):
        self.fields = fields
        Generator.__init__(self, name, derivedname, schema)

    def _generate(self, arrays, index, cache):
        return oamap.proxy.RecordProxy(self, arrays, cache, index)

class MaskedRecordGenerator(Masked, RecordGenerator):
    def __init__(self, mask, maskidx, fields, name, derivedname, schema):
        Masked.__init__(self, mask, maskidx)
        RecordGenerator.__init__(self, fields, name, derivedname, schema)

################################################################ Tuples

class TupleGenerator(Generator):
    def __init__(self, types, name, derivedname, schema):
        self.types = types
        Generator.__init__(self, name, derivedname, schema)

    def _generate(self, arrays, index, cache):
        return oamap.proxy.TupleProxy(self, arrays, cache, index)

class MaskedTupleGenerator(Masked, TupleGenerator):
    def __init__(self, mask, maskidx, types, name, derivedname, schema):
        Masked.__init__(self, mask, maskidx)
        TupleGenerator.__init__(self, types, name, derivedname, schema)

################################################################ Pointers

class PointerGenerator(Generator):
    posdtype = numpy.dtype(numpy.int32)

    def __init__(self, positions, positionsidx, target, name, derivedname, schema):
        self.positions = positions
        self.positionsidx = positionsidx
        self.target = target
        Generator.__init__(self, name, derivedname, schema)

    def _generate(self, arrays, index, cache):
        positions = cache.arraylist[self.positionsidx]
        if positions is None:
            self._getarrays(arrays, cache, {self.positions: self.positionsidx}, {self.positions: self.posdtype}, {self.positions: ()})
            positions = cache.arraylist[self.positionsidx]

        return self.target._generate(arrays, positions[index], cache)

class MaskedPointerGenerator(Masked, PointerGenerator):
    def __init__(self, mask, maskidx, positions, positionsidx, target, name, derivedname, schema):
        Masked.__init__(self, mask, maskidx)
        PointerGenerator.__init__(self, positions, positionsidx, target, name, derivedname, schema)

################################################################ for extensions: domain-specific and user

class ExtendedGenerator(Generator):
    # extensions *must* override pattern, _generate, and degenerate, *may* override matches
    pattern = None

    # default implementation: generate a given type of proxy
    proxyclass = None
    def _generate(self, arrays, index, cache):
        return self.proxyclass(self, arrays, cache, index)

    # default implementation: do nothing; generic type is the same as extended type
    def degenerate(self, obj):
        return obj

    def __init__(self, genericclass, *args):
        self.generic = genericclass(*args)

    @property
    def name(self):
        return self.generic.name

    @property
    def derivedname(self):
        return self.generic.derivedname

    @property
    def schema(self):
        return self.generic.schema

    @classmethod
    def matches(cls, schema):
        def recurse(pattern, schema):
            if isinstance(pattern, basestring):
                return schema["type"] == "primitive" and schema["dtype"] == pattern
            else:
                assert isinstance(pattern, dict) and "type" in pattern

                if "nullable" in pattern and pattern["nullable"] != schema["nullable"]:
                    return False
                if "name" in pattern and pattern["name"] != schema["name"]:
                    return False
                if "label" in pattern and pattern["label"] != schema["label"]:
                    return False

                if pattern["type"] == "primitive":
                    if "dtype" in pattern and pattern["dtype"] != schema["dtype"]:
                        return False
                    if "dims" in pattern and pattern["dims"] != schema["dims"]:
                        return False
                    return True

                elif pattern["type"] == "list":
                    if "content" in pattern:
                        return recurse(pattern["content"], schema["content"])
                    return True

                elif pattern["type"] == "union":
                    if "possibilities" in pattern:
                        return len(pattern["possibilities"]) == len(schema["possibilities"]) and all(recurse(x, y) for x, y in zip(pattern["possibilities"], schema["possibilities"]))
                    return True

                elif pattern["type"] == "record":
                    if "fields" in pattern:
                        if isinstance(pattern["fields"], dict):
                            return set(pattern["fields"].keys()).issubset(set(n for n, x in schema["fields"])) and all(recurse(px, [sx for sn, sx in schema["fields"] if pn == sn][0]) for pn, px in pattern["fields"].items())
                        else:
                            return len(pattern["fields"]) == len(schema["fields"]) and all(pn == sn and recurse(px, sx) for (pn, px), (sn, sx) in zip(pattern["fields"], schema["fields"]))
                    return True

                elif pattern["type"] == "tuple":
                    if "types" in pattern:
                        return len(pattern["types"]) == len(schema["types"]) and all(recurse(x, y) for x, y in zip(pattern["types"], schema["types"]))
                    return True

                elif pattern["type"] == "pointer":
                    if "target" in pattern:
                        return recurse(pattern["target"], schema["target"])
                    return True

                else:
                    assert pattern["type"] in ("primitive", "list", "union", "record", "tuple", "pointer")

        return recurse(cls.pattern, schema.tojson(explicit=True))
        
################################################################ for assigning unique strings to types (used to distinguish Numba types)

def _firstindex(generator):
    if isinstance(generator, Masked):
        return generator.maskidx
    elif isinstance(generator, PrimitiveGenerator):
        return generator.dataidx
    elif isinstance(generator, ListGenerator):
        return generator.startsidx
    elif isinstance(generator, UnionGenerator):
        return generator.tagsidx
    elif isinstance(generator, RecordGenerator):
        for g in generator.fields.values():
            return _firstindex(g)
        return -1
    elif isinstance(generator, TupleGenerator):
        for g in generator.types:
            return _firstindex(g)
        return -1
    elif isinstance(generator, PointerGenerator):
        return generator.positionsidx
    else:
        raise AssertionError("unrecognized generator type: {0}".format(generator))

def _uniquestr(generator, memo):
    if id(generator) not in memo:
        memo.add(id(generator))
        givenname = "nil" if generator.name is None else repr(generator.name)

        if isinstance(generator, PrimitiveGenerator):
            generator._uniquestr = "(P {0} {1} ({2}) {3} {4})".format(givenname, repr(str(generator.dtype)), " ".join(map(repr, generator.dims)), generator.dataidx, repr(generator.data))

        elif isinstance(generator, MaskedPrimitiveGenerator):
            generator._uniquestr = "(P {0} {1} ({2}) {3} {4} {5} {6})".format(givenname, repr(str(generator.dtype)), " ".join(map(repr, generator.dims)), generator.maskidx, repr(generator.mask), generator.dataidx, repr(generator.data))

        elif isinstance(generator, ListGenerator):
            _uniquestr(generator.content, memo)
            generator._uniquestr = "(L {0} {1} {2} {3} {4} {5})".format(givenname, generator.startsidx, repr(generator.starts), generator.stopsidx, repr(generator.stops), generator.content._uniquestr)

        elif isinstance(generator, MaskedListGenerator):
            _uniquestr(generator.content, memo)
            generator._uniquestr = "(L {0} {1} {2} {3} {4} {5})".format(givenname, generator.maskidx, repr(generator.mask), generator.startsidx, repr(generator.starts), generator.stopsidx, repr(generator.stops), generator.content._uniquestr)

        elif isinstance(generator, UnionGenerator):
            for t in generator.possibilities:
                _uniquestr(t, memo)
            generator._uniquestr = "(U {0} {1} {2} {3} {4} ({5}))".format(givenname, generator.tagsidx, repr(generator.tags), generator.offsetsidx, repr(generator.offsets), " ".join(x._uniquestr for x in generator.possibilities))

        elif isinstance(generator, MaskedUnionGenerator):
            for t in generator.possibilities:
                _uniquestr(t, memo)
            generator._uniquestr = "(U {0} {1} {2} {3} {4} {5} {6} ({7}))".format(givenname, generator.maskidx, repr(generator.mask), generator.tagsidx, repr(generator.tags), generator.offsetsidx, repr(generator.offsets), " ".join(x._uniquestr for x in generator.possibilities))

        elif isinstance(generator, RecordGenerator):
            for t in generator.fields.values():
                _uniquestr(t, memo)
            generator._uniquestr = "(R {0} ({1}))".format(givenname, " ".join("({0} . {1})".format(repr(n), t._uniquestr) for n, t in generator.fields.items()))

        elif isinstance(generator, MaskedRecordGenerator):
            for t in generator.fields.values():
                _uniquestr(t, memo)
            generator._uniquestr = "(R {0} {1} {2} ({3}))".format(givenname, generator.maskidx, repr(generator.mask), " ".join("({0} . {1})".format(repr(n), t._uniquestr) for n, t in generator.fields.items()))

        elif isinstance(generator, TupleGenerator):
            for t in generator.types:
                _uniquestr(t, memo)
            generator._uniquestr = "(T {0} ({1}))".format(givenname, " ".join(t._uniquestr for t in generator.types))

        elif isinstance(generator, MaskedTupleGenerator):
            for t in generator.types:
                _uniquestr(t, memo)
            generator._uniquestr = "(T {0} {1} {2} ({3}))".format(givenname, generator.maskidx, repr(generator.mask), " ".join(t._uniquestr for t in generator.types))

        elif isinstance(generator, PointerGenerator):
            _uniquestr(generator.target, memo)
            if generator._internal:
                target = _firstindex(generator.target)
            else:
                target = generator.target._uniquestr
            generator._uniquestr = "(X {0} {1} {2} {3})".format(givenname, generator.positionsidx, repr(generator.positions), target)

        elif isinstance(generator, MaskedPointerGenerator):
            _uniquestr(generator.target, memo)
            if generator._internal:
                target = _firstindex(generator.target)
            else:
                target = generator.target._uniquestr
            generator._uniquestr = "(X {0} {1} {2} {3} {4} {5})".format(givenname, generator.maskidx, repr(generator.mask), generator.positionsidx, repr(generator.positions), target)

        elif isinstance(generator, ExtendedGenerator):
            _uniquestr(generator.generic, memo)
            generator._uniquestr = "({0} {1})".format(generator.__class__.__name__, generator.generic._uniquestr)

        else:
            raise AssertionError("unrecognized generator type: {0}".format(generator))
