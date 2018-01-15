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

import numpy

import oamap.generator

class PackedSource(object):
    roles = ()

    def __init__(self, source, isapplicable, topackedname):
        self.source = source
        self.isapplicable = isapplicable
        self.topackedname = topackedname

    def getall(self, *names):
        packednames = []
        unpackednames = []
        toget = []
        for name in names:
            if self.isapplicable(name):
                packednames.append(self.topackedname(name))
                unpackednames.append(name)
            else:
                toget.append(name)

        for packedname in packednames:
            if packedname not in toget:
                toget.append(packedname)

        if hasattr(self.source, "getall"):
            out = self.source.getall(*toget)
        else:
            out = dict((n, self.source[n]) for n in toget)

        for packedname, unpackedname in zip(packednames, unpackednames):
            array = out[packedname]
            out[unpackedname] = self.unpack(unpackedname, array, out)

        for packedname in packednames:
            del out[packedname]

        return out

    def putall(self, **arrays):
        out = {}
        for name, array in arrays.items():
            if self.isapplicable(name):
                packed = self.pack(name, array, arrays)
                if packed is not None:
                    out[self.topackedname(name)] = packed
            else:
                out[name] = array

        if hasattr(self.source, "putall"):
            self.source.putall(**out)
        else:
            for n, x in out.items():
                self.source[n] = x

    def unpack(self, unpackedname, array, arrays):
        return array

    def pack(self, unpackedname, array, arrays):
        return array

################################################################ BitPackMasks

class BitPackMasks(PackedSource):
    def __init__(self, source, isapplicable=lambda name: name.endswith("-M"), topackedname=lambda name: name[:-2] + "-m"):
        super(MaskBitPacked, self).__init__(source, isapplicable, topackedname)

    def unpack(self, unpackedname, array, arrays):
        if not isinstance(array, numpy.ndarray):
            array = numpy.array(array, dtype=numpy.dtype(numpy.uint8))
        unmasked = numpy.unpackbits(array).view(numpy.bool_)
        mask = numpy.empty(len(unmasked), dtype=oamap.generator.Masked.maskdtype)
        mask[unmasked] = numpy.arange(unmasked.sum(), dtype=mask.dtype)
        mask[~unmasked] = oamap.generator.Masked.maskedvalue
        return mask

    def pack(self, unpackedname, array, arrays):
        if not isinstance(array, numpy.ndarray):
            array = numpy.array(array, dtype=oamap.generator.Masked.maskdtype)
        return numpy.packbits(array != oamap.generator.Masked.maskedvalue)

################################################################ RunLengthMasks

# TODO: run-length encoding for masks

################################################################ ListsAsCounts

class ListsAsCounts(PackedSource):
    class _UniqueKey(object):
        def __hash__(self):
            return hash(ListsAsCounts._UniqueKey)
        def __eq__(self, other):
            return self is other
    _uniquekey = _UniqueKey()

    def __init__(self, source, isstarts=lambda name: name.endswith("-B"), isstops=lambda name: name.endswith("-E"), topackedname=lambda name: name[:-2] + "-c"):
        super(ListAsCounts, self).__init__(source, lambda name: isstarts(name) or isstops(name), topackedname)
        self.isstarts = isstarts
        self.isstops = isstops

    def fromcounts(self, array):
        offsets = numpy.empty(len(array) + 1, dtype=oamap.generator.ListGenerator.posdtype)
        offsets[0] = 0
        offsets[1:] = numpy.cumsum(counts)
        return offsets[:-1], offsets[1:]

    def unpack(self, unpackedname, array, arrays):
        if self.isstarts(unpackedname):
            if self._uniquekey not in arrays:
                arrays[self._uniquekey] = self.fromcounts(array)
            return arrays[self._uniquekey][0]

        elif isstops(unpackedname):
            if self._uniquekey not in arrays:
                arrays[self._uniquekey] = self.fromcounts(array)
            return arrays[self._uniquekey][1]

    def tocounts(self, starts, stops):
        if not isinstance(starts, numpy.ndarray):
            starts = numpy.array(starts, dtype=oamap.generator.ListGenerator.posdtype)
        if not isinstance(starts, numpy.ndarray):
            stops = numpy.array(stops, dtype=oamap.generator.ListGenerator.posdtype)
        if not starts[0] == 0 or not numpy.array_equal(starts[1:], stops[:-1]):
            raise ValueError("starts and stops cannot be converted to a single counts array")
        return stops - starts

    def pack(self, unpackedname, array, arrays):
        if self.isstarts(unpackedname):
            if self._uniquekey not in arrays:
                stops = None
                for n, a in arrays.items():
                    if self.isstops(n):
                        stops = a
                        break
                if stops is None:
                    raise KeyError("stops not found for starts: {0}".format(repr(unpackedname)))
                arrays[self._uniquekey] = self.tocounts(array, stops)
            return arrays[self._uniquekey]

        elif self.isstops(unpackedname):
            if self._uniquekey not in arrays:
                starts = None
                for n, a in arrays.items():
                    if self.isstarts(n):
                        starts = a
                        break
                if starts is None:
                    raise KeyError("starts not found for stops: {0}".format(repr(unpackedname)))
                arrays[self._uniquekey] = self.tocounts(starts, array)
            return arrays[self._uniquekey]

################################################################ DropUnionOffsets

class DropUnionOffsets(PackedSource):
    def __init__(self, source, isapplicable=lambda name: name.endswith("-O"), topackedname=lambda name: name[:-2] + "-T"):
        super(DropUnionOffsets, self).__init__(source, isapplicable, topackedname)

    def unpack(self, unpackedname, array, arrays):
        if not isinstance(array, numpy.ndarray):
            array = numpy.array(array, dtype=oamap.generator.UnionGenerator.tagdtype)
        offsets = numpy.empty(len(array), dtype=oamap.generator.UnionGenerator.offsetdtype)
        for tag in numpy.unique(array):
            hastag = (array == tag)
            offsets[hastag] = numpy.arange(hastag.sum(), dtype=offsets.dtype)
        return offsets

    def pack(self, unpackedname, array, arrays):
        return None

################################################################ CompressAll

# TODO: apply a named compression algorithm
