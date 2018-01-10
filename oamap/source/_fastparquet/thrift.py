#!/usr/bin/env python

# This part is not in fastparquet (they Pythonify the Thrift a different way).

import os

try:
    import thriftpy
    import thriftpy.protocol
except ImportError:
    thriftpy = None
    parquet_thrift = None
else:
    THRIFT_FILE = os.path.join(os.path.dirname(__file__), "parquet.thrift")
    parquet_thrift = thriftpy.load(THRIFT_FILE, module_name="parquet_thrift")
