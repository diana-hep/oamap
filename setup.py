#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

import os.path

from setuptools import find_packages
from setuptools import setup

def get_version():
    g = {}
    exec(open(os.path.join("oamap", "version.py")).read(), g)
    return g["__version__"]

setup(name = "oamap",
      version = get_version(),
      packages = find_packages(exclude = ["tests"]),
      scripts = [],
      description = "Tools for analyzing hierarchically nested, columnar data without deserialization.",
      long_description = """Data analysts are often faced with a choice between speed and flexibility. Tabular data, such as SQL tables, can be processed rapidly enough for a truly interactive analysis session, but hierarchically nested data, such as JSON, is better at representing relationships within complex data models. In some domains (such as particle physics), we want to perform calculations on JSON-like structures at the speed of SQL.

The key to high throughput for large datasets, particularly ones with many more attributes than are typically accessed in a single pass, is laying out the data in "columns." All values of an attribute should be contiguous in disk or memory because data are paged from one cache to the next in locally contiguous blocks. The `ROOT <https://root.cern/>`_ and `Parquet <http://parquet.apache.org/>`_ file formats represent hierarchically nested data in a columnar form on disk, and `Apache Arrow <https://arrow.apache.org/>`_ is an emerging standard for sharing hierarchically nested data in memory. However, data from these formats are usually deserialized into conventional data structures before processing, which limits performance (see `this talk <https://youtu.be/jvt4v2LTGK0>`_ and `this paper <https://arxiv.org/abs/1711.01229>`_).

OAMap is a toolset for computing arbitrary functions on hierarchical, columnar data without deserialization. The name stands for Object Array Mapping, in analogy with the `Object Relational Mapping (ORM) <https://en.wikipedia.org/wiki/Object-relational_mapping>`_ interface to some databases. Users (data analysts) write functions on JSON-like objects that OAMap compiles into operations on the underlying arrays, similar to the way that ORM converts object-oriented code into SQL. The difference is that mapping objects to non-relational arrays permits bare-metal performance (giving up some traditional database features).

OAMap is a Python library on top of which high-level analysis software may be built. It focuses on mapping an object-oriented view of data onto columnar arrays. `Numpy <http://www.numpy.org/>`_ is OAMap's only strict dependency, though OAMap objects are also implemented as `Numba extensions <http://numba.pydata.org/numba-doc/dev/extending/index.html>`_, so they may be used in `Numba's <http://numba.pydata.org/>`_ JIT-compiled functions at speeds that match or exceed hand-written C code. OAMap is unopinionated about the source of its columnar arrays, allowing for a variety of backends. See `the walkthrough <https://github.com/diana-hep/oamap/blob/master/README.rst#walkthrough>`_ for more.

Also, a similar object array mapping could be implemented in any language--- Python was chosen only for its popularity among data analysts.""",
      author = "Jim Pivarski (DIANA-HEP)",
      author_email = "pivarski@fnal.gov",
      maintainer = "Jim Pivarski (DIANA-HEP)",
      maintainer_email = "pivarski@fnal.gov",
      url = "https://github.com/diana-hep/oamap",
      download_url = "https://github.com/diana-hep/oamap/releases",
      license = "BSD 3-clause",
      test_suite = "tests",
      install_requires = ["numpy"],
      tests_require = ["thriftpy", "python-snappy"],
      classifiers = [
          "Development Status :: 3 - Alpha",
          "Intended Audience :: Developers",
          "Intended Audience :: Information Technology",
          "Intended Audience :: Science/Research",
          "License :: OSI Approved :: BSD License",
          "Operating System :: MacOS",
          "Operating System :: POSIX",
          "Operating System :: Unix",
          "Programming Language :: Python",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3.4",
          "Programming Language :: Python :: 3.5",
          "Programming Language :: Python :: 3.6",
          "Programming Language :: Python :: 3.7",
          "Topic :: Scientific/Engineering",
          "Topic :: Scientific/Engineering :: Information Analysis",
          "Topic :: Scientific/Engineering :: Mathematics",
          "Topic :: Scientific/Engineering :: Physics",
          "Topic :: Software Development",
          "Topic :: Utilities",
          ],
      platforms = "Any",
      )
