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
import io
import os
import struct
# try:
#     from urlparse import urlparse
# except ImportError:
#     from urllib.parse import urlparse

import numpy

try:
    import thriftpy
    import thriftpy.protocol
except ImportError:
    thriftpy = None
else:
    THRIFT_FILE = os.path.join(os.path.dirname(__file__), "parquet.thrift")
    parquet_thrift = thriftpy.load(THRIFT_FILE, module_name="parquet_thrift")

try:
    import snappy
except ImportError:
    snappy = None

from oamap.schema import *

class ParquetFile(object):
    def __init__(self, file):
        if thriftpy is None:
            raise ImportError("\n\nTo read Parquet files, install thriftpy package with:\n\n    pip install thriftpy --user\nor\n    conda install -c conda-forge thriftpy")

        if isinstance(file, numpy.ndarray):
            if file.dtype.itemsize != 1 or len(file.shape) != 1:
                raise TypeError("if file is a Numpy array, the item size must be 1 (such as numpy.uint8) and shape must be flat, not {0} and {1}".format(file.dtype, file.shape))
            self.memmap = file
        elif hasattr(file, "read") and hasattr(file, "seek"):
            self.file = file
        else:
            raise TypeError("file must be a Numpy array (e.g. memmap) or a file-like object with read and seek methods")

        if hasattr(self, "memmap"):
            headermagic = self.memmap[:4].tostring()
            footermagic = self.memmap[-4:].tostring()
            footersize, = self.memmap[-8:-4].view("<i4")
            index = len(self.memmap) - (footersize + 8)

            class TFileTransport(thriftpy.transport.TTransportBase):
                def __init__(self, memmap, index):
                    self._memmap = memmap
                    self._index = index
                def _read(self, size):
                    if not (0 <= self._index < len(self._memmap)):
                        raise IOError("seek point {0} is beyond array with {1} bytes".format(self._index, len(self._memmap)))
                    out = self._memmap[self._index : self._index + size]
                    self._index += size
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
            footersize, = struct.unpack(b"<i", file.read(4))

            self.file.seek(-(footersize + 8), os.SEEK_END)
            index = None

            class TFileTransport(thriftpy.transport.TTransportBase):
                def __init__(self, file, index):
                    self._file = file
                def _read(self, size):
                    return self._file.read(size)

            self.TFileTransport = TFileTransport

        if headermagic != b"PAR1":
            raise ValueError("not a Parquet-formatted file: header magic is {0}".format(repr(headermagic)))
        if footermagic != b"PAR1":
            raise ValueError("not a Parquet-formatted file: footer magic is {0}".format(repr(footermagic)))

        tin = self.TFileTransport(file, index)
        pin = thriftpy.protocol.compact.TCompactProtocolFactory().get_protocol(tin)
        self.footer = parquet_thrift.FileMetaData()
        self.footer.read(pin)

        def recurse(index, path):
            schema = self.footer.schema[index]
            schema.children = []
            schema.path = path + [schema.name]
            if schema.num_children is None:
                schema.num_children = 0

            for i in range(schema.num_children):
                index += 1
                schema.children.append(self.footer.schema[index])
                index = recurse(index, schema.path)
            return index

        index = 0
        self.fields = []
        while index + 1 < len(self.footer.schema):
            index += 1
            self.fields.append(self.footer.schema[index])
            index = recurse(index, [])

    def column(self, rowgroupid, schema, deflevels=True, replevels=True, data=True, executor=None, blocking=True):
        if executor is not None:
            raise NotImplementedError

        footercolumn = None
        for column in self.footer.row_groups[rowgroupid].columns:
            if column.meta_data.path_in_schema == schema.path:
                footercolumn = column
                break
        if footercolumn is None:
            raise AssertionError("columnpath not found: {0}".format(columnpath))
        
        if hasattr(self, "memmap"):
            def pagereader(index):
                num_values = 0
                while num_values < footercolumn.meta_data.num_values:
                    tin = self.TFileTransport(self.memmap, index)
                    pin = thriftpy.protocol.compact.TCompactProtocolFactory().get_protocol(tin)
                    header = parquet_thrift.PageHeader()
                    header.read(pin)
                    index = tin._index
                    compressed = self.memmap[index : index + header.compressed_page_size]
                    index += 0 if header.compressed_page_size is None else header.compressed_page_size
                    num_values += header.data_page_header.num_values
                    yield header, compressed

        else:
            def pagereader(index):
                # if parallel, open new files
                file = self.file
                file.seek(index, os.SEEK_SET)
                num_values = 0
                while num_values < footercolumn.meta_data.num_values:
                    tin = self.TFileTransport(file, index)
                    pin = thriftpy.protocol.compact.TCompactProtocolFactory().get_protocol(tin)
                    header = parquet_thrift.PageHeader()
                    header.read(pin)
                    compressed = file.read(header.compressed_page_size)
                    num_values += header.data_page_header.num_values
                    yield header, compressed
        
        if footercolumn.meta_data.codec == parquet_thrift.CompressionCodec.UNCOMPRESSED:
            def decompress(compressed):
                return compressed

        elif footercolumn.meta_data.codec == parquet_thrift.CompressionCodec.SNAPPY:
            if snappy is None:
                raise ImportError("\n\nTo read Parquet files with snappy compression, install snappy package with:\n\n    pip install python-snappy --user\nor\n    conda install -c conda-forge python-snappy")
            def decompress(compressed):
                return snappy.decompress(compressed)

        elif footercolumn.meta_data.codec == parquet_thrift.CompressionCodec.GZIP:
            def decompress(compressed):
                return gzip.GzipFile(fileobj=io.BytesIO(compresseddata), mode="rb").read()

        elif footercolumn.meta_data.codec == parquet_thrift.CompressionCodec.LZO:
            raise NotImplementedError

        elif footercolumn.meta_data.codec == parquet_thrift.CompressionCodec.BROTLI:
            raise NotImplementedError

        elif footercolumn.meta_data.codec == parquet_thrift.CompressionCodec.LZ4:
            raise NotImplementedError

        elif footercolumn.meta_data.codec == parquet_thrift.CompressionCodec.ZSTD:
            raise NotImplementedError

        else:
            raise AssertionError("unrecognized codec: {0}".format(footercolumn.meta_data.codec))

        for header, compressed in pagereader(footercolumn.file_offset):
            uncompressed = decompress(compressed)
            print
            print header
            print repr(uncompressed)

