#!/usr/bin/env python

import re

import numpy
import ROOT

from plur.types import *
from plur.types.primitive import withrepr
from plur.types.arrayname import ArrayName
from plur.python import fromarrays

file = ROOT.TFile("/home/pivarski/data/nano-2017-08-31.root")
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

packages = {}
for leaf in leaves:
    if len(leaf.GetBranch().GetListOfLeaves()) != 1:
        raise TypeError("TLeaf \"{0}\" is not the only leaf in TBranch \"{1}\"".format(leaf.GetName(), leaf.GetBranch().GetName()))

    path = leaf.GetName().split("_")

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

        if len(fields) == 1:
            return list(fields.values())[0]
        else:
            out = Record(**fields)
            out.column = None
            out.branchname = None
            return out

tpe = List(toplurtype(packages, ArrayName("events").toListData(), True))
tpe.column = ArrayName("events").toListOffset().str()
tpe.branchname = None

print formattype(tpe)
