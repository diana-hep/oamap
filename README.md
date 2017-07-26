# PLUR

## TL;DR

PLUR is a way to encode complex objects made out of **Primitives**, **Lists**, **Unions**, and **Records** as plain Numpy arrays that can be loaded lazily for efficient columnar access. It can also rewrite Python code to dramatically reduce the runtime costs of Python and to allow for further [acceleration with Numba](http://numba.pydata.org/).

In the example described below, a nested structure takes 3 minutes to process as JSON and Python dicts, 25 seconds to process as PLUR proxies, 3.8 seconds to process as rewritten code (still pure Python), and 0.03 seconds to process when compiled with Numba. That's a factor of 6000 from JSON/dicts to Numba.

In each case, the user writes the same idiomatic Python code, as though these PLUR objects really were the Python lists and objects they resemble. The purpose is to minimize the total time to solution— human and computer.

## What's wrong with data frames?

Many data analysis procedures, particularly in high energy physics, can't work exclusively with a table of rectangular data (i.e. a "data frame" or "flat ntuple"). Sometimes you need an arbitrary-length list of particles or even nested lists, not just numbers.

For instance, a dataset naturally expressed as

```
[Event(met=MET(x=55.3, y=78.3),
       muons=[Muon(px=25.6, py=-7.9, pz=100.6), Muon(px=-17.5, py=-12.9, pz=87.5)]),
 Event(met=MET(x=52.8, y=-109.2),
       muons=[]),
 Event(met=MET(x=97.6, y=45.8),
       muons=[Muon(px=-22.9, py=-31.6, pz=130.5)])]
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

at the expense of duplicating MET data in events with multiple muons and losing MET data in events without muons. Furthermore, only one list in the event can be exploded: we can't do this for two or more particle types.

Finally, one could resort to [normal form](https://en.wikipedia.org/wiki/Database_normalization), making a separate table for each type of particle and then performing SQL `JOIN` operations on the event id. But not only does this complicate the analysis, it also discards the close association between particles in the same event, which must be rediscovered by the potentially expensive join.

Often an analyzer starts optimistically with flat tables, hoping to benefit from the efficiency of lazy, columnar data access, but must rewrite the analysis once nested types become necessary.

Ideally, we'd want fast access with any kind of data.

## PLUR: fast access to Primitives, Lists, Unions, and Records

PLUR is a way to encode complex, hierarchical data in plain Numpy arrays. The acronym stands for the four basic generators of the typesystem:

   * **Primitive:** fixed-width types: the booleans, numbers, and ASCII characters of Numpy.
   * **List:** arbitrary-length lists of any other types, including nested lists.
   * **Union:** represents objects that can be one of several types ("sum types" in type theory).
   * **Record:** represents objects that contain several types ("product types" in type theory).

As an example, a list of lists of objects that can be integers or x-y pairs would be represented as

```
List(List(Union(int32, Record(x=float64, y=float64))))
```

All objects of interest to most data analyses can be represented as some combination of the above. For instance,

   * Unicode strings are `List(uint8)` where combinations of `uint8` bytes are interpreted as characters.
   * Limited-scope pointers are integers representing indexes in some other list.
   * Lookup tables from X to Y are `List(Record(key=X, value=Y))`, read into a runtime structure optimized for lookup, such as a hashmap.

In general, there are three levels of abstraction: the data types generated at runtime (such as `str` from `List(uint8)`), the PLUR types that are directly encoded in Numpy, and the Numpy arrays themselves.

To move a large dataset, one only needs to move a subset of the Numpy arrays— everything else can be reconstructed.

# Other stuff

```python
from plur.types import *

Jet      = Record(px=float64, py=float64, pz=float64, E=float64, btag=float64)
Muon     = Record(px=float64, py=float64, pz=float64, E=float64, q=int8, iso=float64)
Electron = Record(px=float64, py=float64, pz=float64, E=float64, q=int8, iso=float64)
Photon   = Record(px=float64, py=float64, pz=float64, E=float64, iso=float64)
MET      = Record(px=float64, py=float64)

Event = Record(jets               = List(Jet),
               muons              = List(Muon),
               electrons          = List(Electron),
               photons            = List(Photon),
               MET                = MET,
               numPrimaryVertices = int32)
```


```python
import json
import zlib
try:
    import urllib2
except ImportError:
    import urllib.request as urllib2

URL = "http://histogrammar.org/docs/data/triggerIsoMu24_50fb-1.json.gz"

# about 20 seconds to download and decompress
jsonlines = zlib.decompressobj(16 + zlib.MAX_WBITS) \
                .decompress(urllib2.urlopen(URL).read()) \
                .split("\n")

# have to generate dicts on the fly to avoid running out of memory!
def generate():
    for line in jsonlines:
        if line != "":
            yield json.loads(line)
```

```python
from plur.python import toarrays

# about 3 minutes to parse the JSON, make Python dictionaries, and fill
arrays = toarrays("events", generate(), List(Event))
```

```python
import numpy
numpy.savez(open("triggerIsoMu24_50fb-1.npz", "wb"), **arrays)
```

or use the `numpy.savez_compressed` function for zlib compression.

| Format           |   Size |
|:-----------------|-------:|
| JSON             | 114 MB |
| JSON compressed  |  28 MB |
| Numpy            |  39 MB |
| Numpy compressed |  13 MB |

Close and reopen Python.

```python
import numpy
arrays = numpy.load(open("triggerIsoMu24_50fb-1.npz"))

from plur.python import fromarrays

# loads (lazily) in a fraction of a second
events = fromarrays("events", arrays)
```

Random access to any event, any object in the event.

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

Note that we were able to read these _typed_ objects from a pure Numpy file: the data types are encoded in the array names.

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

```python
import math

psum = 0.0
for event in events:
    for muon in event.muons:
        psum += math.sqrt(muon.px**2 + muon.py**2 + muon.pz**2)

print(psum)
```

On my machine, it took 25 seconds to walk through all the muons and compute momenta. Despite appearances, no lists or muon objects were created, only proxies to them. Only arrays necessary for the compuation (9.5 MB in this example) are actually loaded, not all of them (38 MB).

```python
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

3.8 seconds

```python
fcn, arrayparams = local(doit, arrays2type(arrays, "events"), environment={"math": math}, debug=True)
fcn(*[arrays[x] for x in arrayparams])
```

0.98 seconds the first time (compilation), followed by 0.03 seconds each subsequent time (execution only).
