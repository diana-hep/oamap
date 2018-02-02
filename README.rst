OAMap: Object-Array Mapping
===========================

.. image:: https://travis-ci.org/diana-hep/oamap.svg?branch=master
   :target: https://travis-ci.org/diana-hep/oamap

Introduction
------------

Data analysts are often faced with a choice between speed and flexibility. Tabular data, such as SQL tables, can be processed rapidly enough for a truly interactive analysis session, but hierarchically nested formats, such as JSON, are better at representing relationships in complex data models. In some domains (such as particle physics), we want to perform calculations on JSON-like structures at the speed of SQL.

The key to high throughput on large datasets, particularly ones with more attributes than are accessed in a single pass, is laying out the data in "columns." All values of an attribute should be contiguous on disk or memory because data are paged from one cache to the next in locally contiguous blocks. The `ROOT <https://root.cern/>`_ and `Parquet <http://parquet.apache.org/>`_ file formats represent JSON-like data in columns on disk, but these data are usually deserialized into objects for processing in memory. Higher performance can be achieved by maintaining the columnar structure through all stages of the calculation (see `this talk <https://youtu.be/jvt4v2LTGK0>`_ and `this paper <https://arxiv.org/abs/1711.01229>`_).

The OAMap toolkit implements an Object Array Mapping in Python. Object Array Mappings, by analogy with Object Relational Mappings (ORMs) are one-to-one relationships between conceptual objects and physical arrays. You can write functions that appear to be operating on ordinary Python objects— lists, tuples, class instances— but are actually being performed on low-level, contiguous buffers (Numpy arrays). The result is fast processing of large, complex datasets with a low memory footprint.

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

Demonstration
-------------

Sample dataset #1: Parquet
""""""""""""""""""""""""""

Download the `NASA Exoplanet Archive <https://exoplanetarchive.ipac.caltech.edu/>`_ in `Parquet form <http://diana-hep.org/oamap/examples/planets.parquet>`_.

.. code-block:: bash

    wget http://diana-hep.org/oamap/examples/planets.parquet
    pip install thriftpy --user

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

Alternatively, download the same dataset in `Numpy form <http://diana-hep.org/oamap/examples/planets.npz>`_.

.. code-block:: bash

    wget http://diana-hep.org/oamap/examples/planets.npz

Numpy's npz format is intended for rectangular arrays, not deeply nested structure. However, OAMap effectively adds this feature. (Numpy is faster to load into OAMap but results in a larger file than Parquet, due to less aggressive packing.)

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

    >>> stars
    [<Record at index 0>, <Record at index 1>, <Record at index 2>, <Record at index 3>,
     <Record at index 4>, ...]
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

If you've been working through these examples, you might have noticed that the *first* time you look at an attribute, there's a time lag. The data-fetching granularity is one *column* (attribute array) at a time. Even though the objects in this dataset have hundreds of attributes, you don't suffer the cost of loading the attributes you're not interested in, but looking at the first star's temperature loads all the stars' temperatures (per file).

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

    >>> for name in stars._generator.loaded(stars._cache):
    ...     print(stars._listofarrays[0][name])
    [0]
    [2660]
    [   0    1    2 ... 3562 3565 3570]
    [   1    2    3 ... 3565 3570 3572]
    [   0    1    2 ... 3495 3496 3497]
    [   0    1    2 ... 3487 3488 3489]
    [ 5.19104    4.147876   3.5957696 ... 87.090195   4.425391  13.193242 ]

No objects were involved in the processing of the data.

The fact that the data are in a purely numerical form makes it a perfect fit for Numba, which optimizes number-crunching by compiling Python functions with LLVM.

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

- columns do not need to be packaged together as files— they may be free-floating objects in a key-value database or object store;
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
    from oamap.schema import *
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
    ['HD 40307 b', 'HD 40307 c', 'HD 40307 d', 'HD 40307 f', 'HD 40307 g']
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

We can even modify the dataset without touching all of its elements. For instance, suppose we want to give each star an id number:

.. code-block:: python

    # create a data source that effectively merges the array sets
    class DataSource2:
        def __init__(self, arrays, fallback):
            self.arrays = arrays
            self.fallback = fallback
        def __getitem__(self, name):
            try:
                return self.arrays[name]
            except KeyError:
                return self.fallback[name]

    # modify the schema by adding a primitive (numerical) field
    >>> schema = dataset.schema
    >>> schema.content["id"] = Primitive(int, data="id-array")

    # create a new dataset with the new schema and new source
    >>> source = DataSource2({"id-array": numpy.arange(len(stars), dtype=int)}, DataSource())
    >>> stars_v2 = schema(source)

    # the new dataset has the new field and the old one doesn't, but they share 99% of the data
    >>> stars_v2[0].id
    0
    >>> stars_v2[100].id
    100
    >>> stars_v2[-1].id
    2659
    >>> stars[0].id
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "oamap/proxy.py", line 340, in __getattr__
        raise AttributeError("{0} object has no attribute {1}".format(repr("Record" if
            self._generator.name is None else self._generator.name), repr(field)))
    AttributeError: 'Star' object has no attribute 'id'

Schemas/data types
------------------

Columnar datasets must be defined by a schema and compiled functions must have static data types, so all data in OAMap has a schema. As you've seen in the previous example, the schemas are very fluid: you're not locked into an early choice of schema.

You can examine the schema of any list or record through its ``schema`` property:

.. code-block:: python

    >>> stars.schema.show()

For a large dataset like the exoplanets, be prepared for pages of output.

The schema expresses the nested structure of the data and optionally the names of the arrays to fetch (overriding a default naming convention, derived from the schema structure). Schemas can also document the data and carry arbitrary (JSON) metadata.

Schemas are defined by seven generators: **Primitive**, **List**, **Union**, **Record**, **Tuple**, **Pointer**, and **Extension**, which together form a fairly complete programming environment.

Primitive
"""""""""

Primitives are fixed-width, concrete types such as booleans, numbers, and fixed-size byte strings (e.g. 6-byte MAC addresses or 16-byte UUIDs). The scope will include anything describable by a `Numpy dtype <https://docs.scipy.org/doc/numpy/reference/generated/numpy.dtype.html>`_, though non-trivial dtype shapes (to describe fixed-dimension tensors) and names (to describe non-columnar, flat records) are not implemented yet.

.. code-block:: python

    >>> from oamap.schema import *
    >>> schema = List(Primitive(int, data="p"), starts="b", stops="e")
    >>> obj = schema({"p": [1, 2, 3, 4, 5], "b": [0], "e": [5]})
    >>> obj
    [1, 2, 3, 4, 5]

.. code-block:: python

    >>> schema = List(Primitive("S4"))
    >>> obj = schema.fromdata(["one", "two", "three", "four", "five"])
    >>> obj
    [b'one', b'two', b'thre', b'four', b'five']

Note that "three" is truncated (and the rest are implicitly padded) because the Numpy dtype, ``"S4"`` is 4-byte. See the extension type (below) for a better way to make strings.

List
""""

Lists are arbitrary length collections of any other type. Unlike dynamically typed Python, the contents of a list must all be the same type ("homogeneous"), though unions (below) loosen that requirement.

.. code-block:: python

    >>> schema = List(List("int"))   # shorthand string "int" for Primitive("int")
    >>> obj = schema.fromdata([[1, 2, 3], [], [4, 5]])
    >>> for n, x in obj._arrays.items():
    ...     print(n, x)
    object-B [0]
    object-E [3]
    object-L-B [0 3 3]
    object-L-E [3 3 5]
    object-L-L-Di8 [1 2 3 4 5]
    >>> obj
    [[1, 2, 3], [], [4, 5]]

is a list of lists and

.. code-block:: python

    >>> schema = List(Tuple(["int", "float"]))
    >>> obj = schema.fromdata([(1, 1.1), (2, 2.2), (3, 3.3)])
    >>> for n, x in obj._arrays.items():
    ...     print(n, x)
    object-B [0]
    object-E [3]
    object-L-F0-Di8 [1 2 3]
    object-L-F1-Df8 [1.1 2.2 3.3]
    >>> obj
    [(1, 1.1), (2, 2.2), (3, 3.3)]

is a list of tuples.

Union
"""""

Unions represent data that may be one of a given set of types ("`sum types <https://en.wikipedia.org/wiki/Tagged_union>`_" in type theory). For instance, the elements of the following list could *either* be a floating point number *or* be a list of integers:

.. code-block:: python

    >>> schema = List(Union(["float", List("int")]))
    >>> obj = schema({"object-B": [0],                     # beginning of outer list
                      "object-E": [3],                     # end of outer list
                      "object-L-T": [0, 1, 0],             # tags: possibility 0 (float) or 1 (list of int)?
                      "object-L-O": [0, 0, 1],             # offsets: where to find the compacted contents
                      "object-L-U0-Df8": [1.1, 3.3],       # data for possibility 0 (floats)
                      "object-L-U1-B": [0],                # beginnings of lists for possibility 1
                      "object-L-U1-E": [4],                # ends of lists for possibility 1
                      "object-L-U1-L-Di8": [1, 2, 3, 4]})  # list content for possibility 1 (ints)
    >>> obj
    [1.1, [1, 2, 3, 4], 3.3]

Unions can emulate a popular object-oriented concept: class inheritance. We can make a list of electrons (which have charge) and photons (which don't) as a union of the two types of records.

.. code-block:: python

    >>> schema = List(Union([
    ...     Record(name="Electron", fields={"energy": "float", "charge": "int"}),
    ...     Record(name="Photon",   fields={"energy": "float"})]))
    ... 
    >>> obj = schema.fromdata([
    ...     {"energy": 1.1, "charge":  1},
    ...     {"energy": 2.2, "charge": -1},
    ...     {"energy": 3.3},
    ...     {"energy": 4.4, "charge": -1},
    ...     {"energy": 5.5}
    ...     ])
    ... 
    >>> obj
    [<Electron at index 0>, <Electron at index 1>, <Photon at index 0>, <Electron at index 2>,
     <Photon at index 1>]
    >>> for n, x in obj._arrays.items():
    ...     print(n, x)
    ... 
    object-B [0]
    object-E [5]
    object-L-T [0 0 1 0 1]
    object-L-O [0 1 0 2 1]
    object-L-U0-NElectron-Fenergy-Df8 [1.1 2.2 4.4]
    object-L-U0-NElectron-Fcharge-Di8 [ 1 -1 -1]
    object-L-U1-NPhoton-Fenergy-Df8 [3.3 5.5]

Record
""""""

Records represent data that contain a set of fields— names that map to types ("`product types <https://en.wikipedia.org/wiki/Product_type>`_" in type theory).

You've seen several examples of record types, so here's one drawn from the exoplanets:

.. code-block:: python

    >>> stars.schema.content["planets"].content["discovery"].show()
    Record(
      name = 'Discovery',
      fields = {
        'facility': Pointer(
          doc = 'Name of facility of planet discovery observations',
          target = List(
            name = 'UTF8String',
            content = Primitive(dtype('uint8'))
          )
        ),
        'instrument': List(
          name = 'UTF8String',
          doc = 'Name of instrument of planet discovery observations',
          content = Primitive(dtype('uint8'))
        ),
        'link': List(
          name = 'UTF8String',
          doc = 'Reference name for discovery publication',
          content = Primitive(dtype('uint8'))
        ),
        'locale': Pointer(
          doc = 'Location of observation of planet discovery (Ground or Space)',
          target = List(
            name = 'UTF8String',
            content = Primitive(dtype('uint8'))
          )
        ),
        'telescope': List(
          name = 'UTF8String',
          doc = 'Name of telescope of planet discovery observations',
          content = Primitive(dtype('uint8'))
        ),
        'year': Primitive(dtype('int32'), doc='Year the planet was discovered')
      })

Tuple
"""""

Tuples are like records, but their content fields are numbered, rather than named. They are more like records than lists because

- lists may have any length, but the tuple length is fixed by the schema;
- all elements of a list must have the same type ("homogeneous"), but each element of a tuple may have a different type ("heterogeneous").

.. code-block:: python

    >>> schema = List(Tuple(["int", "float", List("int")]))
    >>> obj = schema.fromdata([(1, 1.1, [1, 2, 3]), (2, 2.2, []), (3, 3.3, [4, 5])])
    >>> obj
    [(1, 1.1, [1, 2, 3]), (2, 2.2, []), (3, 3.3, [4, 5])]

Pointer
"""""""

Pointers connect parts of the object to form trees and graphs, and they reduce memory use by minimizing the number of times a large, complex object must be represented.

OAMap pointers are similar to pointers in a language like C, in that they reference an object by specifying its location with an integer, with two exceptions.

1. The address is an array index, not a native memory address. This allows OAMap to be portable.
2. OAMap pointers are `bounded pointers <https://en.wikipedia.org/wiki/Bounded_pointer>`_, limited to a specified "target."

Pointers may be used in three topologies: (1) to point to another object in the same schema, but not its own parent, (2) to point at its parent, creating a loop (the only way to make arbitrary depth trees or graphs in OAMap), and (3) to point to an external object.

The first case is useful for provenance, so that derived collections can refer to their sources (e.g. reconstructed particles point to their raw measurements; tracks and showers in particle physics).

.. code-block:: python

    >>> schema = Record({"points": List(Tuple(["int", "int"])),
    ...                  "line": List(Pointer(None))})
    >>> schema.fields["line"].content.target = schema.fields["points"].content
    >>> schema.show()
    Record(
      fields = {
        'points': List(
          content = #0: Tuple(
            types = [
              Primitive(dtype('int64')),
              Primitive(dtype('int64'))
            ])
        ),
        'line': List(
          content = Pointer(
            target = #0
          )
        )
      })
    >>> points = [(0, 0), (0, 1), (1, 1), (1, 0)]
    >>> line = [points[0], points[2], points[1]]
    >>> obj = schema.fromdata({"points": points, "line": line})
    >>> for n, x in obj._arrays.items():
    ...     print n, x
    ... 
    object-Fline-B [0]
    object-Fline-E [3]
    object-Fpoints-B [0]
    object-Fpoints-E [4]
    object-Fpoints-L-F0-Di8 [0 0 1 1]
    object-Fpoints-L-F1-Di8 [0 1 1 0]
    object-Fline-L-P-object-Fpoints-L [0 2 1]  # point 0, 2, then 1

The second case builds trees and graphs.

.. code-block:: python

    >>> schema = Record(
    ...     name = "Tree",
    ...     fields = dict(
    ...         label = "float",
    ...         children = List(Pointer(None))
    ...     ))
    ... 
    >>> schema.fields["children"].content.target = schema
    >>> schema.show()
    #0: Record(
      name = 'Tree',
      fields = {
        'label': Primitive(dtype('float64')),
        'children': List(
          content = Pointer(
            target = #0
          )
        )
      })
    >>> obj = schema.fromdata(
    ...     {"label": 1.1,                                     # 1.1
    ...      "children": [                                     #  |
    ...          {"label": 2.2,                                #  ├── 2.2
    ...           "children": [                                #  |    |
    ...               {"label": 4.4,                           #  │    ├── 4.4
    ...                "children": [                           #  │    │    |
    ...                    {"label": 7.7, "children": []}      #  │    │    └── 7.7
    ...                            ]},                         #  |    |
    ...               {"label": 5.5,                           #  │    └── 5.5
    ...                "children": [                           #  |         |
    ...                    {"label": 8.8, "children": []}      #  │         └── 8.8
    ...                            ]}                          #  |
    ...                       ]},                              #  |
    ...          {"label": 3.3,                                #  └── 3.3
    ...           "children": [                                #       |
    ...               {"label": 6.6, "children": []}           #       └── 6.6
    ...                       ]}
    ...                  ]})
    >>> obj
    <Tree at index 0>
    >>> obj.children[0].children[0].label
    2.2

The third case effectively turns contained data into enumeration constants, good for repeated quantities (such as the strings in the exoplanets dataset).

.. code-block:: python

    # the schema for discovery_method is a pointer to strings, rather than strings directly
    >>> stars.schema.content["planets"].content["discovery_method"].show()
    Pointer(
      positions = 'discovery_method-P',
      doc = 'Discovery Method',
      target = List(
        starts = 'discovery_method-X-NUTF8String-B',
        stops = 'discovery_method-X-NUTF8String-E',
        name = 'UTF8String',
        content = Primitive(dtype('uint8'), data='discovery_method-X-NUTF8String-L-Du1')
      )
    ) 

    # string data consists exclusively of _unique_ strings
    >>> stars._listofarrays[0]["discovery_method-X-NUTF8String-L-Du1"].tostring()
    b"""TransitRadial VelocityImagingMicrolensingEclipse Timing VariationsPulsar TimingTransit Timi
        ng VariationsOrbital Brightness ModulationPulsation Timing VariationsAstrometry"""

    # and the discovery method string for 3572 planets are referred to by pointer integers
    >>> stars._listofarrays[0]["discovery_method-P"][:300]
    array([0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 2, 0, 0, 0, 0, 0, 0,
           0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 1, 1,
           0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
           0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 2, 1, 1,
           1, 3, 0, 1, 0, 0, 1, 1, 0, 1, 2, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0,
           0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
           0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0,
           0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
           0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0,
           0, 0, 0, 1, 1, 4, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0,
           0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0,
           0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
           0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 1, 0, 0,
           0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], dtype=int32)

This concept maps nicely onto Parquet's dictionary encoding, so Parquet dictionaries are presented as OAMap pointers.

Extensions and names
""""""""""""""""""""

Extensions allow the six content-oriented type generators to be interpreted in an open-ended variety of ways. For instance, we haven't discussed strings as a distinct type, but strings are just lists of characters, and characters are primitives. Instead of introducing a string type, we allow lists of characters with a special name to be interpreted as strings.

>>> schema = List(List(name="UTF8String", content="uint8"))
>>> obj = schema.fromdata(["hello there", "you guys"])
>>> obj
['hello there', 'you guys']
>>> for n, x in obj._arrays.items():
...     print(n, x)
... 
object-B [0]
object-E [2]
object-L-NUTF8String-B [ 0 11]
object-L-NUTF8String-E [11 19]
object-L-NUTF8String-L-Du1 [104 101 108 108 111  32 116 104 101 114 101 121
                            111 117  32 103 117 121 115]
>>> obj._arrays["object-L-NUTF8String-L-Du1"].tostring()
b'hello thereyou guys'

Extension libraries can be specified at runtime (``oamap.extension.common`` is the default, which includes the most common types) and are pattern-matched to schemas. All specified schema attributes are used in the matching, but name is the most significant discriminator.

Nullability
"""""""""""

Every data type, at every level, may be "nullable." A nullable value may be ``None`` at runtime, and the missing data are identified by masking arrays that also serve as offset arrays.

.. code-block:: python

    >>> schema = List(List(Primitive(int, nullable=True), nullable=True))

    >>> obj = schema.fromdata([[1, None, 3], [], [4, 5]])
    >>> for n, x in obj._arrays.items():
    ...     print n, x
    object-B [0]
    object-E [3]
    object-L-M [0 1 2]
    object-L-B [0 3 3]
    object-L-E [3 3 5]
    object-L-L-M [ 0 -1  1  2  3]
    object-L-L-Di8 [1 3 4 5]

    >>> obj = schema.fromdata([None, [], [4, 5]])
    >>> for n, x in obj._arrays.items():
    ...     print n, x
    object-B [0]
    object-E [3]
    object-L-M [-1  0  1]
    object-L-B [0 0]
    object-L-E [0 2]
    object-L-L-M [0 1]
    object-L-L-Di8 [4 5]

Using the flexibility of the mask-offset, the missing values may be skipped in the data (as above) or filled with placeholders (as in `Apache Arrow <https://arrow.apache.org/>`_).

Datasets and partitions
-----------------------

In the examples above, we created objects on the fly for small, handwritten schemas. Not all of these were lists, though most data processing is performed on some kind of list, often on subsequences in parallel, and often on datasets that are too large to fit into memory. We must be able to split lists up into large chunks, called partitions, to control when they're operated upon and by whom.

A large schema can be wrapped up in a dataset, which we used in the exoplanet-from-HTTP example.

.. code-block:: python

    >>> dataset.show()
    Dataset(
      prefix = 'object',
      delimiter = '-',
      metadata = {'source': 'https://exoplanetarchive.ipac.caltech.edu/'},
      schema = List(
        content = Record(
          name = 'Star',
          fields = {
            ...
          })
      )
    )

If the dataset's schema is a list, we can specify a partitioning in the dataset description. This partitioning is a rule specifying a naming convention or an explicit lookup table to map a column name and a partition number to an array name. OAMap proxies (including those in a Numba-compiled function) load one partition at a time, flushing the previous partition from memory. More advanced processors may use partition numbers to distribute a job.

To a user, processing a whole dataset can be as simple as

.. code-block:: python

    >>> import numba
    >>> import oamap.compiler
    >>> import oamap.source.root
    >>> events = oamap.source.root.open("particle_physics_data/*.root")

    # turn off Python's GIL in compiled code
    >>> @numpy.njit(nogil=True)
    >>> def complex_function(events):
    ...     # action to perform on one partition of events
    ... 
    >>> complex_function(events)

to load each partition serially, holding only one partition in memory at a time, or

.. code-block:: python

    >>> from concurrent.futures import ThreadPoolExecutor
    >>> executor = ThreadPoolExecutor(16)
    >>> executor.map(complex_function, events.partitions)

to run them in parallel, holding as many as 16 partitions in memory at a time.
