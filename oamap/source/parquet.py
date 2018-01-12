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
        parquetschema.hassize = True

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

    parquetschema.oamapschema = oamapschema
    return oamapschema

class ParquetFile(object):
    def __init__(self, file):
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
            schema = self.footer.schema[index]

            schema.path = path + (schema.name,)
            self.path_to_schema[schema.path] = schema
            schema.chunks = []
            schema.defsequence = ()
            schema.repsequence = ()
            schema.hasdictionary = False
            schema.hassize = False

            if schema.num_children is not None:
                for i in range(schema.num_children):
                    index += 1
                    index = recurse(index, schema.path)
            return index

        index = 0
        self.fields = OrderedDict()
        while index + 1 < len(self.footer.schema):
            index += 1
            schema = self.footer.schema[index]
            self.fields[schema.name] = schema
            index = recurse(index, ())

        # pass over rowgroup/column elements, linking to schema and checking for dictionary encodings
        for rowgroupid, rowgroup in enumerate(self.footer.row_groups):
            for columnchunk in rowgroup.columns:
                schema = self.path_to_schema[tuple(columnchunk.meta_data.path_in_schema)]
                assert len(schema.chunks) == rowgroupid
                schema.chunks.append(columnchunk)
                if any(x == parquet_thrift.Encoding.PLAIN_DICTIONARY or x == parquet_thrift.Encoding.RLE_DICTIONARY for x in columnchunk.meta_data.encodings):
                    schema.hasdictionary = True

        # fastparquet's schema_helper makes the tree structure
        self.schema_helper = oamap.source._fastparquet.schema.SchemaHelper(self.footer.schema)

        self.oamapschema = oamap.schema.List(oamap.schema.Record(OrderedDict((x.name, _parquet2oamap(x)) for x in self.fields.values())))

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

    def rowgroup(self, rowgroupid, prefix="object", delimiter="-"):
        return self.oamapschema(ParquetRowGroupArrays(self, rowgroupid, prefix=prefix, delimiter=delimiter))

    def __iter__(self):
        for rowgroupid in range(len(self.footer.row_groups)):
            for x in self.rowgroup(rowgroupid):
                yield x

    def _arrays(self, parquetschema, rowgroupid, prefix, delimiter, parallel):
        dictionary, deflevel, replevel, data, size = self.column(parquetschema, rowgroupid, parallel=parallel)
        out = {}

        if len(parquetschema.defsequence) > 0:
            raise NotImplementedError

        if len(parquetschema.repsequence) > 0:
            raise NotImplementedError

        if parquetschema.hasdictionary:
            raise NotImplementedError

        else:
            if parquetschema.hassize:
                assert isinstance(parquetschema.oamapschema, oamap.schema.List)
                assert isinstance(parquetschema.oamapschema.content, oamap.schema.Primitive)
                assert parquetschema.oamapschema.content.dtype == numpy.dtype(numpy.uint8)
                assert size is not None
                out[parquetschema.oamapschema._get_counts(prefix, delimiter)] = size
                out[parquetschema.oamapschema.content._get_data(parquetschema.oamapschema._get_content(prefix, delimiter), delimiter)] = data

            else:
                out[parquetschema.oamapschema._get_data(prefix, delimiter)] = data

        return out

class ParquetRowGroupArrays(object):
    def __init__(self, parquetfile, rowgroupid, prefix="object", delimiter="-"):
        self._parquetfile = parquetfile
        self._rowgroupid = rowgroupid
        self._prefix = prefix
        self._delimiter = delimiter
        self._arrays = {}
        
    def __getitem__(self, request):
        if request in self._arrays:
            return self._arrays[request]

        elif request.startswith(self._parquetfile.oamapschema._get_starts(self._prefix, self._delimiter)):
            self._arrays[request] = numpy.array([0], numpy.int32)
            return self._arrays[request]
            
        elif request.startswith(self._parquetfile.oamapschema._get_stops(self._prefix, self._delimiter)):
            self._arrays[request] = numpy.array([self._parquetfile.footer.row_groups[self._rowgroupid].num_rows], numpy.int32)
            return self._arrays[request]

        else:
            contentprefix = self._parquetfile.oamapschema._get_content(self._prefix, self._delimiter)

            found = False
            for n in self._parquetfile.oamapschema.content.fields:
                fieldprefix = self._parquetfile.oamapschema.content._get_field(contentprefix, self._delimiter, n)
                if request.startswith(fieldprefix):
                    found = True
                    break

            if not found:
                raise KeyError(repr(request))
            else:
                return self._getarrays(request, fieldprefix, self._parquetfile.fields[n])

    def _getarrays(self, request, prefix, parquetschema):
        if parquetschema.num_children is None:
            self._arrays.update(self._parquetfile._arrays(parquetschema, self._rowgroupid, prefix, self._delimiter, parallel=False))
            return self._arrays[request]

        else:
            raise NotImplementedError
