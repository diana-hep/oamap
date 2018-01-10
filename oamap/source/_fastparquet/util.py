#!/usr/bin/env python

import sys

PY2 = sys.version_info[0] <= 2

def byte_buffer(raw_bytes):
    return buffer(raw_bytes) if PY2 else memoryview(raw_bytes)
