# PLUR

## TL;DR

PLUR is a way to encode complex objects made out of **Primitives**, **Lists**, **Unions**, and **Records** as plain Numpy arrays that can be loaded lazily for efficient columnar access. It can also rewrite Python code to dramatically reduce the runtime costs of Python and allow for further [acceleration with Numba](http://numba.pydata.org/).

In the example described below, a nested data structure takes 3 minutes to process as pre-loaded JSON, 25 seconds to process as PLUR proxies, 3.8 seconds to process by optimized Python code (still pure Python), and 0.03 seconds to process when that optimized code is compiled by Numba: a final single-threaded rate of 320 MB/sec (16 MHz for these events).

In each case, the user writes the same idiomatic Python code, as though these PLUR abstractions really were the Python lists and objects they mimic. The purpose is to minimize the total time to solution— human and computer.

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

Data of interest to most analyses can be represented as some combination of the above. For instance,

   * Unicode strings are `List(uint8)` where subsequences of bytes are interpreted as characters.
   * Limited-scope pointers are integers representing indexes into some other list.
   * Nullable/optional types X (the "maybe monad") are `List(X)` with list lengths of 0 or 1, interpreting empty lists as `None`.
   * Lookup tables from X to Y are `List(Record(key=X, value=Y))`, read into a runtime structure optimized for lookup, such as a hashmap.

There are three layers of abstraction here: types of objects generated at runtime (such as `str` from `List(uint8)`), the PLUR types that are directly encoded in Numpy, and the Numpy arrays themselves.

To move a large dataset, we only need to move a subset of the Numpy arrays— everything else can be reconstructed. "Move" might mean network transfers, reading data from disk, or paging RAM through the CPU cache.

## Particle physics example

To follow along, check out [Revision 166](https://github.com/diana-hep/plur/releases/tag/rev166) and

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

The Python dictionaries generated from the JSON use so much memory that I can't load them all on my laptop. Therefore, we pass `toarrays` a generator to fill the much more compact PLUR representation. (We could also stream directly to files to avoid any growth in memory use.)

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

Now exit Python and open a new Python shell. The file opens in a fraction of a second.

```python
import numpy
arrays = numpy.load(open("triggerIsoMu24_50fb-1.npz"))

from plur.python import fromarrays
events = fromarrays("events", arrays)
```

We can immediately access any event and any object in the events.

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

We can even inspect the data _type,_ which was encoded in the array names. More than one data structure can be stored in a single namespace— name prefixes (`"events"` here) keep them separate.

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

The data are loaded on demand by proxies. List proxies like `events` yield event records when requested by square brackets and event records yield their contents when requested by attributes. If the arrays are in a Numpy file or a memory-mapped file, they won't be loaded if not needed. In fact, a memory-mapped file can be many times larger than your computer's memory and still be accessible on demand.

The following loop iterates over all muons in all events and adds up their momenta. Arbitrarily complex loops are possible, including cross-references between two structures, but non-sequential access is usually slower than sequential (for the normal disk-paging and CPU-caching reasons).

```python
import math

psum = 0.0
for event in events:
    for muon in event.muons:
        psum += math.sqrt(muon.px**2 + muon.py**2 + muon.pz**2)

print(psum)
```

On my laptop, this took 25 seconds. Only five of the thirty arrays were actually loaded (9.5 MB of the 38 MB). Though convenient for taking a quick look at the data, the proxies are not the most efficient way to iterate over data because they create and destroy objects at runtime.

Each primitive, list, union, and record could be represented at runtime by a single number each, which has much less overhead than a proxy instance. Knowing the data type, we can propagate types through the code to replace proxies with simple numbers.

The interface is currently rough, requiring us to use explicit brackets rather than iterators (and no error reporting!), but eventually no code changes will be required for faster access through term rewriting. The following is a kind of compilation, transforming Python to Python, using type inference and rigorous AST manipulation.

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

On the same laptop, this took 3.8 seconds: six times faster. Note that this is all still Python code, just rearranged for faster access (we "compiled the abstractions away").

It's also in a form that can be compiled to native bytecode (no Python at runtime) by Numba. If you have Numba installed, the same two lines with `numba=True` speeds it up by another factor of a hundred:

```python
fcn, arrayparams = local(doit, arrays2type(arrays, "events"), environment={"math": math}, numba=True)
fcn(*[arrays[x] for x in arrayparams])
```

The first time the function is called, it takes 0.98 seconds to compile. Thereafter, it takes 0.03 seconds. There are no Python objects or memory allocations objects in the loop: it would not be any faster if it were written in C++. And yet, it's the same Python analysis code we'd write to explore a handful of events.

## Project roadmap

**Relationship to [Femtocode](https://github.com/diana-hep/femtocode):** Femtocode is a totally functional language with dependent types, intended for high-level data queries. The columnar representation described here is the central idea of the Femtocode execution engine: PLUR is a simpler project that focuses only on accessing data, which can be used in any procedural code. In fact, PLUR can be reimplemented in any language with JIT-compilation (such as [C++ Cling](https://root.cern.ch/cling): hint to ROOT developers).

Femtocode is intended for a future HEP query engine, but Numba and PLUR would be easier to implement in the short term. The HEP query engine is likely to use Python as a query language before Femtocode is ready, and Femtocode itself is likely to be written on top of PLUR.

**Relationship to [Apache Arrow](https://arrow.apache.org/):** after much exploration (four fundamentally different data representations: recursive counters, Parquet-style, Arrow-style, and normal form), I've come to the conclusion that Arrow's chain of offset arrays is the best way to access hierarchical data. It allows for random access, letting us access event data and non-event data in the same framework, and it's simple enough for term rewriting in a complex, procedural language like Python.

The differences are:

   1. PLUR has no dependencies other than Numpy and maybe Numba, so it's easy to install.
   2. Arrow defines the relative placemment of its columnar buffers; PLUR lets them be any Numpy arrays anywhere (including disk via memory-mapped files). Therefore, PLUR arrays can be copied into Arrow buffers with a bulk `memcpy` operation, while Arrow buffers can be zero-copy interpreted as PLUR arrays.
   3. PLUR implements fast accessors for the data. In the future, PLUR could be used as a way of writing Python routines that run on Arrow data, such as a Pandas/R/Spark DataFrame.

### Steps

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

At the same time, ROOT is being updated to expose TBuffer data as Numpy arrays. Also, a distributed query service is being developed, which will use PLUR as an execution engine.
