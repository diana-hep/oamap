#!/usr/bin/env python

import io
import os
import re
import struct

import numpy as np

from fastparquet.speedups import unpack_byte_array    # FIXME!!!

from oamap.source._fastparquet import encoding
from oamap.source._fastparquet.util import byte_buffer
from oamap.source._fastparquet.thrift import parquet_thrift

def read_data(fobj, coding, count, bit_width):
    """For definition and repetition levels

    Reads with RLE/bitpacked hybrid, where length is given by first byte.
    """
    out = np.empty(count, dtype=np.int32)
    o = encoding.Numpy32(out)
    if coding == parquet_thrift.Encoding.RLE:
        while o.loc < count:
            encoding.read_rle_bit_packed_hybrid(fobj, bit_width, o=o)
    else:
        raise NotImplementedError('Encoding %s' % coding)
    return out


def read_def(io_obj, daph, helper, metadata):
    """
    Read the definition levels from this page, if any.
    """
    definition_levels = None
    num_nulls = 0
    if not helper.is_required(metadata.path_in_schema):
        max_definition_level = helper.max_definition_level(
            metadata.path_in_schema)
        bit_width = encoding.width_from_max_int(max_definition_level)
        if bit_width:
            definition_levels = read_data(
                    io_obj, daph.definition_level_encoding,
                    daph.num_values, bit_width)[:daph.num_values]
            num_nulls = daph.num_values - (definition_levels ==
                                           max_definition_level).sum()
            ### don't drop it: I want to concatenate all the definition levels
            # if num_nulls == 0:
            #     definition_levels = None
    return definition_levels, num_nulls


def read_rep(io_obj, daph, helper, metadata):
    """
    Read the repetition levels from this page, if any.
    """
    repetition_levels = None
    if len(metadata.path_in_schema) > 1:
        max_repetition_level = helper.max_repetition_level(
            metadata.path_in_schema)
        bit_width = encoding.width_from_max_int(max_repetition_level)
        if bit_width:
            repetition_levels = read_data(io_obj, daph.repetition_level_encoding,
                                          daph.num_values,
                                          bit_width)[:daph.num_values]
            ### don't drop it: I want to concatenate all the repetition levels
            # if repetition_levels.max() == 0:
            #     repetition_levels = None
    return repetition_levels


def read_data_page(raw_bytes, helper, header, metadata, skip_nulls=False,
                   selfmade=False):
    """Read a data page: definitions, repetitions, values (in order)

    Only values are guaranteed to exist, e.g., for a top-level, required
    field.
    """
    daph = header.data_page_header
    io_obj = encoding.Numpy8(np.frombuffer(byte_buffer(raw_bytes),
                                           dtype=np.uint8))

    repetition_levels = read_rep(io_obj, daph, helper, metadata)

    if skip_nulls and not helper.is_required(metadata.path_in_schema):
        num_nulls = 0
        definition_levels = None
        skip_definition_bytes(io_obj, daph.num_values)
    else:
        definition_levels, num_nulls = read_def(io_obj, daph, helper, metadata)

    nval = daph.num_values - num_nulls
    if daph.encoding == parquet_thrift.Encoding.PLAIN:
        width = helper.schema_element(metadata.path_in_schema).type_length
        values = encoding.read_plain(raw_bytes[io_obj.loc:],
                                     metadata.type,
                                     int(daph.num_values - num_nulls),
                                     width=width)
    elif daph.encoding in [parquet_thrift.Encoding.PLAIN_DICTIONARY,
                           parquet_thrift.Encoding.RLE]:
        # bit_width is stored as single byte.
        if daph.encoding == parquet_thrift.Encoding.RLE:
            bit_width = helper.schema_element(
                    metadata.path_in_schema).type_length
        else:
            bit_width = io_obj.read_byte()
        if bit_width in [8, 16, 32] and selfmade:
            num = (encoding.read_unsigned_var_int(io_obj) >> 1) * 8
            values = io_obj.read(num * bit_width // 8).view('int%i' % bit_width)
        elif bit_width:
            values = encoding.Numpy32(np.empty(daph.num_values-num_nulls+7,
                                               dtype=np.int32))
            # length is simply "all data left in this page"
            encoding.read_rle_bit_packed_hybrid(
                        io_obj, bit_width, io_obj.len-io_obj.loc, o=values)
            values = values.data[:nval]
        else:
            values = np.zeros(nval, dtype=np.int8)
    else:
        raise NotImplementedError('Encoding %s' % daph.encoding)
    return definition_levels, repetition_levels, values[:nval]


def skip_definition_bytes(io_obj, num):
    io_obj.loc += 6
    n = num // 64
    while n:
        io_obj.loc += 1
        n //= 128


def read_dictionary_page(raw_bytes, schema_helper, page_header, column_metadata):
    """Read a page containing dictionary data.

    Consumes data using the plain encoding and returns an array of values.
    """
    if column_metadata.type == parquet_thrift.Type.BYTE_ARRAY:
        values = unpack_byte_array(raw_bytes,
                                   page_header.dictionary_page_header.num_values)
    else:
        width = schema_helper.schema_element(
            column_metadata.path_in_schema).type_length
        values = encoding.read_plain(
                raw_bytes, column_metadata.type,
                page_header.dictionary_page_header.num_values, width)
    return values
