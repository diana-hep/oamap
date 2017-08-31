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
    path = leaf.GetName().split("_")

    pack = packages
    for item in path[:-1]:
        if item not in pack:
            pack[item] = {}
        pack = pack[item]

    pack[path[-1]] = leaf

def toplurtype(pack, allowcounters=True):
    if not isinstance(pack, dict):
        typename = pack.GetTypeName()
        if typename == "Char_t":
            tpe = int8
        elif typename == "UChar_t":
            tpe = uint8
        elif typename == "Int_t":
            tpe = int32
        elif typename == "UInt_t":
            tpe = uint32
        elif typename == "Long64_t":
            tpe = int64
        elif typename == "ULong64_t":
            tpe = uint64
        elif typename == "Float_t":
            tpe = float32
        elif typename == "Double_t":
            tpe = float64
        else:
            raise NotImplementedError, typename

        title = pack.GetBranch().GetTitle()
        check = re.sub("/[CBbSsIiFDLlo]$", "", title)
        if check != pack.GetName() and check != pack.GetName().split("_")[-1]:
            tpe.help = title
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
                    fields[item] = toplurtype(data, allowcounters=allowcounters)

            else:
                name = counter
                if name.startswith("n"):
                    name = name[1:]

                subfields = {}
                for item, data in pairs:
                    subfields[item] = toplurtype(data, allowcounters=False)
                
                fields[name] = List(Record(**subfields))

        if len(fields) == 1:
            return list(fields.values())[0]
        else:
            return Record(**fields)

print formattype(toplurtype(packages))
