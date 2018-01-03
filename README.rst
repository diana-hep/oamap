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

Enough talk: let's get the data. The schema can be treated like a Python type: you get an instance of that type by calling it with arguments. The required argument is a dict-like object of columnar arrays. I'm hosting the exoplanet dataset on the same website, so use this ``DataSource`` class to make the website act like a dict of Numpy arrays.

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

If you print this ``stars`` object on the Python command line (or Jupyter notebook, whatever you're using), you'll see that there are 2660 stars, though you have not downloaded hundreds of attributes for thousands of stars. (Downloading the whole dataset would cause a noticeable delay, especially on a slow network.)

Exploring the data interactively
""""""""""""""""""""""""""""""""

To poke around the data, use ``dir(stars[0])``, ``stars[0]._fields`` or tab-completion to see what fields are available. One such field is ``planets``.

.. code-block:: python

    stars[0].planets           # one planet...
    # [<Planet at index 0>]

    stars[258].planets         # five planets!
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

While executing the above commands, you might have noticed a time lag whenever you requested a *new* attribute, such as star name or planet orbital period, the first time you accessed it from *any* star or planet. If you then view this attribute on another star, there's no time lag because it is already downloaded. The data access has *columnar granularity—* if you show interest in an attribute, it is assumed that you'll want to do something with that attribute for all or most data points. The alternative, *rowwise granularity* (e.g. JSON), would fetch a whole star's data record if you want one of its attributes. (The optimum for data analysis is usually columnar granularity in chunks of *N* records, similar to Parquet's "row groups" or ROOT's "clusters.")

To peek behind the scenes and see these arrays, look at

.. code-block:: python

    stars._cache.arraylist

The slots that are filled with arrays are the ones you've viewed. Note that these arrays don't all have the same length, as they would if this dataset were a rectangular table. There are more planets than stars,

.. code-block:: python

    len(stars)
    # 2660
    sum(len(x.planets) for x in stars)
    # 3572

so there should be more planetary eccentricity values than stellar temperature values, for instance. But some of those values are missing (``None``), so there aren't even the same number of values for two different planetary attributes.

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

You might not always want columnar data. This access method benefits batch analyses and query-style analysis, where you typically want to know something about one or a few attributes from many or all objects. However, sometimes you want to know about all attributes of a single object, e.g. to "drill down" to a single interesting entity or to visualize a single interesting event. Drill downs and event displays are not high-throughput applications, so it usually doesn't hurt to store data as columns for fast analysis and slow single-object examination.

On the other hand, remote procedure calls (RPC) and their extreme, streaming data pipelines, in which objects are always in flight between processors, would be hindered by a columnar data representation. These systems need to shoot a whole object from one processor to the next and then forget it— it makes much more sense for whole objects to be contiguous (rowwise) in that case. You would *not* want to use OAMap for that.

To illustrate the tradeoffs, I've converted the exoplanets dataset into a variety of formats:

======================== ======= ======= ======= ========= ========= ============ ============
Format                   Nested? Binary? Schema? Columnar? Nullable? Uncompressed Compressed*
======================== ======= ======= ======= ========= ========= ============ ============
**CSV**                                                               4.9 MB      0.96 MB
**JSON**                 yes                                         14  MB       1.2  MB
**BSON**                 yes     yes                                 11  MB       1.5  MB
**Avro**                 yes     yes     yes                          3.0 MB      0.95 MB
**ROOT**                 yes     yes     yes     yes                  5.7 MB      1.6  MB
**Parquet**              yes     yes     yes     yes       yes        1.1 MB      0.84 MB
**OAMap in Numpy (npz)** yes     yes     yes     yes       yes        2.7 MB      0.68 MB
======================== ======= ======= ======= ========= ========= ============ ============

(\*Some formats have built-in compression, others have to be externally compressed; in all cases I used gzip level 4.)

- **CSV** was NASA's original file format, but it cannot fit in a rectangular table without padding or duplication— NASA chose duplication. Most stars have only one planet, so it's not *much* duplication.
- **JSON** captures the structure of the data better, but with considerable bloat. Most of this compresses away because it consists of record field names, restated for every data point in the sample.
- The fact that JSON is human-readable text, rather than binary, is often blamed for this bloat, but it usually has more to do with this repetition of data points. **BSON** is a binary version of JSON, but it's not much smaller.
- **Avro** is one of several JSON-like binary formats with a schema (see also Thrift, ProtocolBuffers and FlatBuffers). The schema names all of the fields as metadata so they do not need to be restated in the dataset itself, which trades the flexibility of adding new fields whenever you want with a smaller, faster format. These rowwise formats were designed for RPC and streaming data pipelines.
- The **ROOT** framework serializes arbitrary C++ objects in a binary, columnar format with a schema (the C++ types). While C++ can have nullable records (class objects addressed with pointers), there are no nullable numbers. The exoplanets dataset has a lot of missing data, so I filled them in with ``NaN`` for floats and ``-2147483648`` for integers, which takes more space than skipping missing values entirely.
- **Parquet** is the Big Data community's nested, binary, schemaed, columnar data format that skips missing values. It has a `clever "definition level/repetition level" mechanism <https://blog.twitter.com/engineering/en_us/a/2013/dremel-made-simple-with-parquet.html>`_ to pack structural information about missing data and nesting levels into the fewest bytes before compression, and therefore wins in the uncompressed category.
- **OAMap** uses a simpler mechanism to express nesting (found in ROOT and Apache Arrow) and missing values (just Arrow) which is larger than Parquet when uncompressed, but smaller when compressed. Parquet's nesting mechanism packs nesting structure into a minimum of bits, but those bits have to be repeated for all fields at the same level of a record, and the exoplanets (like particle physics data) have hundreds of fields per record. This duplication can't be compressed away (fields are compressed independently of one another), which could explain why OAMap compresses smaller for exoplanets.

The situation would look different if we had purely numerical data, or text-heavy data, or a dataset without missing values, or one without hundreds of attributes per record. The exoplanets has a little of all of these anti-features— it's the worst of all worlds, and therefore a great example.

OAMap is not a file format
""""""""""""""""""""""""""

Having just extolled OAMap's virtues as a data format, I must emphasize that OAMap is not a data format. It is an abstraction layer just above file formats and sources. The "mapping" described here is between a set of real arrays an a conceptual view of objects, and it doesn't matter how the real arrays get served. The reason I used a website as a data source— probably not a good choice for a high-throughput application— is to emphasize that point. This dataset isn't even a *file.* The binary data are served by HTTP (``urlopen``), separately for each column, and interpreted as arrays by Numpy (``numpy.load``). It could as easily have been a local directory of files, a key-value database, or a single HDF5 file, etc.

To push this point further, let's switch to a real file:

.. code-block:: bash

    wget http://diana-hep.org/oamap/examples/HZZ.root

It's in ROOT format, so you'll need something to read it. Try `uproot <https://github.com/scikit-hep/uproot>`_ (version 2.5.14 or later):

.. code-block:: bash

    pip install uproot --user

Now define a new schema, mapping parts of the conceptual object to the ROOT file's "branches." 

.. code-block:: python

    from oamap.schema import *

    schema = List(
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

Next, load the ROOT "tree" and adapt it to look like a dict.

.. code-block:: python

    import uproot

    class DataSource:
        def __init__(self):
            self.ttree = uproot.open("HZZ.root")["events"]
        def __getitem__(self, name):
            if name == "nEvents":
                # ROOT TTrees don't have a number of entries branch; make it on the fly.
                return numpy.array([self.ttree.numentries])
            else:
                return self.ttree.array(name)

Now you can get objects from the ROOT file, just as you did from the web.

.. code-block:: python

    events = schema(DataSource())

    events[0].met.x, events[0].met.y
    # (5.9127712, 2.5636332)

    events[0].muons[0].px, events[0].muons[0].py, events[0].muons[0].pz
    # (-52.899456, -11.654672, -8.1607933)

    from math import sqrt
    for event in events:
        if len(event.muons) == 2:
            mu1, mu2 = event.muons[0], event.muons[1]
            if mu1.charge * mu2.charge < 0:
                # oppositely signed muons: calculate their mass (it's close to the Z mass)
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

For the file format comparision table (previous section), the "OAMap file" was really a `Numpy npz file <https://docs.scipy.org/doc/numpy/reference/generated/numpy.savez.html>`_, a dead-simple format when you only want to save a set of named arrays. I could have instead put them in a ROOT file, which would have given the ROOT file the missing data handling that worked so well for the exoplanets dataset.

Schemas
"""""""

Now let's focus on OAMap's schemas. Columnar data representations must have schemas, since the schema acts as a set of instructions to reassemble objects from serialized data. "Schemaless" file formats pack reassembly instructions inline with or between the objects, and there's only a "between objects" for a rowwise representation. A schema specifies all of the possible values that objects of that type may take, and the schema definition language describes the possible types that any object in the system can ever have.

To keep things simple and language-independent, OAMap schemas are defined by seven generators: **Primitive**, **List**, **Union**, **Record**, **Tuple**, **Pointer**, and **Extension** (PLURTPE: *plur-teep*). Thus, we can't put function objects or transient types such as file handles into an object described by OAMap, but we can make arbitrary graphs using pointers, heterogeneous collections using unions, and interpret these data in special ways at runtine with extensions. Each generator is described below.

Primitive
~~~~~~~~~

Primitives are fixed-width, concrete types such as booleans, integers, floating point numbers, and complex numbers. Primitives terminate a type schema (they don't contain any subtypes). For generality, OAMap primitives include anything describable by a `Numpy dtype <https://docs.scipy.org/doc/numpy/reference/generated/numpy.dtype.html>`_ and `shape <https://docs.scipy.org/doc/numpy/reference/generated/numpy.ndarray.shape.html>`_— not just scalars but fixed-size vectors, matrices, and tensors and rowwise structs (`Numpy record dtypes <https://docs.scipy.org/doc/numpy/user/basics.rec.html>`_).

For example,

.. code-block:: python

    import numpy
    from oamap.schema import *

    schema = List(Primitive(int, data="p"), counts="c")

    obj = schema({"p": [1, 2, 3, 4, 5], "c": [5]})

    obj
    # [1, 2, 3, 4, 5]

is a list of simple scalars with a dtype generated by ``int``,

.. code-block:: python

    schema = List(Primitive(">c16", (2, 2), data="p"), counts="c")

    obj = schema({"p": [
        [[ 0,  1],
         [ 1,  0]],

        [[ 0, -1j],
         [1j,  0]],

        [[ 1,  0],
         [ 0, -1]]     ], "c": [3]})

    obj
    # [array([[ 0.+0.j,  1.+0.j],
    #         [ 1.+0.j,  0.+0.j]]),
    #  array([[ 0.+0.j,  0.-1.j],
    #         [ 0.+1.j,  0.+0.j]]),
    #  array([[ 1.+0.j,  0.+0.j],
    #         [ 0.+0.j, -1.+0.j]])]

are big-endian (``>``), complex-valued 2×2 matrices, and

.. code-block:: python

    recarray = numpy.empty(5, dtype=[("one", int), ("two", float), ("three", "S5")])
    recarray[0] = (1, 1.1, "one")
    recarray[1] = (2, 2.2, "two")
    recarray[2] = (3, 3.3, "three")
    recarray[3] = (4, 4.4, "four")
    recarray[4] = (5, 5.5, "five")

    schema = List(Primitive(recarray.dtype))
    obj = schema({"object-L": recarray, "object-c": [5]})

    obj
    # [(1,  1.1, 'one'), (2,  2.2, 'two'), (3,  3.3, 'three'), (4,  4.4, 'four'), (5,  5.5, 'five')]

are rowwise records containing an integer, a float, and a string of no more than 5 characters. These rowwise structures can be embedded within a larger columnar object (a ROOT feature; therefore OAMap must support it).

Primitives are by themselves fairly expressive— they can do anything that Numpy can do. What primitives and Numpy cannot express are variable-width values, which is why the example above was limited to strings of 5 characters (shorter strings are padded for constant length).

In fact, if your data fits well into a primitive or simple list of primitives, then you have tabular data and you don't need OAMap. Use Numpy, Pandas, or SQL instead.

List
~~~~

Lists are variable-length in the sense that the schema does not prescribe their length. A list type must always have a content type, which could be anything— primitive types, nested lists, records, etc. Lists are "homogeneous," meaning that all elements in the list must have the same, prescribed type, but that prescribed type could be a union of many options.

For example,

.. code-block:: python

    schema = List(List("int"))   # shorthand string "int" for Primitive("int")

    obj = schema({"object-L-L": [1, 2, 3, 4, 5], "object-L-c": [3, 0, 2], "object-c": [3]})
    obj
    # [[1, 2, 3], [], [4, 5]]

is a list of lists and

.. code-block:: python

    schema = List(Tuple(["int", "float"]))

    obj = schema({"object-L-F0": [1, 2, 3], "object-L-F1": [1.1, 2.2, 3.3], "object-c": [3]})
    obj
    # [(1, 1.1), (2, 2.2), (3, 3.3)]

is a list of tuples. (Lists are homogeneous and arbitrary-length, tuples are heterogeneous and fixed-length.)

List contents are stored in arrays that ignore list boundaries and the boundaries are reconstructed by "counts" arrays like ``"object-L-c": [3, 0, 2]``. Actually, there are three common representations of list structure:

- a **counts array**, which compress well (small integers) but don't permit random access (to find the *Nth* element, you have to add up the first *N – 1* counts);
- an **offsets array**, which is a cumulative sum of the counts array, permitting random access;
- **starts** and **stops arrays**, which individually indicate the start and stop of each list (also random accessible).

ROOT uses counts and offsets, `Arrow uses offsets <https://github.com/apache/arrow/blob/master/format/Layout.md#list-type>`_, and Parquet uses something altogether different (repetition level). OAMap converts any of these into starts and stops arrays because that form is the most powerful: the physical data may contain gaps to emulate stencils, may be in a different physical order than the logical order for database-style indexing, and may contain data accessible by pointer but not in the main list (e.g. it's part of a tree). When OAMap fails to find a starts or stops array (default names end with ``-B`` and ``-E``), it searches for a counts array (default name ends with ``-c``). For simplicity, all of the examples we have considered have been in that fallback case. Arrow and Parquet are handled with special dict-like objects— offsets arrays can be turned into starts and stops without even copying data.

Most datasets are lists at the top level— lists of *something—* so they have one silly-looking single element array containing nothing but the total number of entries. The total number of entries is sometimes found in metadata, rather than data, so this array is created on demand in such cases (as in the ROOT example above).

Some datasets are so large that even a single attribute cannot be fully read into memory— these list-of-X datasets can be represented as a sequence of list-of-X objects, each of which containing one partition of the data. Columnar datasets must always be partitioned at some level, since the serialization of an attribute must end at some point to move on to the next attribute. (In that sense, rowwise data can be thought of as columnar data with partition size 1!) Parquet calls these partitions "row groups" and ROOT calls them "clusters," but OAMap has no special nomenclature. The same schema can apply to many objects, so there's a natural way to process a sequence of partitions:

.. code-block:: python

    schema = List(Record({"x": "float", "y": "float", "z": "float"}))
    for arrays in partitions:
        obj = schema(arrays)
        for x in obj:
            do_something(x)

Union
~~~~~

Unions represent data that could be one of several types. In algebraic type theory, these are called "`sum types <https://en.wikipedia.org/wiki/Tagged_union>`_" because addition has the properties of logical-or: the type may be this, *or* that, *or* something else.

A union is expressed by a list of possibilities:

.. code-block:: python

    schema = List(Union(["float", List("int")]))

    obj = schema({"object-c": [3],                       # length of outer list
                  "object-L-T": [0, 1, 0],               # tags: possibility 0 (float) or 1 (list of int)?
                  "object-L-U0": [1.1, 3.3],             # data for possibility 0
                  "object-L-U1-c": [4],                  # list lengths for possibility 1
                  "object-L-U1-L": [1, 2, 3, 4]})        # list content for possibility 1
    obj
    # [1.1, [1, 2, 3, 4], 3.3]

Unions can emulate a popular object-oriented concept: class inheritance. If we wanted to model an ontology of objects, like "electrons, muons, and taus are all leptons, leptons and quarks are all charged particles, charged particles and photons are all particles", we can create records for each of the concrete classes and combine them with a union.

.. code-block:: python

    schema = List(Union([
        Record(name="NeutralParticle", fields={"energy": "float"}),
        Record(name="ChargedParticle", fields={"energy": "float", "charge": "int"})
        ]))
    obj = schema({"object-c": [5],
                  "object-L-T": [1, 1, 0, 1, 0, 0],
                  "object-L-U0-Fenergy": [1.1, 2.2, 3.3],
                  "object-L-U1-Fenergy": [1.1, 2.2, 3.3],
                  "object-L-U1-Fcharge": [1, -1, -1]})
    obj
    # [<ChargedParticle at index 0>, <ChargedParticle at index 1>, <NeutralParticle at index 0>,
    #  <ChargedParticle at index 2>, <NeutralParticle at index 1>]

Extensive unions can almost emulate a dynamically typed environment: if you could enumerate every possible type as a union's possibilities, you could get the behavior of native Python, which determines types at runtime using a mechanism similar to the "tags" above. (Every Python object has a pointer to its type object, which is an integer, like the tag integer here.) However, you can't actually express "the union of all types" because you have to explicitly list *concrete* types, and there are infinitely many of those, generated by a finite number of generators (primitives, lists, unions, records, tuples, and pointers). If you have a dataset that makes use of dynamic typing, you can usually identify the two or three concrete types a quantity will actually have, and make a union of those. Unions allow you to approach, but not reach, dynamic typing.

The tags array (``-T``) and contents (``-U*``) in these examples are sufficient to express the types and data, but not to randomly access an element (without counting the number of times that tag has appeared before, to find the offset into the contents arrays). If not provided (by ``-O``), OAMap creates an offsets array for random access, similar to the way that it creates list starts and stops from a counts array.

An offsets array may point to compact contents (Arrow's "`dense union <https://github.com/apache/arrow/blob/master/format/Layout.md#dense-union-type>`_"):

    schema = List(Union(["float", "bool"]))
    obj = schema({"object-c": [5],
                  "object-L-T": [0, 0, 0, 1, 1],
                  "object-L-O": [0, 1, 2, 0, 1],                # counting, masked by tag
                  "object-L-U0": [1.1, 2.2, 3.3],
                  "object-L-U1": [True, False]})
    obj
    # [1.1, 2.2, 3.3, True, False]

or padded contents (Arrow's "`sparse union <https://github.com/apache/arrow/blob/master/format/Layout.md#sparse-union-type>`_"):

    schema = List(Union(["float", "bool"]))
    obj = schema({"object-c": [5],
                  "object-L-T": [0, 0, 0, 1, 1],
                  "object-L-O": [0, 1, 2, 3, 4],                # just counting
                  "object-L-U0": [1.1, 2.2, 3.3, -999, -999],   # need to pad unused values
                  "object-L-U1": [-1, -1, -1, True, False]})
    obj
    # [1.1, 2.2, 3.3, True, False]

In both cases, the offsets can be computed from the tags, so we often avoid saving them.

Record
~~~~~~

Records represent data that contains several types. In algebraic type theory, these are called "`product types <https://en.wikipedia.org/wiki/Product_type>`_" because multiplication has the properties of logical-and: the type is this *and* that, *and* something else.

A record is expressed by a dict of field names to field types (or a list of key-value pairs to maintain the order for readability).

We've already seen several examples of record types, so here's one drawn from the exoplanet dataset:

.. code-block:: python

    remotefile = urlopen("http://diana-hep.org/oamap/examples/planets/schema.json")
    remotefile = codecs.getreader("utf-8")(remotefile)
    schema = Schema.fromjsonfile(remotefile)

    schema.content.fields["gaia"].show()
    # Record(
    #   nullable = True, name = 'GAIAMeasurements', 
    #   fields = {
    #     'distance': Record(
    #       nullable = True, name = 'ValueAsymErr', 
    #       fields = {
    #         'lim': Primitive(dtype('bool'), nullable=True),
    #         'loerr': Primitive(dtype('float32'), nullable=True),
    #         'val': Primitive(dtype('float32'), nullable=True),
    #         'hierr': Primitive(dtype('float32'), nullable=True)
    #       }),
    #     'propermotion': Record(
    #       nullable = True, name = 'GAIAProperMotion', 
    #       fields = {
    #         'total': Record(
    #           name = 'ValueErr', 
    #           fields = {
    #             'lim': Primitive(dtype('bool'), nullable=True),
    #             'err': Primitive(dtype('float32'), nullable=True),
    #             'val': Primitive(dtype('float32'), nullable=True)
    #           }),
    #         'dec': Record(
    #           name = 'ValueErr', 
    #           fields = {
    #             'lim': Primitive(dtype('bool'), nullable=True),
    #             'err': Primitive(dtype('float32'), nullable=True),
    #             'val': Primitive(dtype('float32'), nullable=True)
    #           }),
    #         'ra': Record(
    #           name = 'ValueErr', 
    #           fields = {
    #             'lim': Primitive(dtype('bool'), nullable=True),
    #             'err': Primitive(dtype('float32'), nullable=True),
    #             'val': Primitive(dtype('float32'), nullable=True)
    #           })
    #       }),
    #     'parallax': Record(
    #       nullable = True, name = 'ValueAsymErr', 
    #       fields = {
    #         'lim': Primitive(dtype('bool'), nullable=True),
    #         'loerr': Primitive(dtype('float32'), nullable=True),
    #         'val': Primitive(dtype('float32'), nullable=True),
    #         'hierr': Primitive(dtype('float32'), nullable=True)
    #       }),
    #     'gband': Record(
    #       name = 'ValueErr', 
    #       fields = {
    #         'lim': Primitive(dtype('bool'), nullable=True),
    #         'err': Primitive(dtype('float32'), nullable=True),
    #         'val': Primitive(dtype('float32'), nullable=True)
    #       })
    #   })

Records don't need to have names. If a record doesn't have a name, its type is defined solely by its field names and types; if it does have a name, its type also depends on the name. Thus, two records containing ``{"x": "float", "y": "float", "z": "float"}`` can be the same type if anonymous but different types if named "Position" and "Direction", for instance. (This is `structural typing <https://en.wikipedia.org/wiki/Structural_type_system>`_ by default and `nominal typing <https://en.wikipedia.org/wiki/Nominal_type_system>`_ if desired.)

Tuple
~~~~~

Tuples represent data that contains several types, but unlike records, the content fields are not named, they're numbered. These are also "`product types <https://en.wikipedia.org/wiki/Product_type>`_" for the same reason.

Tuples are fundamentally different from lists:

- list data can have any length, but the tuple length is fixed by the type schema;
- all elements of a list must have the same type (though that could be a union type), but each element of a tuple may have a different type (specified by the type schema).

Tuples and lists are more distinct from each other in a static typesystem than they are in a dynamic language like Python.

Here's an example of a tuple:

.. code-block:: python

    schema = List(Tuple(["int", "float", List("int")]))

    obj = schema({"object-c": [3],                       # length of outer list
                  "object-L-F0": [1, 2, 3],              # tuple field 0 contents
                  "object-L-F1": [1.1, 2.2, 3.3],        # tuple field 1 contents
                  "object-L-F2-c": [3, 0, 2],            # tuple field 2 list lengths
                  "object-L-F2-L": [1, 2, 3, 4, 5]})     # tuple field 2 list contents
    obj
    # [(1, 1.1, [1, 2, 3]), (2, 2.2, []), (3, 3.3, [4, 5])]

There's barely any difference between a record and a tuple, but sometimes you want to name your fields, sometimes you want to infer them from order.

Pointer
~~~~~~~

Pointers connect parts of an object to form trees, graphs, and help to save space by minimizing the number of times a large, complex object must be represented.

OAMap pointers are similar to pointers in a language like C, in that they reference an object by specifying its location with an integer, with two exceptions.

1. The address is an array index, not a native memory address. This allows OAMap object to be portable, because the native memory addresses can't be copied as-is from one process to another.
2. OAMap pointers are `bounded pointers <https://en.wikipedia.org/wiki/Bounded_pointer>`_, limited to a specified "target."

This second condition limits the power of the pointer mechanism, but for good reason. A pointer in C can point *anywhere,* even at objects of the wrong type (causing an incorrect cast; garbage data) or out of the memory owned by the process (causing a segmentation fault). OAMap pointers can only point to objects described by a given schema node. I see this limitation as analogous to the limitation imposed by programming with ``while`` loops instead of ``goto`` statements, since the options it eliminates are generally bad. If you want a pointer to point to multiple targets, you would simply make a union of pointers— unions allow you to approach unbounded pointers in the same way that unions allow you to approach dynamic typing (described above), letting you reintroduce these features in measured doses.

Pointers can be used in three topologies: (1) to point at another object within the same schema, but not its own parent, (2) to point at its parent object, creating a loop (the only way to make arbitrary depth trees and graphs in OAMap), and (3) to point to an external object.

Here's an example of the first case (pointing at another object within the same schema, but not its own parent):

.. code-block:: python

    # to link the schema to itself, temporarily set the pointer target to None
    schema = Record({"points": List(Tuple(["int", "int"])),
                     "line": List(Pointer(None))})

    # and then set it properly
    schema.fields["line"].content.target = schema.fields["points"].content

    # the print-out shows this internal connection with a "#0" label
    schema.show()
    # Record(
    #   fields = {
    #     'points': List(
    #       content = #0: Tuple(
    #         types = [
    #           Primitive(dtype('int64')),
    #           Primitive(dtype('int64'))
    #         ])
    #     ),
    #     'line': List(
    #       content = Pointer(
    #         target = #0
    #       )
    #     )
    #   })

    # Note: depending on the order of the fields, you might see this:
    # Record(
    #   fields = {
    #     'line': List(
    #       content = Pointer(
    #         target = #0: Tuple(
    #           types = [
    #             Primitive(dtype('int64')),
    #             Primitive(dtype('int64'))
    #           ])
    #       )
    #     ),
    #     'points': List(
    #       content = #0
    #     )
    #   })
    # It's the same thing!

    obj = schema({"object-Fpoints-c": [4],                         # number of points
                  "object-Fpoints-L-F0": [0, 0, 1, 1],             # point x values
                  "object-Fpoints-L-F1": [0, 1, 1, 0],             # point y values
                  "object-Fline-c": [3],                           # number of steps in line
                  "object-Fline-L-P-object-Fpoints-L": [0, 2, 1]   # which points the line connects
                 })
    obj.points
    # [(0, 0), (0, 1), (1, 1), (1, 0)]
    obj.line
    # [(0, 0), (1, 1), (0, 1)]

Connecting the dots is a generic-sounding application, but this feature is needed in particle physics to link measured tracks and showers to reconstructed particles without duplication. (Remember that these objects have hundreds of fields.)

Here's an example of the second case (pointing at a pointer's parent object, creating a loop):

.. code-block:: python

    schema = Record(
        name = "Tree",
        fields = dict(
            label = "float",
            children = List(Pointer(None))
        ))

    schema.fields["children"].content.target = schema

    schema.show()
    # #0: Record(
    #   name = 'Tree', 
    #   fields = {
    #     'children': List(
    #       content = Pointer(
    #         target = #0
    #       )
    #     ),
    #     'label': Primitive(dtype('int64'))
    #   })

    # Suppose we want to build this structure:
    # 
    # 1.1
    #  │
    #  ├── 2.2
    #  │    │
    #  │    ├── 4.4
    #  │    │    └── 7.7
    #  │    │
    #  │    └── 5.5
    #  │         └── 8.8
    #  │
    #  └── 3.3
    #       └── 6.6

    obj = schema({
        "object-NTree-Flabel": [1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7, 8.8],
        "object-NTree-Fchildren-c": [2, 2, 1, 1, 1, 0, 0, 0],
        "object-NTree-Fchildren-L-P-object-NTree": [1, 2, 3, 4, 5, 6, 7, 8]
        })

    obj
    # <Tree at index 0>
    obj.label, obj.children
    # (1.1, [<Tree at index 1>, <Tree at index 2>])
    obj.children[0].label, obj.children[0].children
    # (2.2, [<Tree at index 3>, <Tree at index 4>])
    obj.children[0].children[0].label, obj.children[0].children[0].children
    # (4.4, [<Tree at index 6>])
    obj.children[0].children[0].children[0].label, obj.children[0].children[0].children[0].children
    # (7.7, [])
    obj.children[0].children[1].label, obj.children[0].children[1].children
    # (5.5, [<Tree at index 7>])
    obj.children[0].children[1].children[0].label, obj.children[0].children[1].children[0].children
    # (8.8, [])
    obj.children[1].label, obj.children[1].children
    # (3.3, [<Tree at index 5>])
    obj.children[1].children[0].label, obj.children[1].children[0].children
    # (6.6, [])











Extension
~~~~~~~~~

Nullability
~~~~~~~~~~~





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
