OAMap: Object-Array Mapping
===========================

.. image:: https://travis-ci.org/diana-hep/oamap.svg?branch=master
   :target: https://travis-ci.org/diana-hep/oamap

Perform high-speed calculations on columnar data without creating intermediate objects.

Introduction
------------

Data analysts are often faced with a choice between speed and flexibility. Tabular data, such as SQL tables, can be processed rapidly enough for a truly interactive analysis session, but hierarchically nested formats, such as JSON, are better at representing relationships in complex data models. In some domains (such as particle physics), we want to perform calculations on JSON-like structures at the speed of SQL.

The key to high throughput on large datasets, particularly ones with more attributes than are accessed in a single pass, is laying out the data in "columns." All values of an attribute should be contiguous on disk or memory because data are paged from one cache to the next in locally contiguous blocks. The `ROOT <https://root.cern/>`_ and `Parquet <http://parquet.apache.org/>`_ file formats represent JSON-like data in columns on disk, but these data are usually deserialized into objects for processing in memory. Higher performance can be achieved by maintaining the columnar structure through all stages of the calculation (see `this talk <https://youtu.be/jvt4v2LTGK0>`_ and `this paper <https://arxiv.org/abs/1711.01229>`_).

The OAMap toolkit implements an Object Array Mapping in Python. Object Array Mappings, like Object Relational Mappings (ORMs) are one-to-one relationships between conceptual objects and physical arrays. You can write functions that appear to be operating on ordinary Python objects--- lists, tuples, class instances--- but are actually being performed on low-level, contiguous buffers (Numpy arrays). The result is low-memory, fast processing of large, complex datasets.

OAMap has two primary modes: (1) pure-Python object proxies, which pretend to be Python objects but actually access array data on demand, and (2) bare-metal bytecode compiled by `Numba <http://numba.pydata.org/>`_. The two are seamlessly interchangeable, and since OAMap proxies are `Numba extensions <http://numba.pydata.org/numba-doc/dev/extending/index.html>`_, they may be mixed with other data structures in any `Numba-compilable <http://numba.pydata.org/numba-doc/latest/reference/pysupported.html>`_ function.

Any columnar file format or database can be used as a data source: OAMap can get arrays of data from any dict-like object (Python object implementing ``__getitem__``), even in compiled code. Backends to ROOT, Parquet, and HDF5 are included, as well as a Python ``shelve`` alternative. Storing and accessing a complete dataset, including metadata, requires no more infrastructure than a collection of named arrays. (Data types are encoded in the names, values in the arrays.) OAMap is intended as a middleware layer above file formats and databases but below a fully integrated analysis suite.

Demonstration
-------------

Installation
""""""""""""

Install OAMap the usual way:

.. code-block:: bash

    pip install oamap --user

or similar (use ``sudo``, ``virtualenv``, or ``conda`` if you wish).

Sample dataset
""""""""""""""

Download the `NASA Exoplanet Archive <https://exoplanetarchive.ipac.caltech.edu/>`_ in Parquet form:

.. code-block:: bash

    wget http://diana-hep.org/oamap/examples/planets.parquet

or similar (click `this link <http://diana-hep.org/oamap/examples/planets.parquet>`_ and "Save As..." if you wish).

Exploring data
""""""""""""""

Load the Parquet dataset with its ``open`` function. If we had a large set of Parquet files, you could pass a list or glob pattern (wildcard

.. code-block:: python

    >>> import oamap.source.parquet
    >>> stars = oamap.source.parquet.open("planets.parquet")
    >>> stars
    [<Record at index 0>, <Record at index 1>, <Record at index 2>, <Record at index 3>, <Record at index 4>, ...]
