# PLUR

## TL;DR

PLUR is a way to encode complex objects made out of **Primitives**, **Lists**, **Unions**, and **Records** as plain Numpy arrays that can be loaded lazily for efficient columnar access. It can also rewrite Python code to dramatically reduce the runtime costs of Python and allow for further [acceleration with Numba](http://numba.pydata.org/).

In the example described below, a nested data structure takes 3 minutes to process as pre-loaded JSON, 25 seconds to process as PLUR proxies, 3.8 seconds to process by optimized Python code (still pure Python), and 0.03 seconds to process when that optimized code is compiled by Numba: a final single-threaded rate of 320 MB/sec (16 MHz for these events).

In each case, the user writes the same idiomatic Python code, as though these PLUR abstractions really were the Python lists and objects they mimic. The purpose is to minimize the total time to solution— human and computer.

## Table of contents

   1. [What's wrong with data frames?](#whats-wrong-with-data-frames)
   2. [PLUR: fast access to Primitives, Lists, Unions, and Records](#plur-fast-access-to-primitives-lists-unions-and-records)
   3. [Particle physics example](#particle-physics-example)
   4. [Relationship to other projects](#relationship-to-other-projects)
      1. [Femtocode](#relationship-to-femtocode)
      2. [Apache Arrow](#relationship-to-apache-arrow)
      3. [ROOT](#relationship-to-root)
      4. [Databases](#relationship-to-databases)
   5. [Project roadmap](#project-roadmap)

## In the wiki

   1. [Encoding scheme](../../wiki/Encoding-scheme), a language independent specification.
   2. [Review of columnar data representations](../../wiki/Review-of-columnar-data-representations), an overview of at least four fundamentally different approaches to the problem and how we settled on PLUR.

## What's wrong with data frames?

Many data analysis procedures, particularly in high energy physics, can't work exclusively with a rectangular table of data (i.e. a "data frame" or "flat ntuple"). Sometimes you need an arbitrary-length list of particles or even nested lists.

For instance, a dataset naturally expressed as

```
[Event(met=MET(x=55.3, y=78.3),
       muons=[Muon(px=25.6, py=-7.9, pz=100.6), Muon(px=-17.5, py=-12.9, pz=87.5)]),   # two muons
 Event(met=MET(x=52.8, y=-109.2),
       muons=[]),                                                                      # no muons
 Event(met=MET(x=97.6, y=45.8),
       muons=[Muon(px=-22.9, py=-31.6, pz=130.5)])]                                    # one muon
```

can be forced into

| Event # | MET x |  MET y | Muon1 px | Muon1 py | Muon1 pz |
|--------:|------:|-------:|---------:|---------:|---------:|
|       0 |  55.3 |   78.3 |     25.6 |     -7.9 |    100.6 |
|       1 |  52.8 | -109.2 |      ??? |      ??? |      ??? |
|       2 |  97.6 |   45.8 |    -22.9 |    -31.6 |    130.5 |

but only at the expense of truncating or padding the list of muons.

Alternatively, it could be exploded into

| Muon # | Event id | MET x |  MET y | Muon px | Muon py | Muon pz |
|-------:|---------:|------:|-------:|--------:|--------:|--------:|
|      0 |        0 |  55.3 |   78.3 |    25.6 |    -7.9 |   100.6 |
|      1 |        0 |  55.3 |   78.3 |   -17.5 |   -12.9 |    87.5 |
|      2 |        2 |  97.6 |   45.8 |   -22.9 |   -31.6 |   130.5 |

at the expense of duplicating MET data in events with multiple muons and losing MET data in events without muons. Furthermore, only one list can be exploded this way: we can't do it for two or more particle types in the same event.

Finally, we could resort to [normal form](https://en.wikipedia.org/wiki/Database_normalization), making a separate table for each type of particle and then performing SQL `JOIN` operations on the event id. But not only does this [vastly complicate the analysis](https://stackoverflow.com/q/38831961/1623645), it also discards the close association between particles in the same event, which must be rediscovered by the potentially expensive join.

Often a data analyst starts optimistically with flat tables, hoping to benefit from fast processing due to lazy, columnar data access and term rewriting, but then must re-express the analysis as code once nested types become necessary, and then again, converting from Python to C++ as the size of the dataset grows.

Ideally, we'd want simple Python code to analyze any kind of data as fast as a database query.

## PLUR: fast access to Primitives, Lists, Unions, and Records

PLUR is a way to encode complex, hierarchical data in plain Numpy arrays. The acronym stands for the four basic generators of the typesystem:

   * **Primitive:** fixed-width types: the booleans, ints, floats, and complex numbers of Numpy.
   * **List:** arbitrary-length lists of any other types, including nested lists.
   * **Union:** represents objects that can be one of several types ("sum types" in type theory).
   * **Record:** represents objects that contain several types ("product types" in type theory).

As an example, a list of lists of integers or x-y pairs would be represented as

```
List(List(Union(int32, Record(x=float64, y=float64))))
```

Data of interest to just about any analysis can be represented as some combination of the above. For instance,

   * Collections of physics events containing particles containing raw measurements are lists of records of lists of records of lists of records.
   * Unicode strings are `List(uint8)` where subsequences of bytes are interpreted as characters.
   * Limited-scope pointers are integers representing indexes into some other list. This includes what is known as an event list: a representation of a filtered dataset that names the selected entries, rather than copying them, which makes these skims very lightweight for storage.
   * Nullable/optional types X (the "maybe monad") are `List(X)` with list lengths of 0 or 1, interpreting empty lists as `None`.
   * Lookup tables from X to Y are `List(Record(key=X, value=Y))`, read into a runtime structure optimized for lookup, such as a hashmap.

PLUR is a scheme to encode any hierarchical data that can be described by those four generators as a set of flat arrays. An implementation of PLUR, such as the Python/Numpy implementation in this package, only needs to get the four generators right, as well as their interactions, so there's on the order of sixteen tests to verify correctness. That's why it pays to keep the fundamental set of generators small.

A PLUR implementation should have

   * methods to convert data into and out of arrays,
   * methods to view arrays as objects, lazily with proxies,
   * possibly methods to "compile away" the abstraction, so that nothing is present at runtime but indexes into the arrays.

This package implements all three for Python and Numpy.

It's worth emphasizing that PLUR is not a file format: a file format specifies how data are encoded as bytes on disk, while PLUR specifies how one abstraction, hierarchical data, is encoded in another, a namespace of flat arrays. Numpy has several natural serializations— `.npy` files, `.npz` files, `.pkl` files, HDF5 files through PyTables, or even ROOT files. However, these arrays could also be stored as a web server that responds to URL names with array data or in a key-value object store over a network.

There are three layers of abstraction:

|   |
|:-:|
| runtime interpretation (e.g. Unicode string rather than `List(uint8)` |
| hierarchical data: PLUR proxies or translated code |
| namespace of flat arrays: Numpy, HDF5, object store, etc. |

PLUR's data representation is columnar, meaning that all values of an attribute at a given level of hierarchy are stored contiguously in the same array. This improves data access in several ways:

   1. Only the attributes actually used by the calculation need to be read. For objects with many attributes, limited by the reading rate of the physical medium (disk), this can be a huge speedup. The particle physics community has benefited from [this feature of ROOT](https://root.cern.ch/root/InputOutput.html) for many years, but PLUR goes further in not reconstructing objects even after reading. This solves a problem in which selective reading lets you read muons and not electrons if you're only interested in muons, but you still have to read all attributes of a muon to construct the object. With PLUR's proxies, unused attributes at any level may be left unread.
   2. Future analysis code with modified data types can read old data, as long as all the required attributes are there. This is known [in ROOT as schema evolution](https://root.cern.ch/root/SchemaEvolution.html), but in Python it's just [duck typing](https://en.wikipedia.org/wiki/Duck_typing). Even in a statically typed context, PLUR's Record types are [structurally typed](https://en.wikipedia.org/wiki/Structural_type_system): they have no names, so the only restriction on passing an object to a function is that it has the field names and types that the function expects. This is relevant for compiling PLUR accessors with Numba. A schema evolution that changes field names would only involve column name mapping in PLUR.
   3. Contiguous data can be paged into RAM from disk (e.g. in memory-mapped Numpy files) or [paged into CPU cache from RAM](https://lwn.net/Articles/250967/) in a predictable way. If objects are constructed on the heap at runtime, even a sequential scan through events would require random memory access. A sequential scan through a PLUR List is sequential in the array source, whether that is disk or RAM.
   4. Datasets can share arrays, particularly new versions of datasets that differ from old ones by only a few additional or removed fields. This is an extreme form of [ROOT's tree-friend concept](https://root.cern.ch/root/html534/guides/users-guide/Trees.html#example-3-adding-friends-to-trees): PLUR's datasets are such loosely bound collections of columns that they are completely formed out of friends. The technique is more generally known as [structural sharing](https://en.wikipedia.org/wiki/Persistent_data_structure). Event lists (described above) allow even skims to share data: the memory cost of skimming an entire dataset is just the cost of storing one new array.

Let's illustrate the PLUR concept and its Python/Numpy implementation with an example.

## Particle physics example

To follow along, check out [Revision 167](https://github.com/diana-hep/plur/releases/tag/rev167) and

```bash
python setup.py install --user
```

The only explicit dependency is Numpy, though the last step requires Numba (installable with [Conda](https://conda.io/miniconda.html)).

In a Python session, define some types:

```python
from plur.types import *

Jet      = Record(px=float64, py=float64, pz=float64, E=float64, btag=float64)
Muon     = Record(px=float64, py=float64, pz=float64, E=float64, q=int8, iso=float64)
Electron = Record(px=float64, py=float64, pz=float64, E=float64, q=int8, iso=float64)
Photon   = Record(px=float64, py=float64, pz=float64, E=float64, iso=float64)
MEt      = Record(px=float64, py=float64)

Event = Record(jets               = List(Jet),
               muons              = List(Muon),
               electrons          = List(Electron),
               photons            = List(Photon),
               MET                = MEt,
               numPrimaryVertices = int32)
```

Now we will load half a million events of type `List(Event)` from a JSON file.

```python
import json
import zlib
try:
    import urllib2                       # Python 2
except ImportError:
    import urllib.request as urllib2     # Python 3

URL = "http://histogrammar.org/docs/data/triggerIsoMu24_50fb-1.json.gz"

# About 20 seconds to download and decompress.
jsonlines = zlib.decompressobj(16 + zlib.MAX_WBITS) \
                .decompress(urllib2.urlopen(URL).read()) \
                .split("\n")

# Must generate dicts on the fly to avoid running out of memory!
def generate():
    for line in jsonlines:
        if line != "":
            yield json.loads(line)
```

The Python dicts generated from the JSON use so much memory that I can't load them all on my laptop. Therefore, we pass `toarrays` a generator to fill the much more compact PLUR representation. (We could also stream directly to files to avoid any growth in memory use.)

```python
from plur.python import toarrays

# About 3 minutes to parse the JSON, make Python dictionaries, and fill.
arrays = toarrays("events", generate(), List(Event))
```

Now the data structures are just a set of Numpy arrays. Some arrays store data, some represent structure, and even the names encode the type structure (losslessly). Each one-dimensional array may be thought of as a "column" in the database sense (i.e. "split mode" in ROOT).

```python
>>> list(arrays.keys())
['events-Lo',
'events-Ld-R_photons-Lo',
'events-Ld-R_photons-Ld-R_pz',
'events-Ld-R_photons-Ld-R_py',
'events-Ld-R_photons-Ld-R_px',
'events-Ld-R_photons-Ld-R_iso',
'events-Ld-R_photons-Ld-R_E',
'events-Ld-R_numPrimaryVertices',
'events-Ld-R_muons-Lo',
'events-Ld-R_muons-Ld-R_q',
'events-Ld-R_muons-Ld-R_pz',
'events-Ld-R_muons-Ld-R_py',
'events-Ld-R_muons-Ld-R_px',
'events-Ld-R_muons-Ld-R_iso',
'events-Ld-R_muons-Ld-R_E',
'events-Ld-R_MET-R_py',
'events-Ld-R_MET-R_px',
'events-Ld-R_jets-Lo',
'events-Ld-R_jets-Ld-R_pz',
'events-Ld-R_jets-Ld-R_py',
'events-Ld-R_jets-Ld-R_px',
'events-Ld-R_jets-Ld-R_E',
'events-Ld-R_jets-Ld-R_btag',
'events-Ld-R_electrons-Lo',
'events-Ld-R_electrons-Ld-R_q',
'events-Ld-R_electrons-Ld-R_pz',
'events-Ld-R_electrons-Ld-R_py',
'events-Ld-R_electrons-Ld-R_px',
'events-Ld-R_electrons-Ld-R_iso',
'events-Ld-R_electrons-Ld-R_E']
```

Use Numpy's `savez` to save them all to an uncompressed zip file (or `savez_compressed` for compression).

```python
import numpy
numpy.savez(open("triggerIsoMu24_50fb-1.npz", "wb"), **arrays)
```

| Format           |   Size |
|:-----------------|-------:|
| JSON             | 114 MB |
| JSON compressed  |  28 MB |
| Numpy            |  39 MB |
| Numpy compressed |  13 MB |

Exit Python and open a new Python shell. The file opens in a fraction of a second regardless of how large it is.

```python
import numpy
arrays = numpy.load(open("triggerIsoMu24_50fb-1.npz"))

from plur.python import fromarrays
events = fromarrays("events", arrays)
```

We can now access any event and any object in the events without noticible lag. If the arrays were memory-mapped files, the operating system would seek to the appropriate parts of the file and page them into memory just in time. Our example uses a ZIP file, which reads and possibly decompresses the appropriate array from the file on demand.

```python
>>> print(events[0])
events(MET=MET(px=-8.6744089126586914, py=21.898799896240234),
       electrons=[],
       jets=[],
       muons=[muons(E=141.13978576660156, iso=0.0, px=4.8594961166381836, py=-30.239873886108398, pz=137.7764892578125, q=-1)],
       numPrimaryVertices=7,
       photons=[])

>>> print(events[-1])
events(MET=MET(px=-15.61468505859375, py=22.061094284057617),
       electrons=[],
       jets=[],
       muons=[muons(E=80.679710388183594, iso=0.0, px=28.932826995849609, py=1.5360887050628662, pz=75.297653198242188, q=1)],
       numPrimaryVertices=9,
       photons=[])

>>> print(events[-100].muons[0].iso)
3.68770575523
```

We can even inspect the data type, which was encoded in the array names. More than one data structure can be stored in a single namespace— name prefixes (`"events"` in this example) keep them separate.

```python
>>> from plur.types import *
>>> arrays2type(arrays, "events")
List(Record(MET                = Record(px=float64, py=float64),
            electrons          = List(Record(E=float64, iso=float64, px=float64, py=float64, pz=float64, q=int8)),
            jets               = List(Record(E=float64, btag=float64, px=float64, py=float64, pz=float64)),
            muons              = List(Record(E=float64, iso=float64, px=float64, py=float64, pz=float64, q=int8)),
            numPrimaryVertices = int32,
            photons            = List(Record(E=float64, iso=float64, px=float64, py=float64, pz=float64))))
```

We can use the same proxies to loop over the data: the following loop computes and adds up the momentum of all muons in all events. Arbitrarily complex loops are possible, including back-tracking and cross-referencing among structures, event data and non-event data. Although any order is possible, sequential access is generally faster than non-sequential access for the normal disk-paging and CPU-caching reasons.

```python
import math

psum = 0.0
for event in events:
    for muon in event.muons:
        psum += math.sqrt(muon.px**2 + muon.py**2 + muon.pz**2)

print(psum)
```

On my laptop, this took 25 seconds. Only five of the thirty arrays were actually loaded (9.5 MB of the 38 MB). Most of this time is spent creating and destroying proxy objects, which are Python class instances pointing to relevant parts of the arrays. In principle, all we need to pass around is an index for each non-primitive object: extracting items from lists, instances of a union, or attributes from a record just requires a special interpretation of that index.

As an alternative to passing proxy objects in dynamic Python, we could translate the Python code to pass integer indexes and interpret them correctly. This involves something like a compiler pass, propagating PLUR data types through the code to insert index interpretations at the appropriate places, which can be performed rigorously at the level of [abstract syntax trees](https://en.wikipedia.org/wiki/Abstract_syntax_tree).

This PLUR implementation has experimental support for code transformation, though the interface is currently rough (no error checking!). We can't use foreach-style loops yet, but eventually we'll be able to put exactly the same code that works with proxies into the code transformation tool and get a large speedup for free.

Here's an illustration:

```python
import math
from plur.types import *
from plur.compile import local

def doit(events):
    psum = 0.0
    for i in range(len(events)):
        for j in range(len(events[i].muons)):
            psum += math.sqrt(events[i].muons[j].px**2 +
                              events[i].muons[j].py**2 +
                              events[i].muons[j].pz**2)
    return psum

fcn, arrayparams = local(doit, arrays2type(arrays, "events"), environment={"math": math})
fcn(*[arrays[x] for x in arrayparams])
```

On the same laptop, this took 3.8 seconds: six times faster to do exactly the same work. Note that this is all still Python code, rearranged for faster access (we "compiled the abstractions away").

In this form, it is also possible for Numba to compile the function to native bytecode (no Python at runtime). The code transformation was necessary because Numba understands integer indexes better than dynamic Python objects. If you have Numba installed, try adding a single parameter `numba=True` to the code transformation for another factor of a hundred in speedup:

```python
fcn, arrayparams = local(doit, arrays2type(arrays, "events"), environment={"math": math}, numba=True)
fcn(*[arrays[x] for x in arrayparams])
```

The first time the function is called, it takes 0.98 seconds to compile, but afterward it takes 0.03 seconds: a single-threaded rate of 320 MB/sec (16 MHz for these events). Now imagine parallelizing it.

With all the hierarchical data in PLUR objects that get compiled away, this function consists of nothing but numbers, for loops, and mathematical function calls, something that Numba's LLVM-based optimizer can optimize as well as C or C++. And yet it was not any more arduous to write— the same for loop you might use to explore the first few events scales up to huge datasets without assistance on your part.

You just write analysis code on complex objects in Python and get database-style speeds.

## Relationship to other projects

### Relationship to [Femtocode](https://github.com/diana-hep/femtocode)

PLUR could be seen as a (temporary!) de-scoping of Femtocode. Femtocode was intended as a query language for a HEP query service with an execution engine that optimizes code for columnar, hierarchical data. PLUR is just the columnar, hierarchical data, implementing fast data access and not a whole language.

The HEP query service we are developing is likely to use Python as a query language, accelerated by PLUR and Numba. Femtocode would be a later enhancement, and is likely to be rewritten on top of PLUR.

### Relationship to [Apache Arrow](https://arrow.apache.org/)

After much exploration (four [fundamentally different data representations](../../wiki/Review-of-columnar-data-representations)), I've come to the conclusion that Arrow's chain of offset arrays is the best way to access hierarchical data. It allows for random access, letting us access event data and non-event data in the same framework, and it's simple enough for term rewriting in a complex, procedural language like Python.

The differences between Arrow and PLUR are:

   1. Arrow defines the relative placemment of its columnar buffers; PLUR lets them be any Numpy arrays anywhere (including disk via memory-mapped files). Therefore, PLUR arrays can be copied into Arrow buffers with a bulk `memcpy` operation, while Arrow buffers can be zero-copy interpreted as PLUR arrays.
   2. PLUR implements fast accessors over the data. In the future, PLUR could be used as a way of writing Python routines that run fast on Arrow data, such as a Pandas/R/Spark DataFrame.
   3. PLUR has no dependencies other than Numpy and maybe Numba, so it's easy to install.

### Relationship to [ROOT](https://root.cern/)

PLUR shares many concepts with the ROOT file format, but there are differences. First, PLUR is not a data format: one could use ROOT as a source and storage for PLUR data structures (converting Numpy arrays to and from ROOT TBranches). But more significantly,

   1. The goal of ROOT serialization is to store and retrieve arbitrary C++ objects, essentially like a C++ version of Python's pickle. PLUR encodes data adhering to a language-independent type system, which is intentionally kept small for simplicity.
   2. ROOT materializes data as ordinary C++ objects so that C++ code can run on them. PLUR uses Python's dynamism or instruments compiled code to provide the illusion that the Python code is operating on objects, when in fact it is operating on array indexes that produce the required object attributes as needed.
   3. Data can be modified in-place with ROOT; PLUR objects are immutable. Modifying a PLUR dataset, such as updating attribute values, actually creates a new column to be used in conjunction with the old columns like a diff-patch.
   4. ROOT schema evolution is complicated by the fact that C++ is a nominally typed language: classes must have the same name; it's not enough to have the right attributes.

ROOT and PLUR can be used together: I am currently implementing fast, native Numpy access to ROOT TTrees so that ROOT data can be streamed through PLUR proxies.

Moreover, the [PLUR specification](../../wiki/Encoding-scheme) is language-neutral: it could be implemented in [Cling, a just-in-time C++ compiler](https://root.cern.ch/cling). The code transformations that provide the fastest access can be implemented more easily with C++ metaprogramming than the Python code transformation.

### Relationship to databases

PLUR is being developed specifically for use in a service that aggregates particle physics data in response to user queries. This is why database-style columnar data and term rewriting are important. However, PLUR can be used by itself to analyze any data, as the example above shows.

One important distinction between a real database and distributed PLUR is that databases maintain indexes over some fields for faster lookup than a sequential scan. PLUR is not just compatible with adding an index: the event list concept (described above) is a good way to interface the two.

An event list is a usually sorted, always unique list of pointers into a collection like `List(Event)`. The "pointers" themselves are just indexes in that collection (not raw memory pointers!). Event lists are the result of skims, so that a skim can be represented by one new column, rather than a copy of a subset of rows for every column of the original dataset.

Database indexes are a copy of the most relevant columns as sorted trees or other structures for particular kinds of access. These database tables could be maintained alongside a PLUR dataset with a column that represents the PLUR index. When the database selects a subset of rows, it can present them to PLUR as an event list for rapid iteration over the results.

To a user, this would require a combined query: an SQL part (for the database) followed by a Python part (for PLUR) to be executed on the selected entries. Femtocode could simplify this into a single expression.

## Project roadmap

   * Define the PLUR representation **(done)**.
   * Conversion of Python objects into PLUR **(done)**.
   * Proxies to view PLUR data as lazily-loaded Python objects **(done)**.
   * Transform code to "compile away" the PLUR abstraction **(started)**.
      * Square brackets for lists and attribute access for records **(done)**.
      * Test all combinations of primitives, lists, unions, and records **(done)**.
      * `len` function for lists **(done)**.
      * `for` loop iteration.
      * `enumerate`, `zip`, etc.
      * Assignment carries PLUR type through type inference.
   * Good error messages, catching PLUR type errors at compile time.
   * Maybe require Femtocode-style constraints on list indexes and union members to eliminate this type of runtime error.
   * Simple extension types, such as strings (`List(uint8)`), nullable/optional (`List(X)`), and pointers (`int64` with a list reference).
   * Use pointers as event lists and database-style indexes: essential for query engine.
   * Integrate with ROOT, zero-copy interpreting internal TBuffer data as PLUR data (requires ROOT updates).
