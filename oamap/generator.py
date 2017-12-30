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
    @staticmethod
    def _getarray(arrays, name, cache, cacheidx, dtype, dims):
        if cache.arraylist[cacheidx] is None:
            try:
                array = arrays[name]
            except KeyError as err:
                self._fallback(arrays, cache, name, err)
            cache.arraylist[cacheidx] = array
            if dtype is not None and getattr(cache.arraylist[cacheidx], "dtype", dtype) != dtype:
                raise TypeError("arrays[{0}].dtype is {1} but expected {2}".format(repr(name), cache.arraylist[cacheidx].dtype, dtype))
            if dims is not None and getattr(cache.arraylist[cacheidx], "shape", (0,) + dims)[1:] != dims:
                raise TypeError("arrays[{0}].shape[1:] is {1} but expected {2}".format(repr(name), cache.arraylist[cacheidx].shape[1:], dims))
        return cache.arraylist[cacheidx]

    def _fallback(self, arrays, cache, name, err):
        raise err

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

    def __init__(self, mask, maskidx, packmask):
        self.mask = mask
        self.maskidx = maskidx
        self.packmask = packmask

    def _fallback(self, arrays, cache, name, err):
        if name == self.mask:
            try:
                packmask = arrays[self.packmask]
            except KeyError:
                pass
            else:
                # packmask = numpy.packbits(mask != -1)
                if packmask.dtype != numpy.dtype(numpy.uint8):
                    raise TypeError("arrays[{0}].dtype is {1} but expected uint8".format(repr(self.packmask), packmask.dtype))
                if packmask.shape[1:] != ():
                    raise TypeError("arrays[{0}].shape[1:] is {1} but expected ()".format(repr(self.packmask), packmask.shape[1:]))
                unmasked = numpy.unpackbits(packmask).view(numpy.bool_)
                mask = numpy.empty(len(unmasked), dtype=self.maskdtype)
                mask[unmasked] = numpy.arange(unmasked.sum(), dtype=self.maskdtype)
                mask[~unmasked] = self.maskedvalue
                return mask

            raise err

        else:
            return self.__class__.__bases__[1]._fallback(self, arrays, cache, name, err)

    def _generate(self, arrays, index, cache):
        value = self._getarray(arrays, self.mask, cache, self.maskidx, self.maskdtype, ())[index]
        if value == self.maskedvalue:
            return None
        else:
            # otherwise, the value is the index for packed data
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
        return self._getarray(arrays, self.data, cache, self.dataidx, self.dtype, self.dims)[index]

class MaskedPrimitiveGenerator(Masked, PrimitiveGenerator):
    def __init__(self, mask, maskidx, packmask, data, dataidx, dtype, dims, name, derivedname, schema):
        Masked.__init__(self, mask, maskidx, packmask)
        PrimitiveGenerator.__init__(self, data, dataidx, dtype, dims, name, derivedname, schema)

################################################################ Lists

class ListGenerator(Generator):
    dtype = numpy.dtype(numpy.int32)

    def __init__(self, starts, startsidx, stops, stopsidx, counts, content, name, derivedname, schema):
        self.starts = starts
        self.startsidx = startsidx
        self.stops = stops
        self.stopsidx = stopsidx
        self.counts = counts
        self.content = content
        Generator.__init__(self, name, derivedname, schema)

    def _fallback(self, arrays, cache, name, err):
        if name == self.starts:
            raise NotImplementedError
        elif name == self.stops:
            raise NotImplementedError
        else:
            raise err

    def _generate(self, arrays, index, cache):
        starts = self._getarray(arrays, self.starts, cache, self.startsidx, self.dtype, ())
        stops  = self._getarray(arrays, self.stops,  cache, self.stopsidx,  self.dtype, ())
        return oamap.proxy.ListProxy(self, arrays, cache, starts[index], 1, stops[index] - starts[index])

class MaskedListGenerator(Masked, ListGenerator):
    def __init__(self, mask, maskidx, packmask, starts, startsidx, stops, stopsidx, counts, content, name, derivedname, schema):
        Masked.__init__(self, mask, maskidx, packmask)
        ListGenerator.__init__(self, starts, startsidx, stops, stopsidx, counts, content, name, derivedname, schema)

################################################################ Unions

class UnionGenerator(Generator):
    dtype = numpy.dtype(numpy.int32)

    def __init__(self, tags, tagsidx, offsets, offsetsidx, possibilities, name, derivedname, schema):
        self.tags = tags
        self.tagsidx = tagsidx
        self.offsets = offsets
        self.offsetsidx = offsetsidx
        self.possibilities = possibilities
        Generator.__init__(self, name, derivedname, schema)

    def _fallback(self, arrays, cache, name, err):
        if name == self.tags:
            raise err
        else:
            raise NotImplementedError

    def _generate(self, arrays, index, cache):
        tags    = self._getarray(arrays, self.tags,    cache, self.tagsidx,    self.dtype, ())
        offsets = self._getarray(arrays, self.offsets, cache, self.offsetsidx, self.dtype, ())
        return self.possibilities[tags[index]]._generate(arrays, offsets[index], cache)

class MaskedUnionGenerator(Masked, UnionGenerator):
    def __init__(self, mask, maskidx, packmask, tags, tagsidx, offsets, offsetsidx, possibilities, name, derivedname, schema):
        Masked.__init__(self, mask, maskidx, packmask)
        UnionGenerator.__init__(self, tags, tagsidx, offsets, offsetsidx, possibilities, name, derivedname, schema)

################################################################ Records

class RecordGenerator(Generator):
    def __init__(self, fields, name, derivedname, schema):
        self.fields = fields
        Generator.__init__(self, name, derivedname, schema)

    def _generate(self, arrays, index, cache):
        return oamap.proxy.RecordProxy(self, arrays, cache, index)

class MaskedRecordGenerator(Masked, RecordGenerator):
    def __init__(self, mask, maskidx, packmask, fields, name, derivedname, schema):
        Masked.__init__(self, mask, maskidx, packmask)
        RecordGenerator.__init__(self, fields, name, derivedname, schema)

################################################################ Tuples

class TupleGenerator(Generator):
    def __init__(self, types, name, derivedname, schema):
        self.types = types
        Generator.__init__(self, name, derivedname, schema)

    def _generate(self, arrays, index, cache):
        return oamap.proxy.TupleProxy(self, arrays, cache, index)

class MaskedTupleGenerator(Masked, TupleGenerator):
    def __init__(self, mask, maskidx, packmask, types, name, derivedname, schema):
        Masked.__init__(self, mask, maskidx, packmask)
        TupleGenerator.__init__(self, types, name, derivedname, schema)

################################################################ Pointers

class PointerGenerator(Generator):
    dtype = numpy.dtype(numpy.int32)

    def __init__(self, positions, positionsidx, target, name, derivedname, schema):
        self.positions = positions
        self.positionsidx = positionsidx
        self.target = target
        Generator.__init__(self, name, derivedname, schema)

    def _generate(self, arrays, index, cache):
        positions = self._getarray(arrays, self.positions, cache, self.positionsidx, self.dtype, ())
        return self.target._generate(arrays, positions[index], cache)

class MaskedPointerGenerator(Masked, PointerGenerator):
    def __init__(self, mask, maskidx, packmask, positions, positionsidx, target, name, derivedname, schema):
        Masked.__init__(self, mask, maskidx, packmask)
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
            generator._uniquestr = "(P {0} {1} ({2}) {3} {4} {5} {6} {7})".format(givenname, repr(str(generator.dtype)), " ".join(map(repr, generator.dims)), generator.maskidx, repr(generator.mask), repr(generator.packmask), generator.dataidx, repr(generator.data))

        elif isinstance(generator, ListGenerator):
            _uniquestr(generator.content, memo)
            generator._uniquestr = "(L {0} {1} {2} {3} {4} {5} {6})".format(givenname, generator.startsidx, repr(generator.starts), generator.stopsidx, repr(generator.stops), repr(generator.counts), generator.content._uniquestr)

        elif isinstance(generator, MaskedListGenerator):
            _uniquestr(generator.content, memo)
            generator._uniquestr = "(L {0} {1} {2} {3} {4} {5} {6} {7})".format(givenname, generator.maskidx, repr(generator.mask), repr(generator.packmask), generator.startsidx, repr(generator.starts), generator.stopsidx, repr(generator.stops), repr(generator.counts), generator.content._uniquestr)

        elif isinstance(generator, UnionGenerator):
            for t in generator.possibilities:
                _uniquestr(t, memo)
            generator._uniquestr = "(U {0} {1} {2} {3} {4} ({5}))".format(givenname, generator.tagsidx, repr(generator.tags), generator.offsetsidx, repr(generator.offsets), " ".join(x._uniquestr for x in generator.possibilities))

        elif isinstance(generator, MaskedUnionGenerator):
            for t in generator.possibilities:
                _uniquestr(t, memo)
            generator._uniquestr = "(U {0} {1} {2} {3} {4} {5} {6} {7} ({8}))".format(givenname, generator.maskidx, repr(generator.mask), repr(generator.packmask), generator.tagsidx, repr(generator.tags), generator.offsetsidx, repr(generator.offsets), " ".join(x._uniquestr for x in generator.possibilities))

        elif isinstance(generator, RecordGenerator):
            for t in generator.fields.values():
                _uniquestr(t, memo)
            generator._uniquestr = "(R {0} ({1}))".format(givenname, " ".join("({0} . {1})".format(repr(n), t._uniquestr) for n, t in generator.fields.items()))

        elif isinstance(generator, MaskedRecordGenerator):
            for t in generator.fields.values():
                _uniquestr(t, memo)
            generator._uniquestr = "(R {0} {1} {2} {3} ({4}))".format(givenname, generator.maskidx, repr(generator.mask), repr(generator.packmask), " ".join("({0} . {1})".format(repr(n), t._uniquestr) for n, t in generator.fields.items()))

        elif isinstance(generator, TupleGenerator):
            for t in generator.types:
                _uniquestr(t, memo)
            generator._uniquestr = "(T {0} ({1}))".format(givenname, " ".join(t._uniquestr for t in generator.types))

        elif isinstance(generator, MaskedTupleGenerator):
            for t in generator.types:
                _uniquestr(t, memo)
            generator._uniquestr = "(T {0} {1} {2} {3} ({4}))".format(givenname, generator.maskidx, repr(generator.mask), repr(generator.packmask), " ".join(t._uniquestr for t in generator.types))

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
            generator._uniquestr = "(X {0} {1} {2} {3} {4} {5} {6})".format(givenname, generator.maskidx, repr(generator.mask), repr(generator.packmask), generator.positionsidx, repr(generator.positions), target)

        elif isinstance(generator, ExtendedGenerator):
            _uniquestr(generator.generic, memo)
            generator._uniquestr = "({0} {1})".format(generator.__class__.__name__, generator.generic._uniquestr)

        else:
            raise AssertionError("unrecognized generator type: {0}".format(generator))
