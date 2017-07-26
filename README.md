## PLUR: efficient iterators for Primitives, Lists, Unions, and Records

Motivation for this project will go here.

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
