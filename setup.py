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
      description = "Toolset for computing directly on hierarchically nested, columnar data, such as Apache Arrow.",
      long_description = """Data analysts are often faced with a choice between speed and flexibility. Tabular data, such as an SQL table or CSV file, can be accessed quickly, which improves the question-and-answer nature of exploratory data analysis. Hierarchically nested data, such as JSON, expresses better the relationship between nested quantities. These relationships *can* be represented with separate, linked tables (i.e. `database normalization <https://en.wikipedia.org/wiki/Database_normalization>`_), but at the cost of complexity for the data analyst and the introduction of expensive joins (see `this question <https://stackoverflow.com/q/38831961/1623645>`_, which got me started on this project). Ideally, we want to perform calculations on JSON-like structures at the speed of SQL.

Tools that analyze tabular data get their performance primarily by laying out data in an intelligent way: computers can access contiguous data more quickly than separated data, whether loading from a disk to memory or from memory to the processor. Datasets with many attributes, of which only a few will be 





OAMap, short for Object-Array Mapping and intended




      
Large datasets can be more compact and faster to access when they are laid out in columns (see `Apache Arrow <https://arrow.apache.org/>`_). Even hierarchically nested data can be presented this way, though converting the data between the columnar form and the object form can degrade performance. Non-hierarchical data (rectangular tables, such as an SQL table) can be accessed faster by not materializing rows (see `Apache Drill <https://drill.apache.org/docs/performance/>`_), but this is more complex for data containing variable-length objects, such as arbitrary-length lists.

OAMap is a suite of tools for performing calculations in this way. The name stands for Object-Array-Map, in analogy with Object-Relational-Mapping (ORM) in relational databases. Pure Python calculations are considerably faster and more memory efficient when datasets are expressed in OAMaps, but the real power comes from *compiling* columized code. This toolset includes `extensions to Numba <http://numba.pydata.org/numba-doc/dev/extending/index.html>`_ that will compile your object-oriented code into native array manipulations. Generally, you'd use uncompiled Python for low latency exploration of the data and Numba-compiled functions for high throughput.

OAMap only strictly depends on Numpy, but `Numba <http://numba.pydata.org/>`_ will accelerate it and `pyarrow <https://arrow.apache.org/docs/python/index.html>`_, `h5py <http://www.h5py.org/>`_, etc. provide hooks for converting data among various formats.""",
      author = "Jim Pivarski (DIANA-HEP)",
      author_email = "pivarski@fnal.gov",
      maintainer = "Jim Pivarski (DIANA-HEP)",
      maintainer_email = "pivarski@fnal.gov",
      url = "https://github.com/diana-hep/oamap",
      download_url = "https://github.com/diana-hep/oamap/releases",
      license = "BSD 3-clause",
      test_suite = "tests",
      install_requires = ["numpy"],
      tests_require = [],
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
