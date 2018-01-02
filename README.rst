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

For this walkthrough, we'll be working with a real dataset, the `NASA Exoplanet Archive <https://exoplanetarchive.ipac.caltech.edu/>`_. As an illustration of columnar data access, you can start working with it without fully downloading it. Copy-paste the following to get a schema.

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

The schema is a description of the data type, not the data itself: data in OAMap are strongly and statically typed (even though this is Python). If you're brave, try ``schema.show()`` to see hundreds of attributes for each star and all the planets orbiting these stars. Stars and planets are data records with attributes such as distance, position on the sky, orbital period, mass, discovery method, etc. Most numerical quantities have uncertainties, so values and their uncertainties are bundled into nested records. Discovering planets is a tricky business, so many of these quantities (numeric and string-valued) are "nullable," meaning that they could be missing (unmeasured or otherwise unavailable).

Perhaps the most important point about the structure of this schema is that each star may have a different number of planets.

.. code-block:: python

    schema.show()                             # it's a list
    schema.content.fields["planets"].show()   # it's another list

The data *cannot* be described by a single flat table without padding or duplication. If we were designing a conventional database for this dataset, we would make two tables: one for stars and one for planets, with links between the tables (`normal form <https://en.wikipedia.org/wiki/Database_normalization>`_). That's okay for a single variable-length sublist, but some datasets, such as those in particle physics, have events containing arbitrary numbers of electrons, muons, taus, photons, and many different kinds of jets— the database normalization technique `gets cumbersome <https://stackoverflow.com/q/38831961/1623645>`_ and loses sight of the fact that quantities nested under the same parent should be stored on the same machine because they are frequently processed together.

Enough talk: let's get the data. The schema can be treated like a Python type: you get an instance of that type by calling it with arguments. The required argument is a dict-like object of columnar arrays. We're hosting the exoplanet dataset on the same website, so use this ``DataSource`` class to make the website act like a dict of Numpy arrays.

.. code-block:: python

    import io
    import numpy

    class DataSource:
        def __getitem__(self, name):        # overloads datasource["name"] to fetch from web
            try:
                return numpy.load(io.BytesIO(urlopen(baseurl + name + ".npy").read()))
            except Exception as err:
                raise KeyError(str(err))

    stars = schema(DataSource())

If you print this ``stars`` object on the Python command line (or Jupyter notebook, whatever you're using), you'll see that there are 2660 stars, though you have not downloaded hundreds of attributes for thousands of stars. (You'd notice the delay, especially if you're on a slow network.)

Exploring the data interactively
""""""""""""""""""""""""""""""""

To poke around the data, use ``dir(stars[0])``, ``stars[0]._fields`` or tab-completion to see what fields are available. One such field is ``planets``.

.. code-block:: python

    stars[0].planets
    # [<Planet at index 0>]

    stars[258].planets   # five planets!
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

In short, the dataset appears to be a nested Python object. However, all of these object façades ("proxies") are created on demand from the data in the arrays. In functions compiled by Numba (described at the bottom of this walkthrough), there won't even be any runtime objects— the code itself will be transformed to access array data instead of creating anything that has to be allocated in memory. This code transformation is part of the compilation process and the throughput of the transformed code is often faster than that of compiled C code with runtime objects (see `this talk <https://youtu.be/jvt4v2LTGK0>`_ and `this paper <https://arxiv.org/abs/1711.01229>`_ again).

While executing the above commands, you might have noticed a time lag whenever you requested a *new* attribute, such as star name or planet orbital period, the first time you accessed it from *any* star or planet. If you then view this attribute on another star, there's no time lag because it is already downloaded. Data access has a *columnar granularity—* if you show interest in an attribute, it is assumed that you'll want to do something with that attribute for all or most data points. The alternative, *rowwise granularity* (e.g. JSON), would fetch a whole star's data record if you want one of its attributes. (The optimum for data analysis is usually columnar granularity in chunks of *N* records, similar to Parquet's "row groups" or ROOT's "baskets.")

To peek behind the scenes and see these arrays, look at

.. code-block:: python

    stars._cache.arraylist

The slots that are filled with arrays are the ones you've viewed. Note that these arrays don't all have the same length, as they would if this dataset were a rectangular table. There are more planets than stars,

.. code-block:: python

    len(stars)
    # 2660
    sum(len(x.planets) for x in stars)
    # 3572

so there should be more planetary eccentricity values than stellar temperature values, for instance. But some of those values are missing, so there aren't even the same number of values for two different planetary attributes.

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

When would you want this?
"""""""""""""""""""""""""

Note that you may not always want columnar data. This access method benefits batch analyses and query-style analysis, where you typically want to know something about one or a few attributes from many or all objects. However, sometimes you want to know about all attributes of a single object, e.g. to "drill down" to a single interesting entity or to visualize a single interesting event. Drill downs and event displays are not high-throughput applications, so it usually doesn't hurt to store data as columns for fast analysis and slow single object examination.

On the other hand, remote procedure calls (RPC) and its extreme, streaming data pipelines, in which objects are always in flight between processors, would be hindered by a columnar data representation. These systems need to shoot a whole object from one processor to the next and then forget it— this case is much more efficient with rowwise data. You would *not* want to use OAMap for this case.

To illustrate the tradeoffs, I've converted the exoplanets dataset into a variety of formats:

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

(\*Some formats have built-in compression, others don't; in all cases I compressed with gzip level 4.)

- **CSV** was NASA's original file format, but it cannot fit in a rectangular table without padding or duplication— NASA chose duplication. Most stars have only one planet, so it's not *much* duplication.
- **JSON** captures the structure of the data better, but with considerable bloat. Most of this compresses away because it consists of record field names, restated for every data point in the sample.
- The fact that JSON is human-readable text, rather than binary, is often blamed for this bloat, but it usually has more to do with this repetition of data points. **BSON** is a binary version of JSON, but it's not much smaller.
- **Avro** is one of several JSON-like binary formats with a schema (see also Thrift, ProtocolBuffers and FlatBuffers). The schema names all of the fields as metadata so they do not need to be restated in the dataset itself, which trades the flexibility of adding new fields whenever you want with a smaller, faster format. These rowwise formats were designed for RPC and streaming data pipelines.
- The **ROOT** framework serializes arbitrary C++ objects in a binary, columnar format with a schema (the C++ types). While C++ can have nullable records (class objects addressed with pointers), there are no nullable numbers. The exoplanets dataset has a lot of missing data, so we filled them in with ``NaN`` for floats and ``-2147483648`` for integers, which takes more space than skipping missing values entirely.
- **Parquet** is the Big Data community's nested, binary, schemaed, columnar data format that skips missing values. It has a `clever "definition level/repetition level" mechanism <https://blog.twitter.com/engineering/en_us/a/2013/dremel-made-simple-with-parquet.html>`_ to pack structural information about missing data and nesting levels into the fewest bytes before compression, and therefore wins in the uncompressed category.
- **OAMap** uses a simpler mechanism to express nesting (found in ROOT and Apache Arrow) and missing values (just Arrow) which is larger when uncompressed, but smaller when compressed. Parquet's nesting mechanism packs nesting structure into a minimum of bits, but those bits have to be repeated for all fields at the same level of a record, and the exoplanets (like particle physics data) have hundreds of fields per record. This duplication can't be compressed away (fields are separately compressed), which could explain why OAMap compresses smaller for exoplanets.

The situation might look different if we had purely numerical data, or text-heavy data, or a dataset without missing values, or one without hundreds of attributes per record. The exoplanets has a little of all of these anti-features— it's the worst of all worlds, and is therefore a great example.

OAMap is not a file format
""""""""""""""""""""""""""

Having just extolled OAMap's virtues as a data format, I must emphasize that OAMap is not a data format. It is an abstraction layer just above file formats and sources. The "mapping" described here is between a set of real arrays an a conceptual view of objects, and it doesn't matter how the real arrays are served. The reason I used a website as a data source— probably not a good choice for a high-throughput application— is to emphasize that point: this dataset isn't even a file. The binary data are served by HTTP (``urlopen``) and interpreted as arrays by Numpy (``numpy.load``), but it could as easily have been a local directory of files, a key-value database, or a single HDF5 file.

To make this point further, let's use a real file:

.. code-block:: bash

    wget http://diana-hep.org/oamap/examples/HZZ.root

Since this is a ROOT file, we'll need something to read it. Try `uproot <https://github.com/scikit-hep/uproot>`_ (version 2.5.14 or later):

.. code-block:: bash

    pip install uproot --user

Now we define a new schema, mapping parts of the conceptual object to the ROOT file's "branches." 

.. code-block:: python

    from oamap.schema import *

    schema2 = List(
        counts = "nEvents",
        content = Record(
          name = "Event",
          fields = dict(
            met = Record(
              name = "MissingEnergy",
              fields = dict(
                x = Primitive(None, data="MET_px"),
                y = Primitive(None, data="MET_py"),
              )
            ),
            electrons = List(
              counts = "NElectron",
              content = Record(
                name = "Electron",
                fields = dict(
                  px = Primitive(None, data="Electron_Px"),
                  py = Primitive(None, data="Electron_Py"),
                  pz = Primitive(None, data="Electron_Pz"),
                  energy = Primitive(None, data="Electron_E"),
                  charge = Primitive(None, data="Electron_Charge"),
                  iso = Primitive(None, data="Electron_Iso")
                )
              )
            ),
            muons = List(
              counts = "NMuon",
              content = Record(
                name = "Muon",
                fields = dict(
                  px = Primitive(None, data="Muon_Px"),
                  py = Primitive(None, data="Muon_Py"),
                  pz = Primitive(None, data="Muon_Pz"),
                  energy = Primitive(None, data="Muon_E"),
                  charge = Primitive(None, data="Muon_Charge"),
                  iso = Primitive(None, data="Muon_Iso")
                )
              )
            )
          )
        )
      )

We need to load the ROOT "tree" and adapt it to look like a dict,

.. code-block:: python

    import uproot

    class DataSource2:
        def __init__(self):
            self.ttree = uproot.open("HZZ.root")["events"]
        def __getitem__(self, name):
            if name == "nEvents":
                # ROOT TTrees don't have a number of entries branch; make it on the fly.
                return numpy.array([self.ttree.numentries])
            else:
                return self.ttree.array(name)

and now we can get objects from the ROOT file, just as we could from the web.

.. code-block:: python

    events = schema2(DataSource2())

    events[0].met.x, events[0].met.y
    # (5.9127712, 2.5636332)

    events[0].muons[0].px, events[0].muons[0].py, events[0].muons[0].pz
    # (-52.899456, -11.654672, -8.1607933)

    from math import sqrt
    for event in events:
        if len(event.muons) == 2:
            mu1, mu2 = event.muons[0], event.muons[1]
            if mu1.charge * mu2.charge < 0:
                px = mu1.px + mu2.px
                py = mu1.py + mu2.py
                pz = mu1.pz + mu2.pz
                energy = mu1.energy + mu2.energy
                print(sqrt(energy**2 - px**2 - py**2 - pz**2))

    # 90.2278015749
    # 74.7465483668
    # 89.7578672676
    # 94.855212688
    # 92.1167215271
    # ...

In the file format comparision, I made an "OAMap file" by putting the OAMap arrays into a `Numpy npz file <https://docs.scipy.org/doc/numpy/reference/generated/numpy.savez.html>`_, which is a dead-simple format for a collection of arrays. However, I could have put them into a ROOT file, which would have given the ROOT file the missing data packing feature that it lacked.

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
