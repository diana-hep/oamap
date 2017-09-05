#!/usr/bin/env python

import re

import numpy
import ROOT

from plur.types import *
from plur.types.primitive import withrepr
from plur.types.arrayname import ArrayName
from plur.python import fromarrays

# file = ROOT.TFile("/home/pivarski/data/nano-2017-09-01.root")
file = ROOT.TFile("../compression-tests2/nano-TTLHE-2017-09-04-uncompressed.root")
tree = file.Get("Events")

leaves = list(tree.GetListOfLeaves())

for leaf in leaves:
    counter = leaf.GetLeafCount()
    if counter:
        try:
            index = leaves.index(counter)
        except ValueError:
            pass
        else:
            del leaves[index]

seen = []
packages = {}
for leaf in leaves:
    if len(leaf.GetBranch().GetListOfLeaves()) != 1:
        raise TypeError("TLeaf \"{0}\" is not the only leaf in TBranch \"{1}\"".format(leaf.GetName(), leaf.GetBranch().GetName()))

    path = leaf.GetName().split("_")
    if path[0] == "HLT":
        path = [path[0]] + ["_".join(path[1:])]

    for x in seen:
        for i in range(len(path)):
            if x == path[:i + 1]:
                path = path[:i] + ["_".join(path[i:])]
                break
    seen.append(path)

    pack = packages
    for item in path[:-1]:
        if item not in pack:
            pack[item] = {}
        pack = pack[item]

    pack[path[-1]] = leaf

def toplurtype(pack, name, allowcounters):
    if not isinstance(pack, dict):
        typename = pack.GetTypeName()
        if typename == "Char_t":
            tpe = withrepr(int8, copy=True)
        elif typename == "UChar_t":
            tpe = withrepr(uint8, copy=True)
        elif typename == "Int_t":
            tpe = withrepr(int32, copy=True)
        elif typename == "UInt_t":
            tpe = withrepr(uint32, copy=True)
        elif typename == "Long64_t":
            tpe = withrepr(int64, copy=True)
        elif typename == "ULong64_t":
            tpe = withrepr(uint64, copy=True)
        elif typename == "Float_t":
            tpe = withrepr(float32, copy=True)
        elif typename == "Double_t":
            tpe = withrepr(float64, copy=True)
        else:
            raise NotImplementedError, typename

        title = pack.GetBranch().GetTitle()
        check = re.sub("/[CBbSsIiFDLlo]$", "", title)
        if check != pack.GetName() and check != pack.GetName().split("_")[-1]:
            tpe.help = title

        tpe.column = name.str()
        tpe.branchname = pack.GetBranch().GetName()
        return tpe

    else:
        bycounter = {}
        for item, data in pack.items():
            if isinstance(data, dict):
                counter = None
            else:
                counter = data.GetLeafCount()
                if counter:
                    counter = counter.GetName()
                else:
                    counter = None

            if counter not in bycounter:
                bycounter[counter] = []
            bycounter[counter].append((item, data))

        fields = {}
        for counter, pairs in bycounter.items():
            if counter is None:
                for item, data in pairs:
                    fields[item] = toplurtype(data, name.toRecord(item), allowcounters)

            else:
                n = counter
                if n.startswith("n"):
                    n = n[1:]

                if len(pairs) == 1:
                    item, data = pairs[0]
                    fields[n] = List(toplurtype(data, name.toRecord(n).toListData(), False))
                    fields[n].column = name.toRecord(n).toListOffset().str()
                    fields[n].branchname = data.GetLeafCount().GetBranch().GetName()

                else:
                    subfields = {}
                    for item, data in pairs:
                        if len(bycounter) == 1:
                            subname = name.toListData().toRecord(item)
                        else:
                            subname = name.toRecord(n).toListData().toRecord(item)

                        subfields[item] = toplurtype(data, subname, False)
                        counterbranch = data.GetLeafCount().GetBranch()

                    fields[n] = List(Record(**subfields))
                    fields[n].of.column = None
                    fields[n].of.branchname = None
                    fields[n].column = name.toListOffset().str()
                    fields[n].branchname = counterbranch.GetName()

        if len(fields) == 1 and len(name.path) > 0 and name.path[-1][0] == ArrayName.RECORD_FIELD and list(fields.keys())[0] == name.path[-1][1]:
            return list(fields.values())[0]
        else:
            out = Record(**fields)
            out.column = None
            out.branchname = None
            return out

plurtype = List(toplurtype(packages, ArrayName("events").toListData(), True))
plurtype.column = ArrayName("events").toListOffset().str()
plurtype.branchname = None

print(formattype(plurtype))

def type2dtype(tpe):
    if isinstance(tpe, Primitive):
        return tpe.of.newbyteorder(">")
    elif isinstance(tpe, List):
        return numpy.dtype(numpy.int32).newbyteorder(">")
    else:
        assert False, tpe

def branch2array(branch, tpe, count2offset=False):
    dtype = type2dtype(tpe)

    # this is a (slight) overestimate of the size (due to ROOT headers per cluster)
    size = branch.GetTotalSize()

    # allocate some memory
    array = numpy.empty(size, dtype=dtype)

    # fill it
    entries, bytes = branch.FillNumpyArray(array)
    branch.DropBaskets()

    # clip it to the actual length, which we know exactly after filling
    array = array[: (bytes // array.dtype.itemsize)]

    # swap the byte order: physical and interpreted
    array = array.byteswap(True).view(array.dtype.newbyteorder("="))

    # if this is to be an offset array, compute the cumulative sum of counts
    if count2offset:
        array2 = numpy.empty(array.shape[0] + 1, dtype=numpy.int64)
        array2[0] = 0
        numpy.cumsum(array, out=array2[1:])
        array = array2

    return array

class LazyArray(object):
    def __init__(self, branch, tpe, count2offset):
        self.branch = branch
        self.tpe = tpe
        self.count2offset = count2offset
        self.array = None

    def _getarray(self):
        self.array = branch2array(self.branch, self.tpe, self.count2offset)

    def __getitem__(self, i):
        if self.array is None: self._getarray()
        return self.array[i]

    def __len__(self):
        if self.array is None: self._getarray()
        return len(self.array)

    def cumsum(self, out=None):
        if self.array is None: self._getarray()
        return self.array.cumsum(out=out)

    def tofile(self, filename):
        if self.array is None: self._getarray()
        return self.array.tofile(filename)

    @property
    def shape(self):
        if self.array is None: self._getarray()
        return self.array.shape

    @property
    def dtype(self):
        return type2dtype(self.tpe)

def tree2arrays(tree, tpe):
    if tpe.column is not None and tpe.branchname is not None:
        out = {tpe.column: LazyArray(tree.GetBranch(tpe.branchname), tpe, tpe.column.endswith("-Lo"))}
    elif tpe.column is not None and tpe.branchname is None:
        out = {tpe.column: numpy.array([0, tree.GetEntries()], dtype=numpy.int64)}
    else:
        out = {}

    if isinstance(tpe, List):
        out.update(tree2arrays(tree, tpe.of))

    elif isinstance(tpe, Record):
        for n, t in tpe.of:
            out.update(tree2arrays(tree, t).items())

    return out

# print("")
# print("\n".join("{:55s} [{:.2g}, {:.2g}, {:.2g}, ...]".format(n, v[0], v[1], v[2]) if len(v) > 3 else "{:55s} [{}]".format(n, ", ".join(map(lambda x: "{:.2g}".format(x), v))) for n, v in sorted(tree2arrays(tree, plurtype).items())))

# print("")
# print(len(tree.GetListOfLeaves()), len(tree2arrays(tree, plurtype)))

for column, array in tree2arrays(tree, plurtype).items():
    array.tofile("arrays/" + column)

# events = fromarrays("events", tree2arrays(tree, plurtype), tpe=plurtype)

# for event in events:
#     print "event", event.run, event.luminosityBlock, event.event
#     print "MET", event.MET.pt, event.MET.phi

#     for jet in event.Jet:
#         print "jet", jet.pt, jet.eta, jet.phi

#     for electron in event.Electron:
#         print "electron", electron.pt, electron.eta, electron.phi

#     print "LHE", event.LHE.toJsonString()
#     print "LHEPdfWeight", event.LHEPdfWeight.toJsonString()
#     print "LHEScaleWeight", event.LHEScaleWeight.toJsonString()
#     print
