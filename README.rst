OAMap: Object-Array Mapping
===========================

.. image:: https://travis-ci.org/diana-hep/oamap.svg?branch=master
   :target: https://travis-ci.org/diana-hep/oamap

Introduction
------------

Data analysts are often faced with a choice between speed and flexibility. Tabular data, such as SQL tables, can be processed rapidly enough for a truly interactive analysis session, but hierarchically nested formats, such as JSON, are better at representing relationships in complex data models. In some domains (such as particle physics), we want to perform calculations on JSON-like structures at the speed of SQL.

The key to high throughput on large datasets, particularly ones with more attributes than are accessed in a single pass, is laying out the data in "columns." All values of an attribute should be contiguous on disk or memory because data are paged from one cache to the next in locally contiguous blocks. The `ROOT <https://root.cern/>`_ and `Parquet <http://parquet.apache.org/>`_ file formats represent JSON-like data in columns on disk, but these data are usually deserialized into objects for processing in memory. Higher performance can be achieved by maintaining the columnar structure through all stages of the calculation (see `this talk <https://youtu.be/jvt4v2LTGK0>`_ and `this paper <https://arxiv.org/abs/1711.01229>`_).

The OAMap toolkit implements an Object Array Mapping in Python. Object Array Mappings, by analogy with Object Relational Mappings (ORMs) are one-to-one relationships between conceptual objects and physical arrays. You can write functions that appear to be operating on ordinary Python objects-- lists, tuples, class instances-- but are actually being performed on low-level, contiguous buffers (Numpy arrays). The result is fast processing of large, complex datasets with a low memory footprint.

OAMap has two primary modes: (1) pure-Python object proxies, which pretend to be Python objects but actually access array data on demand, and (2) bare-metal bytecode compiled by `Numba <http://numba.pydata.org/>`_. The pure-Python form is good for low-latency, exploratory work, while the compiled form is good for high throughput. They are seamlessly interchangeable: a Python proxy converts to the compiled form when it enters a Numba-compiled function and switches back when it leaves. You can, for instance, do a fast search in compiled code and examine the results more fully by hand.

Any columnar file format or database can be used as a data source: OAMap can get arrays of data from any dict-like object (any Python object implementing ``__getitem__``), even from within a Numba-compiled function. Backends to ROOT, Parquet, and HDF5 are included, as well as a Python ``shelve`` alternative. Storing and accessing a complete dataset, including metadata, requires no more infrastructure than a collection of named arrays. (Data types are encoded in the names, values in the arrays.) OAMap is intended as a middleware layer above file formats and databases but below a fully integrated analysis suite.

Installation
------------

Install OAMap like any other Python package:

.. code-block:: bash

    pip install oamap --user

or similar (use ``sudo``, ``virtualenv``, or ``conda`` if you wish).

**Strict dependencies:**

- `Python <http://docs.python-guide.org/en/latest/starting/installation/>`_ (2.6+, 3.4+)
- `Numpy <https://scipy.org/install.html>`_

**Recommended dependencies:**

- `Numba and LLVM <http://numba.pydata.org/numba-doc/latest/user/installing.html>`_ to JIT-compile functions (requires a particular version of LLVM, follow instructions)
- `thriftpy <https://pypi.python.org/pypi/thriftpy>`_ to read Parquet files (pure Python, pip is fine)
- `uproot <https://pypi.python.org/pypi/uproot/>`_ to read ROOT files (pure Python, pip is fine)
- `h5py <http://docs.h5py.org/en/latest/build.html>`_ to read HDF5 files (requires binary libraries; follow instructions)

**Optional dependencies:** (all are bindings to binaries that can be package-installed)

- `lz4 <https://anaconda.org/anaconda/lz4>`_ compression used by some ROOT and Parquet files
- `python-snappy <https://anaconda.org/anaconda/python-snappy>`_ compression used by some Parquet files
- `lzo <https://anaconda.org/anaconda/lzo>`_ compression used by some Parquet files
- `brotli <https://anaconda.org/conda-forge/brotli>`_ compression used by some Parquet files
