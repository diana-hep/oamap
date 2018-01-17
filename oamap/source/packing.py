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

import json
import sys

import numpy

import oamap.generator

if sys.version_info[0] > 2:
    basestring = str

class PackedSource(object):
    def __init__(self, source, suffix):
        self.source = source
        self.suffix = suffix

    def __repr__(self):
        return "{0}({1}{2})".format(self.__class__.__name__, repr(self.source), "".join(", " + repr(x) for x in self._tojsonargs()))

    def getall(self, names, roles):
        if hasattr(self.source, "getall"):
            return self.source.getall(names, roles)
        else:
            return dict((n, self.source[n]) for n in names)

    def putall(self, names2arrays, roles):
        if hasattr(self.source, "putall"):
            self.source.putall(names2arrays, roles)
        else:
            for n, x in names2arrays.items():
                self.source[n] = x

    def copy(self):
        return self.__class__(self.source, self.suffix)

    def anchor(self, source):
        if self.source is None:
            return self.__class__(source, self.suffix)
        else:
            return self.__class__(self.source.anchor(source), self.suffix)

    def __eq__(self, other):
        return self.__class__.__name__ == other.__class__.__name__ and self._tojsonargs() == other._tojsonargs()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((PackedSource, self.__class__.__name__, tuple(self._tojsonargs())))

    def tojsonfile(self, file, *args, **kwds):
        json.dump(self.tojson(), file, *args, **kwds)

    def tojsonstring(self, *args, **kwds):
        return json.dumps(self.tojson(), *args, **kwds)

    def tojson(self):
        out = []
        node = self
        while isinstance(node, PackedSource):
            args = self._tojsonargs()
            if len(args) == 0:
                out.append(self.__class__.__name__)
            else:
                out.append({self.__class__.__name__: args})
            node = node.source
        return out

    @staticmethod
    def fromjsonfile(file, *args, **kwds):
        return PackedSource.fromjson(json.load(file, *args, **kwds))

    @staticmethod
    def fromjsonstring(data, *args, **kwds):
        return PackedSource.fromjson(json.loads(data, *args, **kwds))

    @staticmethod
    def fromjson(data):
        if isinstance(data, list):
            source = None
            for datum in reversed(data):
                if isinstance(datum, basestring):
                    classname = datum
                    args = ()
                elif isinstance(datum, dict) and len(datum) == 1:
                    classname, = datum.keys()
                    args, = datum.values()
                else:
                    raise ValueError("source packings JSON must be a list of strings or {\"classname\": [args]} dicts")
                try:
                    cls = globals()[classname]
                except KeyError:
                    raise ValueError("source packing class {0} not found".format(repr(classname)))
                source = cls(source, *args)
            return source
        else:
            raise ValueError("source packings JSON must be a list of strings or {\"classname\": [args]} dicts")

################################################################ BitPackMasks

class MaskBitPack(PackedSource):
    def __init__(self, source, suffix="-bitpacked"):
        super(MaskBitPack, self).__init__(source, suffix)

    def _tojsonargs(self):
        if self.suffix == "-bitpacked":
            return []
        else:
            return [self.suffix]

    def getall(self, names, roles):
        notmasks = [n for n in names if roles.get(n, None) is not oamap.generator.MASK]
        masks    = [n for n in names if roles.get(n, None) is oamap.generator.MASK]

        out = super(MaskBitPack, self).getall(notmasks, roles)
        for n in masks:
            out[n] = self.unpack(super(MaskBitPack, self).getall([n + self.suffix], {}))
        return out

    def putall(self, names2arrays, roles):
        notmasks = dict((n, x) for n, x in names2arrays.items() if roles.get(n, None) is not oamap.generator.MASK)
        masks    = dict((n, x) for n, x in names2arrays.items() if roles.get(n, None) is oamap.generator.MASK)

        for n, x in masks.items():
            super(MaskBitPack, self).putall({n + self.suffix: pack(x)}, {})
        super(MaskBitPack, self).putall(notmasks, roles)
        
    def unpack(self, array):
        if not isinstance(array, numpy.ndarray):
            array = numpy.array(array, dtype=numpy.dtype(numpy.uint8))
        unmasked = numpy.unpackbits(array).view(numpy.bool_)
        mask = numpy.empty(len(unmasked), dtype=oamap.generator.Masked.maskdtype)
        mask[unmasked] = numpy.arange(unmasked.sum(), dtype=mask.dtype)
        mask[~unmasked] = oamap.generator.Masked.maskedvalue
        return mask

    def pack(self, array):
        if not isinstance(array, numpy.ndarray):
            array = numpy.array(array, dtype=oamap.generator.Masked.maskdtype)
        return numpy.packbits(array != oamap.generator.Masked.maskedvalue)

################################################################ RunLengthMasks

# TODO: run-length encoding for masks

################################################################ ListsAsCounts

class ListCounts(PackedSource):
    def __init__(self, source, suffix="-counts"):
        super(ListCounts, self).__init__(source, suffix)

    def _tojsonargs(self):
        if self.suffix == "-counts":
            return []
        else:
            return [self.suffix]

    def getall(self, names, roles):
        others = [n for n in names if roles.get(n, None) is not oamap.generator.STARTS and roles.get(n, None) is not oamap.generator.STOPS]
        starts = [n for n in names if roles.get(n, None) is oamap.generator.STARTS]
        stops  = [n for n in names if roles.get(n, None) is oamap.generator.STOPS]

        out = super(ListCounts, self).getall(others, roles)
        if len(starts) == len(stops) == 0:
            pass
        elif len(starts) == len(stops) == 1:
            startsname, = starts
            stopsname,  = stops
            out[startsname], out[stopsname] = self.fromcounts(super(ListCounts, self).getall([startsname + self.suffix], {}))
        else:
            raise RuntimeError("cannot determine which starts ({0}) corresponds to which stops ({1})".format(", ".join(repr(n) for n in starts), ", ".join(repr(n) for n in stops)))
        return out

    def putall(self, names2arrays, roles):
        others = dict((n, x) for n, x in names.items() if roles.get(n, None) is not oamap.generator.STARTS and roles.get(n, None) is not oamap.generator.STOPS)
        starts = dict((n, x) for n, x in names.items() if roles.get(n, None) is oamap.generator.STARTS)
        stops  = dict((n, x) for n, x in names.items() if roles.get(n, None) is oamap.generator.STOPS)

        if len(starts) == len(stops) == 0:
            pass
        elif len(starts) == len(stops) == 1:
            (startsname, startsarray), = starts.items()
            (stopsname,  stopsarray),  = stops.items()
            super(ListCounts, self).putall({startsname + self.suffix: self.tocounts(startsarray, stopsarray)}, {})
        else:
            raise RuntimeError("cannot determine which starts ({0}) corresponds to which stops ({1})".format(", ".join(repr(n) for n in starts), ", ".join(repr(n) for n in stops)))
        super(ListCounts, self).putall(others, roles)

    def fromcounts(self, array):
        offsets = numpy.empty(len(array) + 1, dtype=oamap.generator.ListGenerator.posdtype)
        offsets[0] = 0
        offsets[1:] = numpy.cumsum(counts)
        return offsets[:-1], offsets[1:]

    def tocounts(self, starts, stops):
        if not isinstance(starts, numpy.ndarray):
            starts = numpy.array(starts, dtype=oamap.generator.ListGenerator.posdtype)
        if not isinstance(starts, numpy.ndarray):
            stops = numpy.array(stops, dtype=oamap.generator.ListGenerator.posdtype)
        if not starts[0] == 0 or not numpy.array_equal(starts[1:], stops[:-1]):
            raise ValueError("starts and stops cannot be converted to a single counts array")
        return stops - starts

################################################################ DropUnionOffsets

class UnionDropOffsets(PackedSource):
    def __init__(self, source):
        super(DropUnionOffsets, self).__init__(source, "")

    def _tojsonargs(self):
        return []

    def getall(self, names, roles):
        tags    = [n for n in names if roles.get(n, None) is oamap.generator.TAGS]
        offsets = [n for n in names if roles.get(n, None) is oamap.generator.OFFSETS]

        out = super(UnionDropOffsets, self).getall([n for n in names if n not in offsets], roles)
        if len(tags) == len(offsets) == 0:
            pass
        elif len(tags) == len(offsets) == 1:
            tagsname,    = tags
            offsetsname, = offsets
            out[offsetsname] = self.tags2offsets(out[tagsname])
        else:
            raise RuntimeError("cannot determine which tags ({0}) corresponds to which offsets ({1})".format(", ".join(repr(n) for n in tags), ", ".join(repr(n) for n in offsets)))
        return out

    def putall(self, names2arrays, roles):
        super(UnionDropOffsets, self).putall(dict((n, x) for n, x in names2arrays.items() if roles.get(n, None) is not oamap.generator.OFFSETS), roles)

    def tags2offsets(self, tags):
        if not isinstance(tags, numpy.ndarray):
            tags = numpy.array(tags, dtype=oamap.generator.UnionGenerator.tagdtype)
        offsets = numpy.empty(len(tags), dtype=oamap.generator.UnionGenerator.offsetdtype)
        for tag in numpy.unique(tags):
            hastag = (tags == tag)
            offsets[hastag] = numpy.arange(hastag.sum(), dtype=offsets.dtype)
        return offsets

################################################################ CompressAll

# TODO: apply a named compression algorithm
