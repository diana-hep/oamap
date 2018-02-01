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

OAMap has two primary modes: (1) pure-Python object proxies, which pretend to be Python objects but actually access array data on demand, and (2) bare-metal bytecode compiled by `Numba <http://numba.pydata.org/>`_. The pure-Python form is good for low-latency, exploratory work, while the compiled form is good for high throughput. They are seamlessly interchangeable: a Python proxy converts to the compiled form when it enters a Numba-compiled function and switches back when it leaves. You can, for instance, do a fast search in compiled code and examine the results more fully by hand.

Any columnar file format or database can be used as a data source: OAMap can get arrays of data from any dict-like object (Python object implementing ``__getitem__``), even in compiled code. Backends to ROOT, Parquet, and HDF5 are included, as well as a Python ``shelve`` alternative. Storing and accessing a complete dataset, including metadata, requires no more infrastructure than a collection of named arrays. (Data types are encoded in the names, values in the arrays.) OAMap is intended as a middleware layer above file formats and databases but below a fully integrated analysis suite.

Demonstration
-------------

Installation
""""""""""""

Install OAMap like any other Python package:

.. code-block:: bash

    pip install oamap --user

or similar (use ``sudo``, ``virtualenv``, or ``conda`` if you wish).

**Strict dependencies:**

- `python <http://docs.python-guide.org/en/latest/starting/installation/>`_ (2.6+, 3.4+)
- `numpy <https://scipy.org/install.html>`_

**Recommended dependencies:**

- `numba <http://numba.pydata.org/numba-doc/latest/user/installing.html>`_ to JIT-compile functions (requires LLVM, follow instructions)
- `thriftpy <https://pypi.python.org/pypi/thriftpy>`_ to read Parquet files (pure Python, pip is fine)
- `uproot <https://pypi.python.org/pypi/uproot/>`_ to read ROOT files (pure Python, pip is fine)
- `h5py <http://docs.h5py.org/en/latest/build.html>`_ to read HDF5 files (requires binary libraries; follow instructions)

**Optional dependencies:** (all are bindings to binaries that can be package-installed)

- `lz4 <https://anaconda.org/anaconda/lz4>`_ compression used by some ROOT and Parquet files
- `python-snappy <https://anaconda.org/anaconda/python-snappy>`_ compression used by some Parquet files
- `lzo <https://anaconda.org/anaconda/lzo>`_ compression used by some Parquet files
- `brotli <https://anaconda.org/conda-forge/brotli>`_ compression used by some Parquet files

Sample dataset #1: Parquet
""""""""""""""""""""""""""

Download the `NASA Exoplanet Archive <https://exoplanetarchive.ipac.caltech.edu/>`_ in Parquet form:

.. code-block:: bash

    wget http://diana-hep.org/oamap/examples/planets.parquet
    pip install thriftpy --user

(or click `this link <http://diana-hep.org/oamap/examples/planets.parquet>`_ and "Save As..." if you wish).

Parquet is a columnar data format intended for data with deeply nested structure.

Load the Parquet dataset with its ``open`` function. If you have a large set of Parquet files, you could pass a list or glob pattern (``*`` and ``?`` wildcards), even if the total dataset is enormous, because nothing is loaded until it is needed.

.. code-block:: python

    >>> import oamap.source.parquet
    >>> stars = oamap.source.parquet.open("planets.parquet")
    >>> stars
    [<Record at index 0>, <Record at index 1>, <Record at index 2>, <Record at index 3>,
     <Record at index 4>, ...]

Sample dataset #2: Numpy npz
""""""""""""""""""""""""""""

Alternatively, download the same dataset in Numpy form:

.. code-block:: bash

    wget http://diana-hep.org/oamap/examples/planets.npz

(or click `this link <http://diana-hep.org/oamap/examples/planets.npz>`_ and "Save As..." if you wish).

Numpy's npz format is intended for rectangular arrays, not deeply nested structure. However, OAMap bridges the gap. (Numpy is faster to load into OAMap than Parquet but the file size is larger, due to less aggressive packing.)

Load the Numpy dataset with its ``open`` function. If you have a large set of Numpy files, you could pass a list or glob pattern (``*`` and ``?`` wildcards), even if the total dataset is enormous, because nothing is loaded until it is needed.

.. code-block:: python

    >>> import oamap.source.npz
    >>> stars = oamap.source.npz.open("planets.npz")
    >>> stars
    [<Star at index 0>, <Star at index 1>, <Star at index 2>, <Star at index 3>,
     <Star at index 4>, ...]

Sample dataset #3: HDF5
"""""""""""""""""""""""

TODO

Sample dataset #4: ROOT
"""""""""""""""""""""""

TODO

Exploring the data
""""""""""""""""""

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

The first star has one planet.

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
    >>> (stars[0].planets[0].transit_duration.val, stars[0].planets[0].transit_duration.loerr,
    ...  stars[0].planets[0].transit_duration.hierr)
    (0.17783, -0.0042900001, 0.0042900001)

Here's a star with five planets:

.. code-block:: python

    >>> stars[258].planets
    [<Record at index 324>, <Record at index 325>, <Record at index 326>, <Record at index 327>,
     <Record at index 328>]
    >>> [x.name for x in stars[258].planets]
    ['HD 40307 b', 'HD 40307 c', 'HD 40307 d', 'HD 40307 f', 'HD 40307 g']
    >>> [x.discovery_method for x in stars[258].planets]
    ['Radial Velocity', 'Radial Velocity', 'Radial Velocity', 'Radial Velocity', 'Radial Velocity']

If you've been working through these examples, you might have noticed that the *first* time you look at an attribute, there's a time lag. The data-fetching granularity is one *column* (attribute array) at a time. Even though this dataset has hundreds of parameters, you don't suffer the cost of loading the parameters you're not interested in, but looking at the first star's temperature loads all the stars' temperatures (per partition/file).

One column at a time is probably the right granularity for you because you'll be analyzing all or most values of a few attributes. For instance, suppose you're interested in solar systems with extremes of orbital periods.

.. code-block:: python

    for star in stars:
        best_ratio = None
        for one in star.planets:
            for two in star.planets:
                if (one.orbital_period is not None and one.orbital_period.val is not None and
                    two.orbital_period is not None and two.orbital_period.val is not None):
                    ratio = one.orbital_period.val / two.orbital_period.val
                    if best_ratio is None or ratio > best_ratio:
                        best_ratio = ratio
        if best_ratio is not None:
            print(best_ratio)

If you're following these examples interactively, you'd have noticed that the lag occurred at the very beginning of the loop, when you asked for the first orbital period and got all of them.

Peeking at OAMap's internals, we can see which arrays are actually loaded.

.. code-block:: python

    >>> print("\n".join(stars._generator.loaded(stars._cache)))
    object-B
    object-E
    object-L-Fplanets-B
    object-L-Fplanets-E
    object-L-Fplanets-L-Forbital_period-M
    object-L-Fplanets-L-Forbital_period-Fval-M
    object-L-Fplanets-L-Forbital_period-Fval-Df4

The ``-B`` and ``-E`` arrays quantify list and sublist lengths, ``-M`` are for nullable fields (almost all of the exoplanets fields could be null, or ``None`` in the Python code), and ``-D`` is the numerical data. (Note: the listing above is from the Parquet file; the Numpy file differs only in that it preserved the record names.)

Peeking further behind the scenes, we can see that these really are Numpy arrays.

.. code-block:: python
    for name in stars._generator.loaded(stars._cache):
        print(name)
        print(stars._listofarrays[0][name])

    object-B
    [0]
    object-E
    [2660]
    object-L-NStar-Fplanets-B
    [   0    1    2 ... 3562 3565 3570]
    object-L-NStar-Fplanets-E
    [   1    2    3 ... 3565 3570 3572]
    object-L-NStar-Fplanets-L-NPlanet-Forbital_period-NValueAsymErr-M
    [   0    1    2 ... 3495 3496 3497]
    object-L-NStar-Fplanets-L-NPlanet-Forbital_period-NValueAsymErr-Fval-M
    [   0    1    2 ... 3487 3488 3489]
    object-L-NStar-Fplanets-L-NPlanet-Forbital_period-NValueAsymErr-Fval-Df4
    [ 5.19104    4.147876   3.5957696 ... 87.090195   4.425391  13.193242 ]

No objects were involved in the processing of this data.

The fact that the data are purely numerical makes it the perfect fit for Numba, which optimizes Pythonic number-crunching by compiling it with LLVM.

Try `installing Numba <http://numba.pydata.org/numba-doc/latest/user/installing.html>`_ and then running the code below. The ``@numba.njit`` decorator specifies that the function must be compiled before it runs and ``import oamap.compiler`` tells Numba how to compile OAMap types.

.. code-block:: python

    import numba
    import oamap.compiler    # crucial! loads OAMap extensions!
    
    @numba.njit
    def period_ratio(stars):
        out = []
        for star in stars:
            best_ratio = None
            for one in star.planets:
                for two in star.planets:
                    if (one.orbital_period is not None and one.orbital_period.val is not None and
                        two.orbital_period is not None and two.orbital_period.val is not None):
                        ratio = one.orbital_period.val / two.orbital_period.val
                        if best_ratio is None or ratio > best_ratio:
                            best_ratio = ratio
            if best_ratio is not None and best_ratio > 200:
                out.append(star)
        return out
    
    # The benefit of compiling is lost on a small dataset like this (compilation time ~ run time),
    # but I'm sure you can find a much bigger one.  :)
    >>> extremes = period_ratio(stars)
    # Now that we've filtered with compiled code, we can examine the outliers in Python.
    >>> extremes
    [<Record at index 284>, <Record at index 466>, <Record at index 469>, <Record at index 472>,
     <Record at index 484>, <Record at index 502>, <Record at index 510>, <Record at index 559>,
     <Record at index 651>, <Record at index 665>, <Record at index 674>, <Record at index 728>,
     <Record at index 1129>, <Record at index 1464>, <Record at index 1529>, <Record at index 1567>,
     <Record at index 1814>, <Record at index 1819>, <Record at index 1953>, <Record at index 1979>,
     <Record at index 1980>, <Record at index 2305>, <Record at index 2332>, <Record at index 2366>,
     <Record at index 2623>, <Record at index 2654>]
    # These are unusual solar systems (most don't have so many planets).
    >>> extremes[0].planets
    [<Record at index 384>, <Record at index 385>, <Record at index 386>, <Record at index 387>,
     <Record at index 388>, <Record at index 389>]
    # Indeed, the orbital period ratio for this one is 2205.0 / 5.75969.
    >>> [x.orbital_period.val for x in extremes[0].planets]
    [5.75969, 16.357, 49.748, 122.744, 604.67, 2205.0]
    # Including attributes that we didn't consider in the search.
    >>> [x.mass_best.val for x in extremes[0].planets]
    [0.0416, 0.0378, 0.0805, 0.0722, 0.0732, 0.2066]

The exploratory one-liners and the analysis functions you would write to study your data are similar to what they'd be if these were JSON or Python objects. However,

- the data are stored in a binary, columnar form, which minimizes memory use and streamlines data transfers from disk or network to memory to CPU cache);
- scans over the data can be compiled for higher throughput.

These two features speed up conventional workflows.

Unconventional workflows: columnar granularity
""""""""""""""""""""""""""""""""""""""""""""""

In the demonstration above, we downloaded the file we wanted to analyze. That required us to take all of the columns, including those we aren't interested in. Object-array mapping shifts the granular unit from a file that describes a complete dataset to its individual columns. Thus,

- columns do not need to be packaged together as files— they may be free-floating objects in an object store;
- the same columns may be used in different datasets— different versions, different structures, different filters— because datasets with substantial overlaps in content should not be allowed to waste memory.

To demonstrate this, we'll look at the same dataset with download-on-demand. We're using a simple HTTP server for this, but any key-value database or object store would work.

.. code-block:: python

    import numpy
    import io
    import codecs
    try:
        from urllib.request import urlopen   # Python 3
    except ImportError:
        from urllib2 import urlopen          # Python 2

    baseurl = "http://diana-hep.org/oamap/examples/planets/"

    # wrap the website as a dict-like object with a __getitem__ method
    class DataSource:
        def __getitem__(self, name):
            ### uncomment the following line to see how it works
            # print(name)
            try:
                return numpy.load(io.BytesIO(urlopen(baseurl + name + ".npy").read()))
            except Exception as err:
                raise KeyError(str(err))

    # download the dataset description
    remotefile = urlopen(baseurl + "dataset.json")

    # explicit utf-8 conversion required for Python 3
    remotefile = codecs.getreader("utf-8")(remotefile)

    # the dataset description tells OAMap which arrays (URLs) to fetch
    from oamap.schema import Dataset
    dataset = Dataset.fromjsonfile(remotefile)
    stars = dataset.schema(DataSource())

Now we can work with this dataset exactly as we did before. (I'm including the optional printouts from above.)

.. code-block:: python

    # object-B
    # object-E
    >>> stars
    [<Star at index 0>, <Star at index 1>, <Star at index 2>, <Star at index 3>, <Star at index 4>, ...,
     <Star at index 2655>, <Star at index 2656>, <Star at index 2657>, <Star at index 2658>,
     <Star at index 2659>]
    >>> stars[0].ra, stars[0].dec
    # object-L-NStar-Fra-Df4
    # object-L-NStar-Fdec-Df4
    (293.12738, 42.320103)
    >>> stars[258].planets
    # object-L-NStar-Fplanets-B
    # object-L-NStar-Fplanets-E
    [<Planet at index 324>, <Planet at index 325>, <Planet at index 326>, <Planet at index 327>,
     <Planet at index 328>]
    >>> [x.name for x in stars[258].planets]
    # object-L-NStar-Fplanets-L-NPlanet-Fname-NUTF8String-B
    # object-L-NStar-Fplanets-L-NPlanet-Fname-NUTF8String-E
    # object-L-NStar-Fplanets-L-NPlanet-Fname-NUTF8String-L-Du1
    [u'HD 40307 b', u'HD 40307 c', u'HD 40307 d', u'HD 40307 f', u'HD 40307 g']
    >>> period_ratio(stars)
    # object-L-NStar-Fplanets-L-NPlanet-Forbital_period-NValueAsymErr-Fval-M
    # object-L-NStar-Fplanets-L-NPlanet-Forbital_period-NValueAsymErr-Fval-Df4
    # object-L-NStar-Fplanets-L-NPlanet-Forbital_period-NValueAsymErr-M
    [<Star at index 284>, <Star at index 466>, <Star at index 469>, <Star at index 472>, <Star at index 484>,
     <Star at index 502>, <Star at index 510>, <Star at index 559>, <Star at index 651>, <Star at index 665>,
     <Star at index 674>, <Star at index 728>, <Star at index 1129>, <Star at index 1464>,
     <Star at index 1529>, <Star at index 1567>, <Star at index 1814>, <Star at index 1819>,
     <Star at index 1953>, <Star at index 1979>, <Star at index 1980>, <Star at index 2305>,
     <Star at index 2332>, <Star at index 2366>, <Star at index 2623>, <Star at index 2654>]

Scope of computability
""""""""""""""""""""""


