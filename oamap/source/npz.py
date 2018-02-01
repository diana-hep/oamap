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
import glob
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

import numpy

import oamap.schema
import oamap.inference
import oamap.fill
import oamap.proxy
from oamap.util import import_module

def open(path, mode="r", prefix="object", delimiter="-"):
    def explode(x):
        parsed = urlparse(x)
        if parsed.scheme == "file" or len(parsed.scheme) == 0:
            return sorted(glob.glob(os.path.expanduser(parsed.netloc + parsed.path)))
        else:
            raise ValueError("URL scheme '{0}' not recognized".format(parsed.scheme))

    if isinstance(path, basestring):
        paths = explode(path)
    else:
        paths = [y for x in path for y in explode(x)]

    if len(paths) == 0:
        raise ValueError("no matching filenames")

    npzfile = numpy.load(paths[0])
    try:
        datasetarray = npzfile[prefix]
        assert datasetarray.dtype == numpy.dtype(numpy.uint8) and len(datasetarray.shape) == 1
        dataset = oamap.schema.Dataset.fromjsonstring(datasetarray.tostring())
    except:
        schema = oamap.inference.fromnames(npzfile.keys(), prefix=prefix, delimiter=delimiter)
    else:
        schema = dataset.schema

    generator = schema.generator()
    listofarrays = [NumpyFileArrays(paths[0], npzfile)] + [NumpyFileArrays(x, None) for x in paths[1:]]
    return oamap.proxy.PartitionedListProxy(generator, listofarrays)

class NumpyFileArrays(object):
    def __init__(self, filename, arrays):
        self._filename = filename
        self._arrays = arrays

    def __getitem__(self, request):
        if self._arrays is None:
            self._arrays = numpy.load(self._filename)
        return self._arrays[request]

    def close(self):
        if self._arrays is not None:
            self._arrays.close()
            self._arrays = None

def load(npzfile, prefix="object", delimiter="-"):
    if not isinstance(npzfile, numpy.lib.npyio.NpzFile):
        npzfile = numpy.load(npzfile)
    if not isinstance(npzfile, numpy.lib.npyio.NpzFile):
        raise TypeError("npzfile must be a Numpy NpzFile (e.g. oamap.source.npz.load(numpy.load(\"filename.npz\")))")

    try:
        datasetarray = npzfile[prefix]
        assert datasetarray.dtype == numpy.dtype(numpy.uint8) and len(datasetarray.shape) == 1
        dataset = oamap.schema.Dataset.fromjsonstring(datasetarray.tostring())
    except:
        schema = oamap.inference.fromnames(npzfile.keys(), prefix=prefix, delimiter=delimiter)
    else:
        schema = dataset.schema

    return schema(npzfile)

def savez(file, value, schema=None, prefix="object", delimiter=None, extension=None, saveschema=True, compressed=False, inferencelimit=None, pointer_fromequal=False):
    if schema is None:
        if isinstance(value, oamap.proxy.Proxy):
            schema = value._generator.schema
        else:
            schema = oamap.inference.fromdata(value, limit=inferencelimit)

    if isinstance(schema, oamap.schema.Dataset):
        dataset = schema
        schema = dataset.schema
    else:
        dataset = oamap.schema.Dataset(schema, prefix=prefix, delimiter="-", extension=extension)

    if dataset.partitioning is not None:
        raise ValueError("npz files do not support partitioning")

    if delimiter is None:
        if dataset.delimiter is None:
            delimiter = "-"
        else:
            delimiter = dataset.delimiter

    if extension is None:
        if dataset.extension is None:
            extension = import_module("oamap.extension.common")
        elif isinstance(dataset.extension, basestring):
            extension = import_module(dataset.extension)
        else:
            extension = [import_module(x) for x in dataset.extension]

    generator = schema.generator(prefix=prefix, delimiter=delimiter, extension=extension)

    if isinstance(value, oamap.proxy.Proxy) and hasattr(value._arrays, "items"):
        arrays = dict(value._arrays.items())
    elif isinstance(value, oamap.proxy.Proxy) and hasattr(value._arrays, "keys"):
        arrays = dict((n, value._arrays[n]) for n in value._arrays.keys())
    elif isinstance(value, oamap.proxy.Proxy) and hasattr(value._arrays, "__iter__"):
        arrays = dict((n, value._arrays[n]) for n in value._arrays)
    else:
        arrays = oamap.fill.fromdata(value, generator=generator, pointer_fromequal=pointer_fromequal)

    if saveschema and prefix not in arrays:
        arrays[prefix] = numpy.frombuffer(dataset.tojsonstring(), dtype=numpy.uint8)

    if compressed:
        numpy.savez_compressed(file, **arrays)
    else:
        numpy.savez(file, **arrays)

def savez_compressed(file, value, schema=None, prefix="object", delimiter=None, extension=None, saveschema=True, inferencelimit=None, pointer_fromequal=False):
    return savez(file, value, schema=schema, prefix=prefix, delimiter=delimiter, extension=extension, saveschema=saveschema, compressed=True, inferencelimit=inferencelimit, pointer_fromequal=pointer_fromequal)
