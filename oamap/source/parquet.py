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

import os
import struct
import gzip
import io
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

class ParquetFile(object):
    def __init__(self, file):
        if thriftpy is None:
            raise ImportError("\n\nTo read Parquet files, Install thriftpy package with:\n\n    pip install thriftpy --user\nor\n    conda install -c conda-forge thriftpy.")

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

            class TFileTransport(thriftpy.transport.TTransportBase):
                def __init__(self, memmap):
                    self._fo = file
                    self._pos = len(memmap) - (footersize + 8)
                    self._index = self._pos
                def _read(self, size):
                    if not (0 <= self._index < len(self._fo)):
                        raise IOError("seek point {0} is beyond array with {1} bytes".format(self._index, len(self._fo)))
                    out = self._fo[self._index : self._index + size]
                    self._index += size
                    if len(out) == 0:
                        return b""
                    else:
                        return out.tostring()

        else:
            self.file.seek(0, os.SEEK_SET)
            headermagic = file.read(4)

            self.file.seek(-4, os.SEEK_END)
            footermagic = file.read(4)

            self.file.seek(-8, os.SEEK_END)
            footersize, = struct.unpack(b"<i", file.read(4))

            class TFileTransport(thriftpy.transport.TTransportBase):
                def __init__(self, file):
                    file.seek(-(footersize + 8), os.SEEK_END)
                    self._fo = file
                    self._pos = file.tell()
                def _read(self, size):
                    return self._fo.read(size)
        
        if headermagic != b"PAR1":
            raise ValueError("not a Parquet-formatted file: header magic is {0}".format(repr(headermagic)))
        if footermagic != b"PAR1":
            raise ValueError("not a Parquet-formatted file: footer magic is {0}".format(repr(footermagic)))

        tin = TFileTransport(file)
        pin = thriftpy.protocol.compact.TCompactProtocolFactory().get_protocol(tin)
        self.footer = parquet_thrift.FileMetaData()
        self.footer.read(pin)


