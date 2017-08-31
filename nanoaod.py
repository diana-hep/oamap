#!/usr/bin/env python

import numpy
import ROOT

from plur.types import *
from plur.types.primitive import withrepr
from plur.types.arrayname import ArrayName
from plur.python import fromarrays

file = ROOT.TFile("/home/pivarski/data/nano-2017-08-31.root")
tree = file.Get("Events")

class ValueDescr(object):
    def __init__(self, fieldname, plurtype, rootbranch):
        self.fieldname = fieldname
        self.plurtype = plurtype
        self.rootbranch = rootbranch

    def __repr__(self):
        return "ValueDescr({0}, {1})".format(self.plurtype, self.rootbranch)

    def toplur(self, name):
        out = withrepr(self.plurtype, copy=True)
        out.column = name.toRecord(self.fieldname).str()
        out.branchname = self.rootbranch.GetName()
        return out

class ListDescr(object):
    def __init__(self, fieldname, counterbranch):
        self.fieldname = fieldname
        self.counterbranch = counterbranch
        self.fields = {}

    def __getitem__(self, name):
        return self.fields[name]

    def __setitem__(self, name, value):
        self.fields[name] = value

    def __repr__(self):
        return "ListDescr({0}, {1}, {2})".format(self.fieldname, self.counterbranch, self.fields)

    def toplur(self, name):
        out = List(Record(**dict((n, v.toplur(name.toRecord(self.fieldname).toListData())) for n, v in self.fields.items())))
        out.of.column = None
        out.of.branchname = None
        out.column = name.toRecord(self.fieldname).toListOffset().str()
        out.branchname = self.counterbranch.GetName()
        return out

values = {}
lists = {}
for branch in tree.GetListOfBranches():
    leaves = branch.GetListOfLeaves()
    if leaves.GetEntries() == 1:
        fieldname = branch.GetName()

        if leaves[0].GetLeafCount():
            counterbranch = leaves[0].GetLeafCount().GetBranch()
            countername = counterbranch.GetName()
            if countername.startswith("n"):
                countername = countername[1:]
                if len(countername) > 0:
                    countername = countername[0].lower() + countername[1:]

            if countername not in lists:
                lists[countername] = ListDescr(countername, counterbranch)

            tofill = lists[countername]
            if "_" in fieldname:
                fieldname = fieldname[fieldname.index("_") + 1:]
            
        else:
            tofill = values

        typename = leaves[0].GetTypeName()
        if typename == "Char_t":
            plurtype = int8
        elif typename == "UChar_t":
            plurtype = uint8
        elif typename == "Int_t":
            plurtype = int32
        elif typename == "UInt_t":
            plurtype = uint32
        elif typename == "Long64_t":
            plurtype = int64
        elif typename == "ULong64_t":
            plurtype = uint64
        elif typename == "Float_t":
            plurtype = float32
        elif typename == "Double_t":
            plurtype = float64
        else:
            raise NotImplementedError, typename

        tofill[fieldname] = ValueDescr(fieldname, plurtype, branch)

for listdescr in lists.values():
    countername = listdescr.counterbranch.GetName()
    if countername in values:
        del values[countername]

plurtype = List(Record(**dict(
    [(n, v.toplur(ArrayName("events").toListData())) for n, v in values.items()] +
    [(n, v.toplur(ArrayName("events").toListData())) for n, v in lists.items()])))
plurtype.of.column = None
plurtype.of.branchname = None
plurtype.column = ArrayName("events").toListOffset().str()
plurtype.branchname = None

print formattype(plurtype)

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
    if count2offset:
        size = branch.GetTotalSize() + 1
    else:
        size = branch.GetTotalSize()

    # allocate some memory
    array = numpy.empty(size, dtype=dtype)

    # fill it
    if count2offset:
        entries, bytes = branch.FillNumpyArray(array[1:])
    else:
        entries, bytes = branch.FillNumpyArray(array)

    # clip it to the actual length, which we know exactly after filling
    if count2offset:
        array = array[: (bytes // array.dtype.itemsize) + 1]
    else:
        array = array[: (bytes // array.dtype.itemsize)]

    # swap the byte order: physical and interpreted
    array = array.byteswap(True).view(array.dtype.newbyteorder("="))

    # if this is to be an offset array, compute the cumulative sum of counts
    if count2offset:
        array[0] = 0
        numpy.cumsum(array[1:], out=array[1:])

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

print
print "\n".join("{:50s} [{:.2g}, {:.2g}, {:.2g}, ...]".format(n, v[0], v[1], v[2]) if len(v) > 3 else "{:50s} [{}]".format(n, ", ".join(map(lambda x: "{:.2g}".format(x), v))) for n, v in sorted(tree2arrays(tree, plurtype).items()))

print
print len(tree.GetListOfLeaves()), len(tree2arrays(tree, plurtype))

# events = fromarrays("events", tree2arrays(tree, plurtype), tpe=plurtype)

# for event in events:
#     print "event", event.run, event.luminosityBlock, event.event
#     for jet in event.jet:
#         print "jet", jet.pt, jet.eta, jet.phi
