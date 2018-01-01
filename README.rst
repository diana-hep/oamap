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

For this walkthrough, we'll be working with a real dataset, the `NASA Exoplanet Archive <https://exoplanetarchive.ipac.caltech.edu/>`_. As an illustration of columnar data access, we can start working with it without fully downloading it. Type the following to get a schema.

.. code-block:: python

    from oamap.schema import *

    import codecs
    try:
        from urllib.request import urlopen   # Python 3
    except ImportError:
        from urllib2 import urlopen          # Python 2

    baseurl = "http://diana-hep.org/oamap/examples/planets/"

    # explicit utf-8 conversion required for Python 3
    remotefile = urlopen(baseurl + "schema.json")
    withcodec = codecs.getreader("utf-8")(remotefile)

    schema = Schema.fromjsonfile(withcodec)

If you're brave, try ``schema.show()`` to see its hundreds of attributes. This data object is a list of stars with planets; each star has attributes like distance, position on the sky, mass, and temperature, and each of those attributes has a central value, asymmetric uncertainties, and limit flags, packaged in record structures. It also has a list of planets, with its own attributes, like orbital period, mass, discovery method, etc. Some of these, like discovery method, are strings, some are numbers, and most are "nullable," meaning that they could be missing (unmeasured or otherwise unavailable).

We can view the data as nested Python objects by providing a dict of arrays to the schema. (The ``DataSource`` below makes the website act like a Python dict.)

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

This ``stars`` object is a list of ``Star`` records with nested ``planets``. If you print it on the Python command line (or Jupyter notebook, whatever you're using), you'll see that there are 2660 stars, though we have not downloaded hundreds of attributes for thousands of stars. (You'd notice the lag.)

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

In short, the dataset appears to be a collection of Python objects. However, it's actually a set of Numpy arrays. One hint that you may have noticed is the time lag whenever you requested a *new* attribute, such as star name or planet orbital period, the first time you accessed it from *any* star or planet. This is because the request triggered a download of the attribute array, which contains values for all stars and planets at once, through our ``DataSource``.

To peek behind the scenes and see these arrays, look at

.. code-block:: python

    stars._cache.arraylist

The slots that are filled with arrays are the ones you've viewed above. Note that these arrays don't all have the same length, as they would if this dataset could be represented as a rectangular table. There are more planets than stars,

.. code-block:: python

    len(stars)
    # 2660
    sum(len(x.planets) for x in stars)
    # 3572

so there should be more values of planetary eccentricity than stellar temperature, for instance. But some of those fields are also missing, so there aren't even the same number of planetary attributes.

.. code-block:: python

    sum(0 if y.eccentricity is None else 1 for x in stars for y in x.planets)
    # 1177
    sum(0 if y.semimajor_axis is None else 1 for x in stars for y in x.planets)
    # 2084

    d = DataSource()
    eccentricity = d["object-L-NStar-Fplanets-L-NPlanet-Feccentricity-NValueAsymErr-Fval"]
    # array([ 0.   ,  0.   ,  0.05 , ...,  0.   ,  0.12 ,  0.062], dtype=float32)
    semimajor_axis = d["object-L-NStar-Fplanets-L-NPlanet-Fsemimajor_axis-NValueAsymErr-Fval"]
    # array([ 0.115     ,  0.01855   ,  0.26899999, ...,  0.359     ,
    #         0.056     ,  0.116     ], dtype=float32)
    len(eccentricity), len(semimajor_axis)
    # (1153, 2076)

The arrays contain exactly as much data as is necessary to reconstruct the objects, so an attribute with more missing data is represented by a smaller array.

I used the website as a data source to emphasize that this is not a type of file— in this particular case, every column is a separate file. The "mapping" in "Object Array Mapping" is between an object and a set of named arrays— those arrays may be located in any file or files. Therefore, it's a metaformat, a way of interpreting arrays as objects.

Advantages and disadvantages
""""""""""""""""""""""""""""

This column-at-a-time way of organizing data is very good if you will be accessing one or a few attributes of all or many objects. For instance, to answer questions like "how many stars and planets are in the dataset?" (above), we only need to access the list sizes, not any of the eccentricity or semimajor axis values, but we have to do it for all stars in the dataset. This access pattern is common in batch data analysis or querying a static dataset.

Sometimes you want the opposite: all attributes of a single object, to "drill down" into a single interesting entity or to visualize a single interesting event. Or perhaps you have a streaming data pipeline, in which whole objects are always moving from one processor to the next. In these cases, you'd want all attributes of an object to be contiguous— rowwise data— rather than all values of an attribute to be contiguous— columnar data. If that is your goal, you do not want to use OAMap.




=========== ======= ======= ======= ========= ========= ============ ============
Format      Nested? Binary? Schema? Columnar? Nullable? Uncompressed Compressed  
=========== ======= ======= ======= ========= ========= ============ ============
CSV                                                     `` 4.9 MB``   ``0.96 MB``
JSON        yes                                         ``14   MB``   ``1.2  MB``
BSON        yes     yes                                 ``11   MB``   ``1.5  MB``
Avro        yes     yes     yes                         `` 3.0 MB``   ``0.95 MB``
ROOT        yes     yes     yes     yes                 `` 5.7 MB``   ``1.6  MB``
Parquet     yes     yes     yes     yes       yes       `` 1.1 MB``   ``0.84 MB``
OAMap-Numpy yes     yes     yes     yes       yes       `` 2.7 MB``   ``0.68 MB``
=========== ======= ======= ======= ========= ========= ============ ============




Schemas
"""""""

