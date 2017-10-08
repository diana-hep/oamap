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

import os.path

from setuptools import find_packages
from setuptools import setup

def get_version():
    g = {}
    exec(open(os.path.join("arrowed", "version.py")).read(), g)
    return g["__version__"]

setup(name = "arrowed",
      version = get_version(),
      packages = find_packages(exclude = ["tests"]),
      scripts = [],
      description = "Compiler and proxies for algorithms running on Arrow data, including nested lists.",
      long_description = """Arrowed provides an object-oriented view of data in `Arrow format <https://arrow.apache.org/`_, including fully nested object hierarchies with arbitrary-length lists. It can also operate on buffers (disconnected arrays) that are formatted like Arrow but not yet assembled into a single data structure, which allows the same data to be used in multiple datasets.

Any function that depends on Arrow data and `the types Numba can handle <http://numba.pydata.org/numba-doc/dev/reference/numpysupported.html>`_ can be "Arrowed". An Arrowed function operates on Arrow buffers in-place, without materializing the objects that you reference in your code. This lets you write natural algorithms, apparently unboxing nested, arbitrary-length lists of record structures, but the only operations that are performed at runtime are contiguous array lookups. Thus, the Arrowed function usually runs much faster than a naive compilation.

This toolkit also includes methods for accessing data interactively in the form of lazy-evaluated proxies. These proxies behave like Python objects; you can interact with them on the commandline or in a notebook, but they load data from Arrow buffers on-the-fly. Compared with compilation, this is a slower but more convenient interface for debugging.

In addition, there are tools for type-inferring and constructing Arrow buffers from Python objects, JSON, etc. and saving these buffers in any format the supports sets of named arrays, such as Numpy .npz files, HDF5, object store databases, etc. The data's schema is encoded in the names of the arrays, and the data are in the arrays.""",
      author = "Jim Pivarski (DIANA-HEP)",
      author_email = "pivarski@fnal.gov",
      maintainer = "Jim Pivarski (DIANA-HEP)",
      maintainer_email = "pivarski@fnal.gov",
      url = "https://github.com/diana-hep/arrowed",
      download_url = "https://github.com/diana-hep/arrowed/releases",
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
