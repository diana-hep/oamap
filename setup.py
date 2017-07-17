#!/usr/bin/env python

import os.path

from setuptools import find_packages
from setuptools import setup

def get_version():
    g = {}
    exec(open(os.path.join("rolup", "version.py")).read(), g)
    return g["__version__"]

setup(name = "rolup",
      version = get_version(),
      packages = find_packages(exclude = ["tests"]),
      scripts = [],
      description = "",
      long_description = """""",
      author = "Jim Pivarski (DIANA-HEP)",
      author_email = "pivarski@fnal.gov",
      maintainer = "Jim Pivarski (DIANA-HEP)",
      maintainer_email = "pivarski@fnal.gov",
      url = "",
      download_url = "",
      license = "Apache Software License v2",
      test_suite = "tests",
      install_requires = ["numpy"],
      tests_require = [],
      classifiers = [
          "Development Status :: 1 - Planning",
          "Intended Audience :: Developers",
          "Intended Audience :: Science/Research",
          "License :: OSI Approved :: Apache Software License",
          "Operating System :: MacOS",
          "Operating System :: POSIX",
          "Operating System :: Unix",
          "Programming Language :: Python",
          "Topic :: Scientific/Engineering",
          "Topic :: Scientific/Engineering :: Information Analysis",
          "Topic :: Scientific/Engineering :: Mathematics",
          "Topic :: Scientific/Engineering :: Physics",
          "Topic :: Software Development",
          "Topic :: Utilities",
          ],
      platforms = "Any",
      )
