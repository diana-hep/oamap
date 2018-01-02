OAMap
=====

.. image:: https://travis-ci.org/diana-hep/oamap.svg?branch=master
   :target: https://travis-ci.org/diana-hep/oamap

Tools for analyzing hierarchically nested, columnar data without deserialization.

Introduction
------------

Data analysts are often faced with a choice between speed and flexibility. Tabular data, such as SQL tables, can be processed rapidly enough for a truly interactive analysis session, but hierarchically nested data, such as JSON, is better at representing relationships within complex data models. In some domains (such as particle physics), we want to perform calculations on JSON-like structures at the speed of SQL.

The key to high throughput for large datasets, particularly ones with many more attributes than are typically accessed in a single pass, is laying out the data in "columns." All values of an attribute should be contiguous in disk or memory because data are paged from one cache to the next in locally contiguous blocks. The `ROOT <https://root.cern/>`_ and `Parquet <http://parquet.apache.org/>`_ file formats represent hierarchically nested data in a columnar form on disk, and `Apache Arrow <https://arrow.apache.org/>`_ is an emerging standard for sharing hierarchically nested data in memory. However, data from these formats are usually deserialized into conventional data structures before processing, which limits performance (see `this talk <https://youtu.be/jvt4v2LTGK0>`_ and `this paper <https://arxiv.org/abs/1711.01229>`_).

OAMap is a toolset for computing arbitrary functions on hierarchical, columnar data without deserialization. The name stands for Object Array Mapping, in analogy with the `Object Relational Mapping (ORM) <https://en.wikipedia.org/wiki/Object-relational_mapping>`_ interface to some databases. Users (data analysts) write functions on JSON-like objects that OAMap compiles into operations on the underlying arrays, similar to the way that ORM converts object-oriented code into SQL. The difference is that mapping objects to non-relational arrays permits bare-metal performance (giving up some traditional database features).

OAMap is a Python library on top of which high-level analysis software may be built. It focuses on mapping an object-oriented view of data onto columnar arrays. `Numpy <http://www.numpy.org/>`_ is OAMap's only strict dependency, though OAMap objects are also implemented as `Numba extensions <http://numba.pydata.org/numba-doc/dev/extending/index.html>`_, so they may be used in `Numba's <http://numba.pydata.org/>`_ JIT-compiled functions at speeds that match or exceed hand-written C code. OAMap is unopinionated about the source of its columnar arrays, allowing for a variety of backends. See the walkthrough (below) for more.

Also, a similar object array mapping could be implemented in any language— Python was chosen only for its popularity among data analysts.

Walkthrough
-----------

Installation
""""""""""""

Start by installing OAMap:

.. code-block:: bash

    pip install oamap --user

or similar (use ``sudo``, ``virtualenv``, or ``conda`` if you wish). Now you should be able to import the package in Python:

.. code-block:: python

    from oamap.schema import *

Sample dataset
""""""""""""""

For this walkthrough, you'll be working with a real dataset, the `NASA Exoplanet Archive <https://exoplanetarchive.ipac.caltech.edu/>`_. As an illustration of columnar data access, you can start working with it without fully downloading it. Copy-paste the following to get a schema.

.. code-block:: python

    from oamap.schema import *

    import codecs
    try:
        from urllib.request import urlopen   # Python 3
    except ImportError:
        from urllib2 import urlopen          # Python 2

    baseurl = "http://diana-hep.org/oamap/examples/planets/"

    # download the schema from our website
    remotefile = urlopen(baseurl + "schema.json")

    # explicit utf-8 conversion required for Python 3
    remotefile = codecs.getreader("utf-8")(remotefile)

    schema = Schema.fromjsonfile(remotefile)

If you're brave, try ``schema.show()`` to see its hundreds of attributes. It represents a list of stars that are known to have planets; each star has attributes like distance, position on the sky, mass, and temperature, and each of those attributes has a central value, asymmetric uncertainties, and limit flags, packaged in record structures. Each star also has a list of planets, with its own attributes, such as orbital period, mass, discovery method, etc. Some of these, like discovery method, are strings, some are numbers, and most are "nullable," meaning that they could be missing (unmeasured or otherwise unavailable).

You can view the data as nested Python objects by providing a dict of arrays to the schema. (The ``DataSource`` below makes the website act like a Python dict.)

.. code-block:: python

    import io
    import numpy

    class DataSource:
        def __getitem__(self, name):
            try:
                return numpy.load(io.BytesIO(urlopen(baseurl + name + ".npy").read()))
            except Exception as err:
                raise KeyError(str(err))

    stars = schema(DataSource())

This ``stars`` object is a list of ``Star`` records with nested ``planets``. If you print it on the Python command line (or Jupyter notebook, whatever you're using), you'll see that there are 2660 stars, though you have not downloaded hundreds of attributes for thousands of stars. (You'd notice the lag.)

Exploring the data interactively
""""""""""""""""""""""""""""""""

To poke around the data, use ``dir(stars[0])``, ``stars[0]._fields`` or tab-completion to see what fields are available. One such field is ``planets``.

.. code-block:: python

    stars[0].planets
    # [<Planet at index 0>]

    stars[258].planets
    # [<Planet at index 324>, <Planet at index 325>, <Planet at index 326>, <Planet at index 327>,
    # <Planet at index 328>]

    stars[0].name
    # 'Kepler-1239'
    stars[0].planets[0].name
    # 'Kepler-1239 b'

    stars[258].name
    # 'HD 40307'
    [x.name for x in stars[258].planets]
    # ['HD 40307 b', 'HD 40307 c', 'HD 40307 d', 'HD 40307 f', 'HD 40307 g']

    stars[0].planets[0].orbital_period.val
    # 5.19104
    stars[0].planets[0].orbital_period.hierr
    # 2.643e-05
    stars[0].planets[0].orbital_period.loerr
    # -2.643e-05
    stars[0].planets[0].orbital_period.lim
    # False

    stars[0].planets[0].discovery_method
    # 'Transit'
    stars[0].planets[0].transit_duration.val
    # 0.17783

    [x.discovery_method for x in stars[258].planets]
    # ['Radial Velocity', 'Radial Velocity', 'Radial Velocity', 'Radial Velocity', 'Radial Velocity']
    [x.transit_duration for x in stars[258].planets]
    # [None, None, None, None, None]

    from collections import Counter
    discovery_method = Counter()
    for star in stars:
        for planet in star.planets:
            discovery_method[planet.discovery_method] += 1

    discovery_method
    # Counter({'Transit': 2774, 'Radial Velocity': 662, 'Microlensing': 53, 'Imaging': 44,
    #          'Transit Timing Variations': 15, 'Eclipse Timing Variations': 9, 'Pulsar Timing': 6,
    #          'Orbital Brightness Modulation': 6, 'Pulsation Timing Variations': 2,
    #          'Astrometry': 1})

Object array mapping
""""""""""""""""""""

In short, the dataset appears to be a nested Python object. However, it's actually a set of Numpy arrays. One hint that you may have noticed is the time lag whenever you requested a *new* attribute, such as star name or planet orbital period, the first time you accessed it from *any* star or planet. This is because the request triggered a download of the attribute array, which contains values for all stars and planets at once, through our ``DataSource``.

To peek behind the scenes and see these arrays, look at

.. code-block:: python

    stars._cache.arraylist

The slots that are filled with arrays are the ones you've viewed. Note that these arrays don't all have the same length, as they would if this dataset were a rectangular table. There are more planets than stars,

.. code-block:: python

    len(stars)
    # 2660
    sum(len(x.planets) for x in stars)
    # 3572

so there should be more values of planetary eccentricity than stellar temperature, for instance. But some of those fields are missing values, so there aren't even the same number of planetary attributes.

.. code-block:: python

    eccentricity_count = 0                                  # one planetary attribute
    for star in stars:
        for planet in star.planets:
            if planet.eccentricity is not None:             # nullable records can be None
                if planet.eccentricity.val is not None:     # nullable floats can be None
                    eccentricity_count += 1
    eccentricity_count
    # 1153

    semimajor_axis_count = 0                                # another planetary attribute
    for star in stars:
        for planet in star.planets:
            if planet.semimajor_axis is not None:           # nullable records can be None
                if planet.semimajor_axis.val is not None:   # nullable floats can be None
                    semimajor_axis_count += 1
    semimajor_axis_count
    # 2076

    d = DataSource()
    eccentricity_array = d["object-L-NStar-Fplanets-L-NPlanet-Feccentricity-NValueAsymErr-Fval"]
    # array([ 0.   ,  0.   ,  0.05 , ...,  0.   ,  0.12 ,  0.062], dtype=float32)
    semimajor_axis_array = d["object-L-NStar-Fplanets-L-NPlanet-Fsemimajor_axis-NValueAsymErr-Fval"]
    # array([ 0.115     ,  0.01855   ,  0.26899999, ...,  0.359     ,
    #         0.056     ,  0.116     ], dtype=float32)

    len(eccentricity_array), len(semimajor_axis_array)
    # (1153, 2076)

Missing values are not padded— these arrays contain exactly as much data as necessary to reconstruct the objects.

Repeated strings can also bloat a dataset, so they're often replaced with enumeration constants— integers whose meaning is either encoded in the schema or in external documentation. OAMap has a pointer data type that naturally provides self-documenting enumeration constants. Consider the difference between the planet's ``name`` field, which has no expected duplicates:

.. code-block:: python

    schema.content.fields["planets"].content.fields["name"].show()
    # List(
    #   name = u'UTF8String', 
    #   content = Primitive(dtype('uint8'))
    # )

    len(d["object-L-NStar-Fplanets-L-NPlanet-Fname-NUTF8String-L"])
    # 41122

    d["object-L-NStar-Fplanets-L-NPlanet-Fname-NUTF8String-L"][:100].tostring()
    # 'Kepler-1239 bKepler-1238 bKepler-618 bKepler-1231 bKepler-1230 bKepler-1233 bKepler-1232 bHD 4308 bK'

and the ``discovery_method`` field, which has many duplicates (it's essentially a category label):

.. code-block:: python

    schema.content.fields["planets"].content.fields["discovery_method"].show()
    # Pointer(
    #   target = List(
    #     name = u'UTF8String', 
    #     content = Primitive(dtype('uint8'))
    #   )
    # )

    len(d["object-L-NStar-Fplanets-L-NPlanet-Fdiscovery_method-X-NUTF8String-L"])
    # 170

    d["object-L-NStar-Fplanets-L-NPlanet-Fdiscovery_method-X-NUTF8String-L"].tostring()
    # 'TransitRadial VelocityImagingMicrolensingEclipse Timing VariationsPulsar TimingTransit Timing
    #  VariationsOrbital Brightness ModulationPulsation Timing VariationsAstrometry'

    d["object-L-NStar-Fplanets-L-NPlanet-Fdiscovery_method-P"][:100]
    # array([0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 2, 0, 0, 0, 0, 0, 0, 0,
    #        0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0,
    #        0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    #        0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 2, 1, 1, 1, 3, 0, 1,
    #        0, 0, 1, 1, 0, 1, 2, 1], dtype=int32)


The content array for planet ``name`` has all 3572 planet names running together, while the content array for ``discovery_method`` has only the 10 *distinct* discovery method names, while its pointer array effectively acts like enumeration constants (pointing to the 10 strings). This space-saving feature is a natural consequence of the pointer data type: no enumeration type is explicitly needed.

Columnar vs rowwise
"""""""""""""""""""

This column-at-a-time way of organizing data is very good if you will be accessing one or a few attributes from all or many objects. For instance, to answer questions like "how many stars and planets are in the dataset?" (above), you only need to access the list size attributes, not any of the eccentricity or semimajor axis values, but you have to do it for all stars in the dataset. This access pattern is common in batch data analysis, when querying a static dataset.

Sometimes, however, you want the opposite: all attributes of a single object, to "drill down" into a single interesting entity or to visualize a single interesting event. Or perhaps you have a streaming data pipeline or Remote Procedure Call (RPC), in which whole objects are moving from one processor to the next. In these cases, you'd want all attributes of an object to be contiguous— rowwise data— rather than all values of an attribute to be contiguous— columnar data. For these cases, you do not want to use OAMap. (Use Protocol Buffers, Thrift, or Avro.)

OAMap is not a file format
""""""""""""""""""""""""""

The reason I used a website as a data source (other than saving you the trouble of downloading a big file) is to emphasize the fact that this is not a new file format— it is a way of working with nested data using tools that can already manage flat, named arrays. In this case, the source of flat, named arrays is HTTP (``urlopen``) with Numpy headers (``numpy.load``), but it could as easily be an HDF5 file. The OAMap functions only require a dict-like source of arrays.

The "mapping" described here is between a conceptual view of objects and the real arrays, however they are served. There are already file formats that represent hierarchically nested objects in arrays— ROOT, Parquet, and Apache Arrow— the transformation rules used by the OAMap package are a generalization of these three, so that they can all be used as sources.

But granted that OAMap is not a file format, it's a particularly efficient one. It requires very little "support structure" to operate. Even the ``schema.json`` that you downloaded to determine the structure of the exoplanets dataset was superfluous— the schema is losslessly encoded in the default array names. (That's why the names are long and contain hyphenated code-letters.) The arrays could literally be binary blobs in a filesystem directory, and

.. code-block:: python

    import oamap.inference
    schema = oamap.inference.fromnames(directory_listing)

would be sufficient to reconstruct the schema and therefore the data. The `Numpy npz file format <https://docs.scipy.org/doc/numpy/reference/generated/numpy.savez.html>`_ is a dead-simple way to save (and optionally compress) a collection of named arrays, and it happens to be the leanest way to store the exoplanets dataset:

======================== ======= ======= ======= ========= ========= ============ ============
Format                   Nested? Binary? Schema? Columnar? Nullable? Uncompressed Compressed*
======================== ======= ======= ======= ========= ========= ============ ============
**CSV**                                                                4.9 MB      0.96 MB
**JSON**                 yes                                          14  MB       1.2  MB
**BSON**                 yes     yes                                  11  MB       1.5  MB
**Avro**                 yes     yes     yes                           3.0 MB      0.95 MB
**ROOT**                 yes     yes     yes     yes                   5.7 MB      1.6  MB
**Parquet**              yes     yes     yes     yes       yes         1.1 MB      0.84 MB
**OAMap in Numpy (npz)** yes     yes     yes     yes       yes         2.7 MB      0.68 MB
======================== ======= ======= ======= ========= ========= ============ ============

**(*gzip level 4)**

- NASA's original data were provided as a **CSV** file, but CSV is a rectangular table that cannot represent the fact that one star can have multiple planets without padding or duplication— NASA chose duplication. This format happens to be relatively small because of all the missing data: missing data only costs one byte in CSV (a comma).
- **JSON** captures the structure of the variable number of planets per star, as well as wrapping up values with their errors in convenient records, but with considerable bloat.
- The fact that JSON is text, rather than binary, is often blamed for its size, but more often it's because JSON lacks a schema. The names of all the fields are repeated for each object. **BSON** is a binary JSON format, but it's not much smaller than JSON.
- **Avro** is binary JSON with a schema, and a good choice when rowwise data is preferred over columnar (e.g. streaming data or RPC). But because it is not columnar, accessing just one attribute requires all attributes to be read, so it can be a poor choice for batch data analysis.
- The **ROOT** framework defines a serialization format for arbitrary C++ objects that is binary and columnar with a schema. It was developed for particle physics data, which requires these features but not often missing data. The exoplanets dataset is relatively large in ROOT format because missing values are represented by a fill value like ``-999``; they cannot be skipped.
- **Parquet** is a binary, columnar format with a schema, and it has a `clever "definition level/repetition level" mechanism <https://blog.twitter.com/engineering/en_us/a/2013/dremel-made-simple-with-parquet.html>`_ to pack missing data and nested data in the fewest bytes before compression. It is therefore the winner in the "uncompressed" category.
- However, the repetition level mechanism requires structure bits for each field, even if there are many fields at the same level of structure, as is the case for our 122 planetary attributes. This repeated data can't be compressed away (it's in different columns). **OAMap** uses a simpler mechanism from ROOT and Apache Arrow that shares one "number of planets" array among all planetary attributes. It's the winner of the "compressed" category.

The story would look different if we had used a string dominated or purely numerical dataset, or if we had used one without missing values, or one with fewer attributes per same-level structure. The exoplanets dataset has a little of all of these anti-features; it's the worst of all worlds, and therefore makes a good example.

Schemas
"""""""

Unlike a rowwise representation, which could introduce new data types at any point in the stream, columnar representations must always have a schema. As we've seen above, schemas also reduce the memory needed to store a dataset, and they allow functions to be compiled for faster execution as well.

A schema definition language defines the scope of representable data. To keep things simple and language-independent, we define schemas with seven generators: **Primitive**, **List**, **Union**, **Record**, **Tuple**, **Pointer**, and **Extension** (PLURTPE: *plur-teep*).

Primitive
~~~~~~~~~

Primitives are fixed-width, concrete types such as booleans, integers, floating point numbers, and complex numbers. For generality, OAMap primitives can be anything describable by a `Numpy dtype <https://docs.scipy.org/doc/numpy/reference/generated/numpy.dtype.html>`_ and `shape <https://docs.scipy.org/doc/numpy/reference/generated/numpy.ndarray.shape.html>`_, which includes not just scalars but fixed-size vectors, matrices, and tensors and rowwise structs (`Numpy record dtypes <https://docs.scipy.org/doc/numpy/user/basics.rec.html>`_).

For example,







List
~~~~

Union
~~~~~

Record
~~~~~~

Tuple
~~~~~

Pointer
~~~~~~~

Extension
~~~~~~~~~







Filling datasets
""""""""""""""""

(immutable or append-only semantics)

Columnar granularity
""""""""""""""""""""

(add an attribute to the exoplanets (number of moons), soft-filter the exoplanets)

Low-latency random access
"""""""""""""""""""""""""

(memory mapped files, starts/stops versus counts)

High throughput processing
""""""""""""""""""""""""""

(compile with Numba; completely avoids deserialization; should add up-to-date performance measurements)
