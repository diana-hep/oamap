#!/usr/bin/env python

# fastparquet is part of the Dask project with Apache v2.0 license.
# 
#     https://github.com/dask/fastparquet
#     https://github.com/dask/fastparquet/blob/master/LICENSE
#     https://fastparquet.readthedocs.io/en/latest/
# 
# It's better to copy parts of fastparquet than to include it as a
# dependency. We want a very small fraction of its functionality (just
# the raw columns!) without all of its dependencies. This copy is
# limited to the functions we actually use, and the OAMap maintainer
# is responsible for keeping this copy up-to-date. For this reason,
# the copy is almost exactly literal, to make comparisons easier.

import sys

PY2 = sys.version_info[0] <= 2

def byte_buffer(raw_bytes):
    return buffer(raw_bytes) if PY2 else memoryview(raw_bytes)
