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

import gzip
import math
import os
import struct
import sys
import zlib

import numpy

import oamap.schema
import oamap.generator
import oamap.source._fastparquet.schema
import oamap.source._fastparquet.core
from oamap.source._fastparquet.extra import thriftpy
from oamap.source._fastparquet.extra import parquet_thrift
from oamap.source._fastparquet.extra import OrderedDict

try:
    import snappy
except ImportError:
    snappy = None
try:
    import lzo
except ImportError:
    lzo = None
try:
    import brotli
except ImportError:
    brotli = None
try:
    import lz4.block
except ImportError:
    lz4 = None

def _decompression(codec):
    if codec == parquet_thrift.CompressionCodec.UNCOMPRESSED:
        return lambda compressed, compressedbytes, uncompressedbytes: compressed

    elif codec == parquet_thrift.CompressionCodec.SNAPPY:
        if snappy is None:
            raise ImportError("\n\nTo read Parquet files with snappy compression, install snappy package with:\n\n    pip install python-snappy --user\nor\n    conda install -c conda-forge python-snappy")
        return lambda compressed, compressedbytes, uncompressedbytes: snappy.decompress(compressed)

    elif codec == parquet_thrift.CompressionCodec.GZIP:
        if sys.version_info[0] <= 2:
            return lambda compressed, compressedbytes, uncompressedbytes: zlib.decompress(compressed, 16 + 15)
        else:
            return lambda compressed, compressedbytes, uncompressedbytes: gzip.decompress(compressed)

    elif codec == parquet_thrift.CompressionCodec.LZO:
        if lzo is None:
            raise ImportError("install lzo")      # FIXME: provide installation instructions
        else:
            return lambda compressed, compressedbytes, uncompressedbytes: lzo.decompress(compressed)

    elif codec == parquet_thrift.CompressionCodec.BROTLI:
        if brotli is None:
            raise ImportError("install brotli")   # FIXME: provide installation instructions
        else:
            return lambda compressed, compressedbytes, uncompressedbytes: brotli.decompress(compressed)

    elif codec == parquet_thrift.CompressionCodec.LZ4:
        if lz4 is None:
            raise ImportError("\n\nTo read Parquet files with lz4 compression, install lz4 package with:\n\n    pip install lz4 --user\nor\n    conda install -c anaconda lz4")
        else:
            return lambda compressed, compressedbytes, uncompressedbytes: lz4.block.decompress(compressed, uncompressed_size=uncompressedbytes)

    elif codec == parquet_thrift.CompressionCodec.ZSTD:
        # FIXME: find the Python zstd package
        raise NotImplementedError("ZSTD decompression")

    else:
        raise AssertionError("unrecognized codec: {0}".format(codec))

def _parquet2oamap(parquetschema):
    # type
    if parquetschema.type == parquet_thrift.Type.BOOLEAN:
        oamapschema = oamap.schema.Primitive(numpy.bool_)

    elif parquetschema.type == parquet_thrift.Type.INT32:
        oamapschema = oamap.schema.Primitive(numpy.int32)

    elif parquetschema.type == parquet_thrift.Type.INT64:
        oamapschema = oamap.schema.Primitive(numpy.int64)

    elif parquetschema.type == parquet_thrift.Type.INT96:
        oamapschema = oamap.schema.Primitive("S12")

    elif parquetschema.type == parquet_thrift.Type.FLOAT:
        oamapschema = oamap.schema.Primitive(numpy.float32)

    elif parquetschema.type == parquet_thrift.Type.DOUBLE:
        oamapschema = oamap.schema.Primitive(numpy.float64)

    elif parquetschema.type == parquet_thrift.Type.BYTE_ARRAY:
        oamapschema = oamap.schema.List(oamap.schema.Primitive(numpy.uint8), name="ByteString")

    elif parquetschema.type == parquet_thrift.Type.FIXED_LEN_BYTE_ARRAY:
        oamapschema = oamap.schema.Primitive("S%d" % parquetschema.type_length)

    elif parquetschema.type is None:
        oamapschema = oamap.schema.Record(OrderedDict((n, _parquet2oamap(x)) for n, x in parquetschema.children.items()))

    else:
        raise AssertionError("unrecognized Parquet schema type: {0}".format(parquetschema.type))

    # repetition_type for nullability (only; list annotation comes from converted_type)
    if parquetschema.repetition_type == parquet_thrift.FieldRepetitionType.OPTIONAL:
        oamapschema.nullable = True

    # converted_type
    if parquetschema.converted_type is None:
        pass

    elif parquetschema.converted_type == parquet_thrift.ConvertedType.UTF8:
        assert parquetschema.type == parquet_thrift.Type.BYTE_ARRAY
        oamapschema.name = "UTF8String"

    elif parquetschema.converted_type == parquet_thrift.ConvertedType.MAP:
        # assert optional field containing repeated key/value pair
        raise NotImplementedError

    elif parquetschema.converted_type == parquet_thrift.ConvertedType.MAP_KEY_VALUE:
        # assert group of two fields
        raise NotImplementedError

    elif parquetschema.converted_type == parquet_thrift.ConvertedType.LIST:
        assert isinstance(oamapschema, oamap.schema.Record) and len(oamapschema.fields) == 1
        content, = oamapschema.fields.values()
        oamapschema = oamap.schema.List(content, nullable=False)

    elif parquetschema.converted_type == parquet_thrift.ConvertedType.ENUM:
        # assert binary field
        raise NotImplementedError

    elif parquetschema.converted_type == parquet_thrift.ConvertedType.DECIMAL:
        # assert binary or fixed primitive
        raise NotImplementedError

    elif parquetschema.converted_type == parquet_thrift.ConvertedType.DATE:
        assert parquetschema.type == parquet_thrift.Type.INT32
        raise NotImplementedError

    elif parquetschema.converted_type == parquet_thrift.ConvertedType.TIME_MILLIS:
        assert parquetschema.type == parquet_thrift.Type.INT32
        raise NotImplementedError

    elif parquetschema.converted_type == parquet_thrift.ConvertedType.TIME_MICROS:
        assert parquetschema.type == parquet_thrift.Type.INT64
        raise NotImplementedError

    elif parquetschema.converted_type == parquet_thrift.ConvertedType.TIMESTAMP_MILLIS:
        assert parquetschema.type == parquet_thrift.Type.INT64
        raise NotImplementedError

    elif parquetschema.converted_type == parquet_thrift.ConvertedType.TIMESTAMP_MICROS:
        assert parquetschema.type == parquet_thrift.Type.INT64
        raise NotImplementedError

    elif parquetschema.converted_type == parquet_thrift.ConvertedType.UINT_8 or \
         parquetschema.converted_type == parquet_thrift.ConvertedType.UINT_16 or \
         parquetschema.converted_type == parquet_thrift.ConvertedType.UINT_32:
        assert parquetschema.type == parquet_thrift.Type.INT32
        raise NotImplementedError

    elif parquetschema.converted_type == parquet_thrift.ConvertedType.UINT_64:
        assert parquetschema.type == parquet_thrift.Type.INT64
        raise NotImplementedError

    elif parquetschema.converted_type == parquet_thrift.ConvertedType.INT_8 or \
         parquetschema.converted_type == parquet_thrift.ConvertedType.INT_16 or \
         parquetschema.converted_type == parquet_thrift.ConvertedType.INT_32:
        assert parquetschema.type == parquet_thrift.Type.INT32
        raise NotImplementedError

    elif parquetschema.converted_type == parquet_thrift.ConvertedType.INT_64:
        assert parquetschema.type == parquet_thrift.Type.INT64
        raise NotImplementedError

    elif parquetschema.converted_type == parquet_thrift.ConvertedType.JSON:
        assert parquetschema.type == parquet_thrift.Type.BYTE_ARRAY
        raise NotImplementedError

    elif parquetschema.converted_type == parquet_thrift.ConvertedType.BSON:
        assert parquetschema.type == parquet_thrift.Type.BYTE_ARRAY
        raise NotImplementedError

    elif parquetschema.converted_type == parquet_thrift.ConvertedType.INTERVAL:
        assert parquetschema.type == parquet_thrift.Type.FIXED_LEN_BYTE_ARRAY and parquetschema.type_length == 12
        raise NotImplementedError

    else:
        raise AssertionError("unrecognized Parquet converted_type: {0}".format(parquetschema.converted_type))

    if parquetschema.hasdictionary:
        oamapschema = oamap.schema.Pointer(oamapschema)
        oamapschema.nullable = oamapschema.target.nullable
        oamapschema.target.nullable = False
        
    parquetschema.oamapschema = oamapschema
    return oamapschema

class ParquetFile(object):
    def __init__(self, file, prefix="object", delimiter="-"):
        # raise ImportError late, when the user actually tries to read a ParquetFile
        if parquet_thrift is None:
            raise ImportError("\n\nTo read Parquet files, install thriftpy package with:\n\n    pip install thriftpy --user\nor\n    conda install -c conda-forge thriftpy")

        # file object may be an array (probably memmap) or a real file (thing with a read/seek interface)
        if isinstance(file, numpy.ndarray):
            if file.dtype.itemsize != 1 or len(file.shape) != 1:
                raise TypeError("if file is a Numpy array, the item size must be 1 (such as numpy.uint8) and shape must be flat, not {0} and {1}".format(file.dtype, file.shape))
            self.memmap = file
        elif hasattr(file, "read") and hasattr(file, "seek"):
            self.file = file
        else:
            raise TypeError("file must be a Numpy array (e.g. memmap) or a file-like object with read and seek methods")

        # check for magic and footer in both cases
        if hasattr(self, "memmap"):
            headermagic = self.memmap[:4].tostring()
            footermagic = self.memmap[-4:].tostring()
            footerbytes, = self.memmap[-8:-4].view("<i4")
            index = len(self.memmap) - (footerbytes + 8)

            class TFileTransport(thriftpy.transport.TTransportBase):
                def __init__(self, memmap, index):
                    self._memmap = memmap
                    self._index = index
                def _read(self, bytes):
                    if not (0 <= self._index < len(self._memmap)):
                        raise IOError("seek point {0} is beyond array with {1} bytes".format(self._index, len(self._memmap)))
                    out = self._memmap[self._index : self._index + bytes]
                    self._index += bytes
                    if len(out) == 0:
                        return b""
                    else:
                        return out.tostring()

            self.TFileTransport = TFileTransport

        else:
            self.file.seek(0, os.SEEK_SET)
            headermagic = file.read(4)

            self.file.seek(-4, os.SEEK_END)
            footermagic = file.read(4)

            self.file.seek(-8, os.SEEK_END)
            footerbytes, = struct.unpack(b"<i", file.read(4))

            self.file.seek(-(footerbytes + 8), os.SEEK_END)
            index = None

            class TFileTransport(thriftpy.transport.TTransportBase):
                def __init__(self, file, index):
                    self._file = file
                def _read(self, bytes):
                    return self._file.read(bytes)

            self.TFileTransport = TFileTransport

        if headermagic != b"PAR1":
            raise ValueError("not a Parquet-formatted file: header magic is {0}".format(repr(headermagic)))
        if footermagic != b"PAR1":
            raise ValueError("not a Parquet-formatted file: footer magic is {0}".format(repr(footermagic)))

        # actually read in the footer
        tin = self.TFileTransport(file, index)
        pin = thriftpy.protocol.compact.TCompactProtocolFactory().get_protocol(tin)
        self.footer = parquet_thrift.FileMetaData()
        self.footer.read(pin)

        # pass over schema elements: find the top-level fields (fastparquet's schema_helper makes the tree structure)
        self.path_to_schema = {}

        def recurse(index, path):
            parquetschema = self.footer.schema[index]

            parquetschema.path = path + (parquetschema.name,)
            self.path_to_schema[parquetschema.path] = parquetschema
            parquetschema.chunks = []
            parquetschema.hasdictionary = False
            parquetschema.hassize = (parquetschema.type == parquet_thrift.Type.BYTE_ARRAY)

            if parquetschema.num_children is not None:
                for i in range(parquetschema.num_children):
                    index += 1
                    index = recurse(index, parquetschema.path)
            return index

        index = 0
        self.fields = OrderedDict()
        while index + 1 < len(self.footer.schema):
            index += 1
            parquetschema = self.footer.schema[index]
            self.fields[parquetschema.name] = parquetschema
            index = recurse(index, ())

        # pass over rowgroup/column elements, linking to schema and checking for dictionary encodings
        for rowgroupid, rowgroup in enumerate(self.footer.row_groups):
            for columnchunk in rowgroup.columns:
                parquetschema = self.path_to_schema[tuple(columnchunk.meta_data.path_in_schema)]
                assert len(parquetschema.chunks) == rowgroupid
                parquetschema.chunks.append(columnchunk)
                if any(x == parquet_thrift.Encoding.PLAIN_DICTIONARY or x == parquet_thrift.Encoding.RLE_DICTIONARY for x in columnchunk.meta_data.encodings):
                    parquetschema.hasdictionary = True

        # fastparquet's schema_helper makes the tree structure
        self.schema_helper = oamap.source._fastparquet.schema.SchemaHelper(self.footer.schema)

        self.oamapschema = oamap.schema.List(oamap.schema.Record(OrderedDict((x.name, _parquet2oamap(x)) for x in self.fields.values())))
        self.oamapschema.defaultnames(prefix=prefix, delimiter=delimiter)
        self._prefix = prefix
        self._delimiter = delimiter

        # self.oamapschema.show()

        def recurse2(parquetschema, defsequence, repsequence):
            if parquetschema.converted_type == parquet_thrift.ConvertedType.LIST:
                defsequence = defsequence + (parquetschema.oamapschema.starts,)
                repsequence = repsequence + (parquetschema.oamapschema.starts,)

            elif parquetschema.repetition_type == parquet_thrift.FieldRepetitionType.OPTIONAL:
                defsequence = defsequence + (parquetschema.oamapschema.mask,)

            parquetschema.defsequence = defsequence
            parquetschema.repsequence = repsequence

            if parquetschema.num_children is not None:
                for child in parquetschema.children.values():
                    recurse2(child, defsequence, repsequence)

        for field in self.fields.values():
            recurse2(field, (), ())

    def column(self, parquetschema, rowgroupid, parallel=False):
        if parallel:
            raise NotImplementedError

        columnchunk = parquetschema.chunks[rowgroupid]

        def get_num_values(header):
            if header.type == parquet_thrift.PageType.DATA_PAGE:
                return header.data_page_header.num_values
            elif header.type == parquet_thrift.PageType.INDEX_PAGE:
                return header.index_page_header.num_values
            elif header.type == parquet_thrift.PageType.DICTIONARY_PAGE:
                return header.dictionary_page_header.num_values
            elif header.type == parquet_thrift.PageType.DATA_PAGE_V2:
                return header.data_page_header_v2.num_values
            else:
                raise AssertionError("unrecognized header type: {0}".format(header.type))

        if hasattr(self, "memmap"):
            def pagereader(index):
                # always safe for parallelization
                num_values = 0
                while num_values < columnchunk.meta_data.num_values:
                    tin = self.TFileTransport(self.memmap, index)
                    pin = thriftpy.protocol.compact.TCompactProtocolFactory().get_protocol(tin)
                    header = parquet_thrift.PageHeader()
                    header.read(pin)
                    index = tin._index
                    compressed = self.memmap[index : index + header.compressed_page_size]
                    index += header.compressed_page_size
                    num_values += get_num_values(header)
                    yield header, compressed

        else:
            def pagereader(index):
                # if parallel, open a new file to avoid conflicts with other threads
                file = self.file
                file.seek(index, os.SEEK_SET)
                num_values = 0
                while num_values < columnchunk.meta_data.num_values:
                    tin = self.TFileTransport(file, index)
                    pin = thriftpy.protocol.compact.TCompactProtocolFactory().get_protocol(tin)
                    header = parquet_thrift.PageHeader()
                    header.read(pin)
                    compressed = file.read(header.compressed_page_size)
                    num_values += get_num_values(header)
                    yield header, compressed
        
        decompress = _decompression(columnchunk.meta_data.codec)
        
        dictionary = None
        deflevelsegs = []
        replevelsegs = []
        datasegs = []
        sizesegs = []

        for header, compressed in pagereader(columnchunk.file_offset):
            uncompressed = numpy.frombuffer(decompress(compressed, header.compressed_page_size, header.uncompressed_page_size), dtype=numpy.uint8)

            # data page
            if header.type == parquet_thrift.PageType.DATA_PAGE:
                deflevelseg, replevelseg, dataseg = oamap.source._fastparquet.core.read_data_page(uncompressed, self.schema_helper, header, columnchunk.meta_data)
                
                if deflevelseg is not None:
                    deflevelsegs.append(deflevelseg)
                if replevelseg is not None:
                    replevelsegs.append(replevelseg)
                if isinstance(dataseg, tuple) and len(dataseg) == 2:
                    datasegs.append(dataseg[0])
                    sizesegs.append(dataseg[1])
                else:
                    datasegs.append(dataseg)

            # index page (doesn't exist in Parquet yet, either)
            elif header.type == parquet_thrift.PageType.INDEX_PAGE:
                raise NotImplementedError

            # dictionary page
            elif header.type == parquet_thrift.PageType.DICTIONARY_PAGE:
                dictionary = oamap.source._fastparquet.core.read_dictionary_page(uncompressed, self.schema_helper, header, columnchunk.meta_data)

            # data page version 2
            elif header.type == parquet_thrift.PageType.DATA_PAGE_V2:
                raise NotImplementedError

            else:
                raise AssertionError("unrecognized header type: {0}".format(header.type))

        # concatenate pages into a column
        if len(deflevelsegs) == 0:
            deflevel = None
        elif len(deflevelsegs) == 1:
            deflevel = deflevelsegs[0]
        else:
            deflevel = numpy.concatenate(deflevelsegs)

        if len(replevelsegs) == 0:
            replevel = None
        elif len(replevelsegs) == 1:
            replevel = replevelsegs[0]
        else:
            replevel = numpy.concatenate(replevelsegs)

        if len(datasegs) == 0:
            data = None
        elif len(datasegs) == 1:
            data = datasegs[0]
        else:
            data = numpy.concatenate(datasegs)

        if len(sizesegs) == 0:
            size = None
        elif len(sizesegs) == 1:
            size = sizesegs[0]
        else:
            size = numpy.concatenate(sizesegs)

        # deal with cases in which the footer lied to us
        if parquetschema.hasdictionary and dictionary is None:
            raise NotImplementedError

        if not parquetschema.hasdictionary and dictionary is not None:
            raise NotImplementedError

        return dictionary, deflevel, replevel, data, size

    def rowgroup(self, rowgroupid):
        return self.oamapschema(ParquetRowGroupArrays(self, rowgroupid))

    def __iter__(self):
        for rowgroupid in range(len(self.footer.row_groups)):
            for x in self.rowgroup(rowgroupid):
                yield x

    def arrays(self, parquetschema, rowgroupid, parallel=False):
        dictionary, deflevel, replevel, data, size = self.column(parquetschema, rowgroupid, parallel=parallel)
        out = {}

        print "defsequence", parquetschema.defsequence
        print "repsequence", parquetschema.repsequence

        if len(parquetschema.defsequence) > 0:
            assert deflevel is not None

            first = True
            length = len(deflevel)
            for depth, maskname in enumerate(parquetschema.defsequence):
                masked = (deflevel == depth)
                if not first:
                    masked = masked[stencil]
                notmasked = numpy.bitwise_not(masked)

                if maskname in parquetschema.repsequence:
                    # this is a list, not a nullable type; we need to process it only to compactify properly
                    length = numpy.count_nonzero(notmasked)                                   # new length
                else:
                    # this is a nullable type; need to create and store a mask
                    oamapmask = numpy.empty(length, dtype=oamap.generator.Masked.maskdtype)   # old length
                    length = numpy.count_nonzero(notmasked)                                   # new length
                    oamapmask[masked] = oamap.generator.Masked.maskedvalue
                    oamapmask[notmasked] = numpy.arange(length, dtype=oamap.generator.Masked.maskdtype)
                    out[maskname] = oamapmask

                first = False
                stencil = (deflevel > depth)

        if len(parquetschema.repsequence) > 0:
            assert replevel is not None
            assert len(deflevel) == len(replevel)
            
            print "deflevel", deflevel.tolist()
            print "replevel", replevel.tolist()

# {"list3": [[[0, 1, 2], [], [], [3, 4]]]}
# {"list3": [[[5, 6]], [], [], [[7, 8]]]}
# {"list3": [[[9, 10, 11], []], []]}

            count = [0, 0, 0, 0]
            counts = ([], [], [], [])
            for d, r in reversed(zip(deflevel, replevel)):
                if d == 3:
                    assert r <= 3
                    if r == 3:
                        count[3] += 1
                    if r == 2:
                        count[3] += 1
                        counts[3].append(count[3]); count[3] = 0
                        count[2] += 1
                    if r == 1:
                        count[3] += 1
                        counts[3].append(count[3]); count[3] = 0
                        count[2] += 1
                        counts[2].append(count[2]); count[2] = 0
                        count[1] += 1
                    if r == 0:
                        count[3] += 1
                        counts[3].append(count[3]); count[3] = 0
                        count[2] += 1
                        counts[2].append(count[2]); count[2] = 0
                        count[1] += 1
                        counts[1].append(count[1]); count[1] = 0
                        count[0] += 1
                if d == 2:
                    assert r <= 2
                    if r == 2:
                        assert count[3] == 0
                        counts[3].append(count[3]); count[3] = 0
                        count[2] += 1
                    if r == 1:
                        assert count[3] == 0
                        counts[3].append(count[3]); count[3] = 0
                        count[2] += 1
                        counts[2].append(count[2]); count[2] = 0
                        count[1] += 1
                    if r == 0:
                        assert count[3] == 0
                        counts[3].append(count[3]); count[3] = 0
                        count[2] += 1
                        counts[2].append(count[2]); count[2] = 0
                        count[1] += 1
                        counts[1].append(count[1]); count[1] = 0
                        count[0] += 1
                if d == 1:
                    assert r <= 1
                    if r == 1:
                        assert count[2] == 0
                        counts[2].append(count[2]); count[2] = 0
                        count[1] += 1
                    if r == 0:
                        assert count[2] == 0
                        counts[2].append(count[2]); count[2] = 0
                        count[1] += 1
                        counts[1].append(count[1]); count[1] = 0
                        count[0] += 1
                if d == 0:
                    assert r <= 0
                    if r == 0:
                        assert count[1] == 0
                        counts[1].append(count[1]); count[1] = 0
                        count[0] += 1

                print
                print "count[1]", count[1], "counts[1]", counts[1]
                print "count[2]", count[2], "counts[2]", counts[2]
                print "count[3]", count[3], "counts[3]", counts[3]
                
            counts[0].append(count[0])

            print "count[0]", count[0], "counts[0]", counts[0]

                    # if r == 1:
                    #     counts[2].append(count[2]); count[2] = 0
                    # if r == 0:
                    #     counts[2].append(count[2]); count[2] = 0
                    #     counts[1].append(count[1]); count[1] = 0




            # count = [0, 0, 0]
            # counts = ([], [], [])
            # for d, r in reversed(zip(deflevel, replevel)):
            #     if d == 3:
            #         count[2] += 1
            #     if d >= 2 and r < 3:
            #         counts[2].append(count[2])
            #         count[2] = 0

            #     # if d == 3:
            #     #     count[2] += 1
            #     # if r < 3:
            #     #     counts[2].append(count[2])
            #     #     count[2] = 0
            #     #     count[1] += 1

            #     # if d == 2:
            #     #     count[1] += 1
            #     # if r < 2:
            #     #     counts[1].append(count[1])
            #     #     count[1] = 0
            #     #     count[0] += 1

            #     # if d == 1:
            #     #     count[0] += 1
            #     # if r < 1:
            #     #     counts[0].append(count[0])
            #     #     count[0] = 0

            # print "counts[0]", counts[0]
            # print "counts[1]", counts[1]
            # print "counts[2]", counts[2]


            # offsets = ([], [], [])

            # length = 0
            # for d, r in zip(deflevel, replevel):
            #     for offseti in range(len(offsets)):
            #         if r < offseti + 1:
            #             if offseti + 1 < len(offsets):
            #                 offsets[offseti].append(len(offsets[offseti + 1]))
            #             else:
            #                 offsets[offseti].append(length)

            #     if d == 3:
            #         length += 1

            # for offseti in range(len(offsets) - 1, -1, -1):
            #     if offseti + 1 < len(offsets):
            #         offsets[offseti].append(len(offsets[offseti + 1]))
            #     else:
            #         offsets[offseti].append(length)

            # print "offsets[0]", offsets[0]
            # print "offsets[1]", offsets[1]
            # print "offsets[2]", offsets[2]


                
            # laststarts = None
            # for repdepth, name in reversed(list(enumerate(parquetschema.repsequence))):
            #     defdepth = parquetschema.defsequence.index(name)
            #     print "repdepth", repdepth, "defdepth", defdepth

            #     reps = replevel[deflevel > defdepth]
            #     if laststarts is not None:
            #         reps = reps[laststarts]

            #     starts, = numpy.where(reps < repdepth + 1)
            #     stops = numpy.append(starts[1:], len(reps))

            #     print "reps", reps.tolist()
            #     print "starts", starts.tolist()
            #     print "stops", stops.tolist()

            #     laststarts = starts

            # raise Exception

        oamapschema = parquetschema.oamapschema

        if parquetschema.hasdictionary:
            assert isinstance(oamapschema, oamap.schema.Pointer)            
            assert dictionary is not None
            assert size is None

            out[oamapschema.positions] = data
            oamapschema = oamapschema.target

            if isinstance(dictionary, tuple) and len(dictionary) == 2:
                data, size = dictionary
            else:
                data = dictionary

        if parquetschema.hassize:
            assert isinstance(oamapschema, oamap.schema.List)
            assert isinstance(oamapschema.content, oamap.schema.Primitive)
            assert oamapschema.content.dtype == numpy.dtype(numpy.uint8)
            assert size is not None
            out[oamapschema.counts] = size
            out[oamapschema.content.data] = data

        else:
            assert isinstance(oamapschema, oamap.schema.Primitive)
            assert oamapschema.dtype == data.dtype
            out[oamapschema.data] = data

        return out

class ParquetRowGroupArrays(object):
    def __init__(self, parquetfile, rowgroupid):
        self._parquetfile = parquetfile
        self._rowgroupid = rowgroupid
        self._arrays = {}
        
    def __getitem__(self, request):
        if request in self._arrays:
            return self._arrays[request]

        elif request.startswith(self._parquetfile.oamapschema.starts):
            self._arrays[request] = numpy.array([0], numpy.int32)
            return self._arrays[request]
            
        elif request.startswith(self._parquetfile.oamapschema.stops):
            self._arrays[request] = numpy.array([self._parquetfile.footer.row_groups[self._rowgroupid].num_rows], numpy.int32)
            return self._arrays[request]

        else:
            contentprefix = self._parquetfile.oamapschema._get_content(self._parquetfile._prefix, self._parquetfile._delimiter)

            found = False
            for n in self._parquetfile.oamapschema.content.fields:
                fieldprefix = self._parquetfile.oamapschema.content._get_field(contentprefix, self._parquetfile._delimiter, n)
                if request.startswith(fieldprefix):
                    found = True
                    break

            if not found:
                raise KeyError(repr(request))
            else:
                return self._getarrays(request, fieldprefix, self._parquetfile.fields[n])

    def _getarrays(self, request, prefix, parquetschema):
        if parquetschema.num_children is None:
            self._arrays.update(self._parquetfile.arrays(parquetschema, self._rowgroupid, parallel=False))
            return self._arrays[request]

        else:
            raise NotImplementedError
