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





# import pyarrow.parquet

# # schema = pyarrow.parquet.read_schema("/home/pivarski/diana/oamap-gh-pages/examples/planets_formats/planets.parquet")

# reader = pyarrow.parquet.ParquetReader()
# reader.open("/home/pivarski/diana/oamap-gh-pages/examples/planets_formats/planets.parquet")

# schema = reader.metadata.schema.to_arrow_schema()
# reader.column_paths
# reader.metadata.schema.column(245)
# reader.read_column(245)
# reader.read_column(245).to_pandas()




# import parquet
# import gzip
# import io
# import numpy

# file = open("/home/pivarski/diana/oamap-gh-pages/examples/planets_formats/planets.parquet")
# if not parquet._check_header_magic_bytes(file) or not parquet._check_footer_magic_bytes(file):
#     raise IOError("not a valid parquet file (missing magic bytes)")
# footer = parquet._read_footer(file)
# footer.num_rows
# footer.schema   # list
# footer.key_value_metadata[0]  # .key .value (both unicode) Spark's JSON schema
# footer.schema[5]  # radialvelocity.val
# footer.schema[5].type == parquet.parquet_thrift.Type.FLOAT
# footer.schema[5].repetition_type == parquet.parquet_thrift.FieldRepetitionType.OPTIONAL
# footer.row_groups[0].columns[3].meta_data.path_in_schema
# footer.row_groups[0].num_rows
# footer.row_groups[0].columns[3]
# footer.row_groups[0].columns[3].file_offset

# file.seek(footer.row_groups[0].columns[3].file_offset)
# page_header = parquet._read_page_header(file)
# compresseddata = file.read(page_header.compressed_page_size)
# data = gzip.GzipFile(fileobj=io.BytesIO(compresseddata), mode="rb").read()

# num_nonnull = page_header.data_page_header.num_values - page_header.data_page_header.statistics.null_count
# values = numpy.frombuffer(data[-num_nonnull*4:], dtype="<f4")

# page_header.data_page_header.definition_level_encoding == parquet.parquet_thrift.Encoding.RLE
# page_header.data_page_header.repetition_level_encoding == parquet.parquet_thrift.Encoding.BIT_PACKED
