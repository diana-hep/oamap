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
      long_description = """Large datasets can be more compact and faster to access when they are laid out in columns (see `Apache Arrow <https://arrow.apache.org/>`_). Even hierarchically nested data can be presented this way, though converting the data between the columnar form and the object form can degrade performance. Non-hierarchical data (rectangular tables) is often accessed without materializing rows (see `Apache Drill <https://drill.apache.org/docs/performance/>`_), but this is more complex for data containing arbitrary-length lists of objects.

OAMap is a suite of tools for performing calculations in this way. The name stands for Object-Array-Map, in analogy with Object-Relational-Mapping in databases. OAMap has a compiler for high throughput calculations and object proxies for low latency interactive exploration.

The compiler takes a Python function operating on objects and converts it to the equivalent function operating on columnar data in Numpy arrays. This by itself can speed up access by an order of magnitude, but especially when further compiled by Numba. Since the transformed function references only numbers and arrays, Numba is capable of compiling it in "nopython" mode.

The proxies are Python objects whose contents and attributes are generated on demand, accessing the columnar arrays, minimizing downloads if the data are remote. Often, it is useful to explore the data interactively in a Python commandline or notebook, then wrap up scratch work as functions to compile. Compiled functions can also return proxies, so a high-speed search may result in anomalies to investigate by hand.

In addition, OAMap contains tools for type-inferring and constructing Arrow buffers from Python objects, JSON, etc., and saving these buffers in any format the supports sets of named arrays, such as Numpy .npz files, HDF5, object store databases, etc. The data's schema is encoded in the names of the arrays, and the data are in the arrays.""",
      author = "Jim Pivarski (DIANA-HEP)",
      author_email = "pivarski@fnal.gov",
      maintainer = "Jim Pivarski (DIANA-HEP)",
      maintainer_email = "pivarski@fnal.gov",
      url = "https://github.com/diana-hep/oamap",
      download_url = "https://github.com/diana-hep/oamap/releases",
      license = "BSD 3-clause",
      test_suite = "tests",
      install_requires = ["numpy", "numba"],  # , "meta"
      tests_require = [],
      classifiers = [
          "Development Status :: 2 - Pre-Alpha"
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
