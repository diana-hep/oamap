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

import oamap.schema
import oamap.generator
from oamap.util import OrderedDict

def schema(table):
    import pyarrow
    def recurse(node, name, index, nullable):
        if isinstance(node, pyarrow.lib.ListType):
            return oamap.schema.List(recurse(node.value_type, name, index + 2, nullable),
                                     nullable=nullable,
                                     starts="{0}/{1}".format(name, index + 1),
                                     stops="{0}/{1}".format(name, index + 1),
                                     mask="{0}/{1}".format(name, index))
        elif isinstance(node, pyarrow.lib.DataType):
            return oamap.schema.Primitive(node.to_pandas_dtype(),
                                          nullable=nullable,
                                          data="{0}/{1}".format(name, index + 1),
                                          mask="{0}/{1}".format(name, index))
        else:
            raise NotImplementedError(type(node))

    fields = []
    for n in table.schema.names:
        field = table.schema.field_by_name(n)
        fields.append((n, recurse(field.type, n, 0, field.nullable)))
    
    return oamap.schema.List(
        oamap.schema.Record(OrderedDict(fields)),
        starts="",
        stops="")

def proxy(table):
    import pyarrow
    class _ArrayDict(object):
        def __init__(self, table):
            self.table = table

        def chop(self, name):
            slashindex = name.rindex("/")
            return name[:slashindex], int(name[slashindex + 1 :])

        def frombuffer(self, chunk, bufferindex):
            def truncate(array, length, offset=0):
                return array[:length + offset]

            def mask(index, length):
                buf = chunk.buffers()[index]
                if buf is None:
                    return numpy.arange(length, dtype=oamap.generator.Masked.maskdtype)
                else:
                    unmasked = truncate(numpy.unpackbits(numpy.frombuffer(buf, dtype=numpy.uint8)).view(numpy.bool_), length)
                    mask = numpy.empty(len(unmasked), dtype=oamap.generator.Masked.maskdtype)
                    mask[unmasked] = numpy.arange(unmasked.sum(), dtype=mask.dtype)
                    mask[~unmasked] = oamap.generator.Masked.maskedvalue
                    return mask

            def recurse(tpe, index, length):
                if isinstance(tpe, pyarrow.lib.ListType):
                    if index == bufferindex:
                        # list mask
                        return mask(index, length)
                    elif index + 1 == bufferindex:
                        # list starts
                        return truncate(numpy.frombuffer(chunk.buffers()[index + 1], dtype=numpy.int32), length, 1)
                    else:
                        # descend into list
                        length = truncate(numpy.frombuffer(chunk.buffers()[index + 1], dtype=numpy.int32), length, 1)[-1]
                        return recurse(tpe.value_type, index + 2, length)

                elif isinstance(tpe, pyarrow.lib.DataType):
                    if index == bufferindex:
                        # data mask
                        return mask(index, length)
                    elif index + 1 == bufferindex:
                        # data
                        return truncate(numpy.frombuffer(chunk.buffers()[index + 1], dtype=tpe.to_pandas_dtype()), length)
                    else:
                        raise AssertionError

                else:
                    raise NotImplementedError
                
            return recurse(chunk.type, 0, len(chunk))

        def getall(self, names):
            out = {}
            for name in names:
                if len(str(name)) == 0:
                    if isinstance(name, oamap.generator.StartsRole):
                        out[name] = numpy.array([0], dtype=oamap.generator.ListGenerator.posdtype)
                    elif isinstance(name, oamap.generator.StopsRole):
                        out[name] = numpy.array([self.table.num_rows], dtype=oamap.generator.ListGenerator.posdtype)
                    else:
                        raise AssertionError

                elif isinstance(name, oamap.generator.StopsRole):
                    out[name] = out[name.starts][1:]

                else:
                    columnname, bufferindex = self.chop(str(name))
                    column = self.table[self.table.schema.names.index(columnname)]
                    chunks = column.data.chunks
                    if len(chunks) == 0:
                        raise ValueError("Arrow column {0} has no chunks".format(repr(columnname)))
                    elif len(chunks) == 1:
                        out[name] = self.frombuffer(chunks[0], bufferindex)
                    else:
                        out[name] = numpy.concatenate([self.frombuffer(chunk, bufferindex) for chunk in chunks])

            return out

    return schema(table)(_ArrayDict(table))
