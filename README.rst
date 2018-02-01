OAMap: Object-Array Mapping
===========================

.. image:: https://travis-ci.org/diana-hep/oamap.svg?branch=master
   :target: https://travis-ci.org/diana-hep/oamap

Perform high-speed calculations on columnar data without creating intermediate objects.

Introduction
------------

Data analysts are often faced with a choice between speed and flexibility. Tabular data, such as SQL tables, can be processed rapidly enough for a truly interactive analysis session, but hierarchically nested formats, such as JSON, are better at representing relationships in complex data models. In some domains (such as particle physics), we want to perform calculations on JSON-like structures at the speed of SQL.

The key to high throughput on large datasets, particularly ones with more attributes than are accessed in a single pass, is laying out the data in "columns." All values of an attribute should be contiguous on disk or memory because data are paged from one cache to the next in locally contiguous blocks. The `ROOT <https://root.cern/>`_ and `Parquet <http://parquet.apache.org/>`_ file formats represent JSON-like data in columns on disk, but these data are usually deserialized into objects for processing in memory. Higher performance can be achieved by maintaining the columnar structure through all stages of the calculation (see `this talk <https://youtu.be/jvt4v2LTGK0>`_ and `this paper <https://arxiv.org/abs/1711.01229>`_).

The OAMap toolkit implements an Object Array Mapping in Python. Object Array Mappings, by analogy with Object Relational Mappings (ORMs) are one-to-one relationships between conceptual objects and physical arrays. You can write functions that appear to be operating on ordinary Python objects— lists, tuples, class instances— but are actually being performed on low-level, contiguous buffers (Numpy arrays). The result is fast processing of large, complex datasets with a low memory footprint.

OAMap has two primary modes: (1) pure-Python object proxies, which pretend to be Python objects but actually access array data on demand, and (2) bare-metal bytecode compiled by `Numba <http://numba.pydata.org/>`_. The pure-Python form is good for low-latency, exploratory work, while the compiled form is good for high throughput. They are seamlessly interchangeable: when a Python object enters a Numba-compiled function, it switches to the compiled form and switches back when it leaves. You can, for instance, do a fast search in compiled code and examine the results more fully by hand.

Any columnar file format or database can be used as a data source: OAMap can get arrays of data from any dict-like object (Python object implementing ``__getitem__``), even in compiled code. Backends to ROOT, Parquet, and HDF5 are included, as well as a Python ``shelve`` alternative. Storing and accessing a complete dataset, including metadata, requires no more infrastructure than a collection of named arrays. (Data types are encoded in the names, values in the arrays.) OAMap is intended as a middleware layer above file formats and databases but below a fully integrated analysis suite.

Demonstration
-------------

Installation
""""""""""""

Install OAMap like any other Python package:

.. code-block:: bash

    pip install oamap --user

or similar (use ``sudo``, ``virtualenv``, or ``conda`` if you wish).

Sample dataset
""""""""""""""

Download the `NASA Exoplanet Archive <https://exoplanetarchive.ipac.caltech.edu/>`_ in Parquet form:

.. code-block:: bash

    wget http://diana-hep.org/oamap/examples/planets.parquet

(or click `this link <http://diana-hep.org/oamap/examples/planets.parquet>`_ and "Save As..." if you wish).

Exploring data
""""""""""""""

Load the Parquet dataset with its ``open`` function. If you have a large set of Parquet files, you could pass a list or glob pattern (``*`` and ``?`` wildcards), because data are always loaded on demand.

.. code-block:: python

    >>> import oamap.source.parquet
    >>> stars = oamap.source.parquet.open("planets.parquet")
    >>> stars
    [<Record at index 0>, <Record at index 1>, <Record at index 2>, <Record at index 3>,
     <Record at index 4>, ...]

This ``stars`` object behaves like a Python list, and each element is a record (i.e. class instance or struct).

.. code-block:: python

    >>> stars[0].fields
    ['activity', 'age', 'color', 'dec', 'density', 'distance', 'ecliptic', 'gaia', 'galactic',
     'luminosity', 'mass', 'metallicity', 'name', 'num_amateur_lightcurves', 'num_general_lightcurves',
     'num_images', 'num_planets', 'num_radial_timeseries', 'num_spectra', 'num_timeseries',
     'num_transit_lightcurves', 'opticalband', 'parallax', 'photometry', 'planets', 'propermotion',
     'ra', 'radialvelocity', 'radius', 'rotational_velocity', 'spectraltype', 'surfacegravity',
     'temperature', 'update']
    # Where is the star on the sky (RA/Dec)?
    >>> stars[0].ra, stars[0].dec
    (293.12738, 42.320103)
    # How hot is it?
    >>> stars[0].temperature
    <Record at index 0>
    # Oh, that's another Record. What's inside of it?
    >>> stars[0].temperature.fields
    ['blend', 'hierr', 'lim', 'loerr', 'val']
    # Measurement errors! Okay, get the central value with asymmetric errors.
    >>> stars[0].temperature.val, stars[0].temperature.loerr, stars[0].temperature.hierr
    (6564.0, -198.42, 153.47)

The elements of a record can be other records, but they can also be other lists. Stars can have an arbitrary number of planets, so this dataset can't be expressed as a rectangular table without padding or duplication.

The first star has one planet

.. code-block:: python

    >>> stars[0].planets
    [<Record at index 0>]
    >>> stars[0].planets[0].fields
    ['angular_separation', 'density', 'discovery', 'discovery_method', 'eccentricity',
     'encyclopedia_link', 'equilibrium_temperature', 'explorer_link', 'has_astrometrical_variations',
     'has_binary', 'has_image', 'has_orbital_modulations', 'has_radial_velocity', 'has_timing_variations',
     'has_transits', 'hd_name', 'hip_name', 'impact_parameter', 'in_k2_data', 'in_kepler_data',
     'inclination', 'isolation_flux', 'letter', 'longitude_periastron', 'mass', 'mass_best', 'mass_sini',
     'name', 'num_notes', 'num_parameters', 'occultation_depth', 'orbital_period', 'periastron',
     'publication_date', 'radial_velocity', 'radius', 'ratio_planetdistance_starradius',
     'ratio_planetradius_starradius', 'reference_link', 'semimajor_axis', 'timesystem_reference',
     'transit_depth', 'transit_duration', 'transit_midpoint']
    # What's the planet's name?
    >>> stars[0].planets[0].name
    'Kepler-1239 b'
    # Is that like the star's name? (Yup.)
    >>> stars[0].name
    'Kepler-1239'
    # How was it discovered?
    >>> stars[0].planets[0].discovery_method
    'Transit'
    # Oh, it's a transit. That means it should have transit information.
    >>> stars[0].planets[0].transit_duration
    <Record at index 0>
    # Another record! These scientists like their measurement errors!
    >>> stars[0].planets[0].transit_duration.fields
    ['hierr', 'lim', 'loerr', 'val']
    >>> stars[0].planets[0].transit_duration.val, stars[0].planets[0].transit_duration.loerr, stars[0].planets[0].transit_duration.hierr
    (0.17783, -0.0042900001, 0.0042900001)
