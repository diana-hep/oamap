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

class JsonEvents(object):
    URL = "http://histogrammar.org/docs/data/triggerIsoMu24_50fb-1.json.gz"

    def __init__(self):
        compressed = urllib2.urlopen(self.URL).read()
        decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS)
        self.astext = decompressor.decompress(compressed).split("\n")

    def __len__(self):
        return len(self.astext)

    def __iter__(self):
        def generate():
            for line in self.astext:
                if line != "":
                    yield json.loads(line)
        return generate()

# about 20 seconds to download and decompress
jsonEvents = JsonEvents()
```


```python
from plur.python import toarrays

# about 3 minutes to parse the JSON, make Python dictionaries, and fill
arrays = toarrays("events", jsonEvents, List(Event))
```

```python
import numpy
numpy.savez(open("triggerIsoMu24_50fb-1.npz", "wb"), **arrays)
```

or `numpy.savez_compressed` for zlib compression.

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
events = fromarrays("events", arrays)
```

