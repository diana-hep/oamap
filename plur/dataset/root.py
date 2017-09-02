#!/usr/bin/env python

# Copyright 2017 DIANA-HEP
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import glob
import os
import sys
import time
import re

import ROOT
import numpy

from plur.python.data import fromarrays
from plur.types.arrayname import ArrayName
from plur.types import *
from plur.types import *
from plur.types.primitive import withrepr
from plur.util import *
from plur.util.lazyarray import LazyArray
import plur.compile.code

def normalizename(name):
    return normalizename.pattern.sub(lambda x: "_{0:02x}".format(ord(x.group(0))), name)

normalizename.pattern = re.compile("[^a-zA-Z0-9]")   # no underscores because that's an escape character

def branch2dtype(branch):
    leaves = list(branch.GetListOfLeaves())
    if len(leaves) != 1:
        raise NotImplementedError("TBranch::GetListOfLeaves()->GetEntries() == {0}".format(len(leaves)))
    leaf = leaves[0]

    leaftype = leaf.GetTypeName()
    if leaftype == "Bool_t":
        return boolean.of
    elif leaftype == "Char_t":
        return int8.of
    elif leaftype == "Short_t":
        return int16.of
    elif leaftype == "Int_t":
        return int32.of
    elif leaftype == "Long_t" or leaftype == "Long64_t":
        return int64.of
    elif leaftype == "Float_t" or leaftype == "Double32_t":
        return float32.of
    elif leaftype == "Double_t":
        return float64.of
    elif leaftype == "UChar_t":
        return uint8.of
    elif leaftype == "UShort_t":
        return uint16.of
    elif leaftype == "UInt_t":
        return uint32.of
    elif leaftype == "ULong_t" or leaftype == "ULong64_t":
        return uint64.of
    else:
        raise NotImplementedError("TLeaf::GetTypeName() == \"{0}\"".format(leaftype))

def tree2type(tree, prefix=None, delimiter="-"):
    if prefix is None:
        prefix = normalizename(tree.GetName())

    column2branch = {}
    column2dtype = {}

    def recurse(name, branch):
        if len(branch.GetListOfBranches()) == 0:
            try:
                dtype = branch2dtype(branch)

                out = withrepr(Primitive(dtype), copy=True)
                out.column = name.str()
                out.branchname = branch.GetName()
                out.dtype = out.of

                column2branch[out.column] = out.branchname
                column2dtype[out.column] = out.dtype

                return out

            except NotImplementedError:
                return None

        def getfields(name):
            fields = {}
            for b in branch.GetListOfBranches():
                n = b.GetName()
                if "." in n:
                    n = n[n.rindex(".") + 1:]
                n = normalizename(n)
                if n not in fields:
                    tpe = recurse(name.toRecord(n), b)
                    if tpe is not None:
                        fields[n] = tpe
            return fields

        className = branch.GetClassName()

        if className == "TClonesArray":
            assert len(branch.GetListOfLeaves()) == 1   # is this always true?

            fields = getfields(name.toListData())
            if len(fields) == 0:
                return None

            out = List(Record(**fields))
            out.of.column = None
            out.of.branchname = None
            out.of.dtype = None

            out.column = name.toListBegin().str()
            out.column2 = name.toListEnd().str()
            out.branchname = branch.GetName()
            out.dtype = branch2dtype(branch)

            column2branch[name.toListSize().str()] = out.branchname
            column2dtype[name.toListSize().str()] = out.dtype

            return out

        else:
            fields = getfields(name)
            if len(fields) == 0:
                return None

            out = Record(**fields)
            out.column = None
            out.branchname = None
            out.dtype = None
            return out

    name = ArrayName(prefix, delimiter=delimiter)
    fields = {}
    for b in tree.GetListOfBranches():
        tpe = recurse(name.toListData().toRecord(normalizename(b.GetName())), b)
        if tpe is not None:
            fields[b.GetName()] = tpe

    if len(fields) == 0:
        raise NotImplementedError("none of the branches in this ROOT TTree could be converted into PLUR types")

    tpe = List(Record(**fields))
    tpe.of.column = None
    tpe.of.branchname = None
    tpe.of.dtype = None
    tpe.column = name.toListBegin().str()
    tpe.column2 = name.toListEnd().str()
    tpe.branchname = None
    tpe.dtype = int64.of

    column2branch[name.toListOffset().str()] = tpe.branchname
    column2dtype[name.toListOffset().str()] = tpe.dtype

    return tpe, prefix, column2branch, column2dtype

def branch2array(tree, branchname):
    branch = tree.GetBranch(branchname)

    # infer the Numpy dtype from the TLeaf type, but it starts as big-endian
    dtype = branch2dtype(branch).newbyteorder(">")

    # this is a (slight) overestimate of the size (due to ROOT headers per cluster)
    size = branch.GetTotalSize()

    # allocate some memory
    array = numpy.empty(size, dtype=dtype)

    # fill it
    entries, bytes = branch.FillNumpyArray(array)

    # if you need to cast, you need to copy the array; otherwise, byte-swap in place
    array = array.byteswap(True).view(array.dtype.newbyteorder("="))

    # clip it to the actual length, which we know exactly after filling
    array = array[: (bytes // array.dtype.itemsize)]

    return array

class ROOTDataset(object):
    @staticmethod
    def fromtree(tree, **options):
        return ROOTDatasetFromTree(tree, **options)

    @staticmethod
    def fromchain(chain, **options):
        return ROOTDatasetFromChain(chain, **options)

    @staticmethod
    def fromfiles(treepath, *filepaths, **options):
        return ROOTDatasetFromFiles(treepath, filepaths, **options)

    def __init__(self):
        raise TypeError("use ROOTDataset.fromtree, ROOTDataset.fromchain, or ROOTDataset.fromfiles to create a ROOTDataset")

    def compile(self, fcn, paramtypes={}, environment={}, numba=None, debug=False):
        # compile and also identify the subset of columns that are actually used in the code
        cfcn, columns = plur.compile.code.toplur(fcn, paramtypes, environment, numba, debug, self._column2branch)
        return cfcn, columns

    # for sequential access: this is the primitive form out of which foreach, map, filter, etc. can be built
    def foreachtree(self, fcn, *otherargs, **options):
        debug = options.get("debug", False)
        if debug:
            totalopen = 0.0
            totalio = 0.0
            totalrun = 0.0
            totalentries = 0
            totalbytes = 0
            stopwatch1 = time.time()

        # replace object references with floating indexes
        cfcn, columns = self.compile(fcn, (self.type,), **options)
        arraynames = [ArrayName.parse(c, self.prefix) for c in columns]
        
        if debug:
            print("")
            longestline = 0

        # make the "top array" manually (there is no ROOT equivalent)
        topbeginname = ArrayName(self.prefix).toListBegin()
        topendname = ArrayName(self.prefix).toListEnd()
        topbegin = numpy.array([0], dtype=numpy.int64)
        topend = numpy.array([0], dtype=numpy.int64)

        # create empty arguments for a first evaluation of the function (to force compilation)
        fcnargs = []
        for column, arrayname in zip(columns, arraynames):
            if arrayname == topbeginname:
                array = topbegin
            elif arrayname == topendname:
                array = topend
            elif len(arrayname.path) > 0 and arrayname.path[-1] == (ArrayName.LIST_BEGIN,):
                array = numpy.array([], dtype=numpy.int64)
            elif len(arrayname.path) > 0 and arrayname.path[-1] == (ArrayName.LIST_END,):
                array = numpy.array([], dtype=numpy.int64)
            else:
                array = numpy.array([], dtype=self._column2dtype[column])
            fcnargs.append(array)

        # first evaluation of the function with empty arguments
        fcnargs.extend(otherargs)
        try:
            cfcn(*fcnargs)
        except:
            sys.stderr.write("Failed to test-run function with empty arrays (to force compilation)\n")
            raise

        if debug:
            stopwatch2 = time.time()

        # start loop over TFiles/TTrees in the chain
        self._rewind()
        while self._hasnext():
            if debug:
                stopwatch3 = time.time()

            # step to the next partition and actually open ROOT files *only if* some needed column can't be found in the cache
            partition = self._partition()
            self._next(self.cache is None or any("{0}.{1}".format(column, partition) not in self.cache for column, arrayname in zip(columns, arraynames)))

            if debug:
                stopwatch4 = time.time()

            # make real function arguments this time
            fcnargs = []
            nbytes = 0
            cachetotouch = []
            offsetarrays = {}
            for column, arrayname in zip(columns, arraynames):
                array = None

                # first check the cache for the column
                if self.cache is not None:
                    cachename = "{0}.{1}".format(column, partition)

                    if cachename in self.cache:
                        cachetotouch.append(cachename)
                        array = self.cache[cachename]

                        # special case: the top array
                        if arrayname == topbeginname:
                            topbegin = array
                        elif arrayname == topendname:
                            topend = array

                # if we couldn't get the array from cache, get it from ROOT
                if array is None:
                    # special case: top array
                    if arrayname == topbeginname:
                        array = topbegin
                    elif arrayname == topendname:
                        topend[0] = self.tree.GetEntries()
                        array = topend

                    # if we want -Lb or -Le (begin or end)
                    elif len(arrayname.path) > 0 and (arrayname.path[-1] == (ArrayName.LIST_BEGIN,) or arrayname.path[-1] == (ArrayName.LIST_END,)):
                        # we get it from the corresponding -Lo (offset)
                        offsetname = ArrayName(arrayname.prefix, arrayname.path[:-1] + (ArrayName.LIST_OFFSET,), arrayname.delimiter)

                        # but if we don't have that yet
                        if offsetname not in offsetarrays:
                            # we get it from the corresponding -Ls (size)
                            sizecolumn = ArrayName(arrayname.prefix, arrayname.path[:-1] + (ArrayName.LIST_SIZE,), arrayname.delimiter).str()

                            # which we actually load
                            sizearray = branch2array(self.tree, self._column2branch[sizecolumn])

                            # calculate the offset array from it
                            offsetarrays[offsetname] = numpy.empty(len(sizearray) + 1, dtype=numpy.int64)
                            offsetarrays[offsetname][0] = 0
                            sizearray.cumsum(out=offsetarrays[offsetname][1:])

                        if arrayname.path[-1] == (ArrayName.LIST_BEGIN,):
                            array = offsetarrays[offsetname][:-1]
                        else:
                            array = offsetarrays[offsetname][1:]

                    # the usual case: just load the array
                    else:
                        array = branch2array(self.tree, self._column2branch[column])
                        
                    # put it into the cache for next time
                    if self.cache is not None:
                        self.cache[cachename] = array

                fcnargs.append(array)
                nbytes += array.nbytes

            # other arguments, not input arrays
            fcnargs.extend(otherargs)

            nentries = topend[0]
            totalentries += nentries
            totalbytes += nbytes

            # touch all recently used columns at once
            if self.cache is not None and hasattr(self.cache, "touch"):
                self.cache.touch(*cachetotouch)

            if debug:
                stopwatch5 = time.time()

            # actually run the function
            try:
                cfcn(*fcnargs)
            except:
                sys.stderr.write("Failed while processing \"{0}\"\n".format(self._identity()))
                raise

            # debugging output
            if debug:
                stopwatch6 = time.time()

                line = "{0:3d}% done; reading: {1:.3f} MB/s, computing: {2:.3f} MHz ({3})".format(
                    int(round(self._percent())),
                    nbytes/(stopwatch5 - stopwatch4)/1024**2,
                    nentries/(stopwatch6 - stopwatch5)/1e6,
                    "..." + self._identity()[-26:] if len(self._identity()) > 29 else self._identity())
                print(line)
                longestline = max(longestline, len(line))

                totalopen += stopwatch4 - stopwatch3
                totalio += stopwatch5 - stopwatch4
                totalrun += stopwatch6 - stopwatch5

        # final debugging output
        if debug:
            print("=" * longestline)
            print("""
total time spent compiling: {0:.3f} sec
             opening files: {1:.3f} sec
              reading data: {2:.3f} sec ({3:.3f} MB --> {4:.3f} MB/s)
                 computing: {5:.3f} sec ({6:d} entries --> {7:.3f} MHz)
       reading + computing: {8:.3f} sec ({9:d} entries --> {10:.3f} MHz)

      from start to finish: {11:.3f} sec""".format(
                stopwatch2 - stopwatch1,
                totalopen,
                totalio,
                totalbytes/1024.0**2,
                totalbytes/totalio/1024**2,
                totalrun,
                totalentries,
                totalentries/totalrun/1e6,
                totalrun + totalio,
                totalentries,
                totalentries/(totalrun + totalio)/1e6,
                time.time() - stopwatch1).lstrip())

    class ROOTLazyArray(LazyArray):
        def __init__(self, tree, branchname):
            super(ROOTDataset.ROOTLazyArray, self).__init__()
            self.tree = tree
            self.branchname = branchname

        def _load(self):
            self.array = branch2array(self.tree, self.branchname)

    # interpret negative indexes as starting at the end of the dataset
    def _normalize(self, i, clip, step):
        lenself = len(self)

        if i < 0:
            j = len(self) + i
            if j < 0:
                if clip:
                    return 0 if step > 0 else lenself
                else:
                    raise IndexError("ROOTDataset index out of range: {0} for length {1}".format(i, lenself))
            else:
                return j

        elif i < lenself:
            return i

        elif clip:
            return lenself if step > 0 else 0

        else:
            raise IndexError("ROOTDataset index out of range: {0} for length {1}".format(i, lenself))

    def __getitem__(self, entry):
        # handle slices
        if isinstance(entry, slice):
            lenself = len(self)

            if entry.step is None:
                step = 1
            else:
                step = entry.step
            if step == 0:
                raise ValueError("slice step cannot be zero")

            if entry.start is None:
                if step > 0:
                    start = 0
                else:
                    start = lenself - 1
            else:
                start = self._normalize(entry.start, True, step)

            if entry.stop is None:
                if step > 0:
                    stop = lenself
                else:
                    stop = -1
            else:
                stop = self._normalize(entry.stop, True, step)

            # by repeatedly calling this function with individual indexes
            return [self[i] for i in range(start, stop, step)]

        else:
            entry = self._normalize(entry, False, 1)

            # find out which tree we need to load
            tree, start = self._findentry(entry)

            # cache the infrastructure for this tree so that contiguous access is not too slow
            if getattr(self, "_start", None) != start:
                lazyarrays = {}
                for column, branchname in self._column2branch.items():
                    arrayname = ArrayName.parse(column, self.prefix)

                    if arrayname == ArrayName(self.prefix).toListOffset():
                        # special case: the top array
                        array = numpy.array([0, tree.GetEntries()], dtype=numpy.int64)
                    else:
                        # create a ROOTLazyArray for this ROOT branch; maybe it will be read from ROOT, maybe not
                        array = self.ROOTLazyArray(tree, branchname)

                    lazyarrays[column] = array

                # set the cache with a newly minted PLUR object (for this whole tree)
                self._start = start
                self._plur = fromarrays(self.prefix, lazyarrays, tpe=self.type)

            # return the PLUR object at the right index
            return self._plur[entry - start]

##################################################################### ROOTDataset given a single TTree

class ROOTDatasetFromTree(ROOTDataset):
    def __init__(self, tree, prefix=None, cache=None, startpartition=0):
        self.tree = tree
        if not self.tree:
            raise IOError("tree not valid")

        self._rewind()
        self._next(True)

        self.type, self.prefix, self._column2branch, self._column2dtype = tree2type(self.tree, prefix)
        self._startpartition = startpartition

        if hasattr(cache, "newuser"):
            self.cache = cache.newuser({"{0}.{1}".format(self.prefix, self._startpartition): {"file": tree.GetCurrentFile().GetName(), "tree": tree.GetName()}})
        else:
            self.cache = cache

    @property
    def startpartition(self):
        return self._startpartition

    @property
    def stoppartition(self):
        return self._startpartition + 1

    def _rewind(self):
        self._dummyindex = 0

    def _hasnext(self):
        return self._dummyindex < 1

    def _next(self, loadroot):
        if not self._hasnext(): raise StopIteration
        self._dummyindex += 1

    def _percent(self):
        return 0.0 if self._dummyindex == 0 else 100.0

    def _identity(self):
        return self.tree.GetName()

    def _partition(self):
        return self._startpartition + self._dummyindex

    def _findentry(self, entry):
        return self.tree, 0

    def __len__(self):
        return self.tree.GetEntries()

    def arrays(self, columns=lambda n: True, arraynames=lambda n: True, branchnames=lambda n: True, lazy=False):
        out = {}
        for column, branchname in self._column2branch.items():
            arrayname = ArrayName.parse(column, self.prefix)
            if columns(column) and arraynames(arrayname) and branchnames(branchname):
                if arrayname == ArrayName(self.prefix).toListOffset():
                    # special case: the top array
                    array = numpy.array([0, self.tree.GetEntries()], dtype=numpy.int64)
                elif lazy:
                    array = self.ROOTLazyArray(self.tree, branchname)
                else:
                    array = self.branch2array(self.tree, branchname)
                out[column] = array

        return out

##################################################################### ROOTDataset given a PyROOT TChain object

class ROOTDatasetFromChain(ROOTDataset):
    def __init__(self, chain, prefix=None, cache=None, startpartition=0):
        self.chain = chain

        self._rewind()
        if not self._hasnext():
            raise IOError("empty TChain")
        self._next(True)

        self.type, self.prefix, self._column2branch, self._column2dtype = tree2type(self.tree, prefix)
        self._startpartition = startpartition

        if hasattr(cache, "newuser"):
            self.cache = cache.newuser(dict(("{0}.{1}".format(self.prefix, self._startpartition + i), {"file": x.GetTitle(), "tree": x.GetName()}) for i, x in enumerate(self.chain.GetListOfFiles())))
        else:
            self.cache = cache

    @property
    def startpartition(self):
        return self._startpartition

    @property
    def stoppartition(self):
        return self._startpartition + self.cache.GetNtrees()

    def _rewind(self):
        self._filename = ""
        self._entryindex = 0
        self._treeindex = 0

    def _hasnext(self):
        return self._treeindex < self.chain.GetNtrees()

    def _next(self, loadroot):
        if not self._hasnext(): raise StopIteration

        if loadroot:
            self.chain.LoadTree(self._entryindex)
            self.tree = self.chain.GetTree()
            if not self.tree:
                raise IOError("tree number {0} not valid in TChain".format(self._treeindex))
            self._filename = self.chain.GetFile().GetName()
            self._entryindex += self.tree.GetEntries()
        else:
            chainelement = self.chain.GetListOfFiles()[self._treeindex]
            self._filename = chainelement.GetTitle()
            self._entryindex += chainelement.GetEntries()

        self._treeindex += 1

    def _percent(self):
        return 100.0 * self._treeindex / self.chain.GetNtrees()

    def _identity(self):
        return self._filename

    def _partition(self):
        return self._startpartition + self._treeindex

    def _findentry(self, entry):
        subentry = self.chain.LoadTree(entry)
        tree = self.chain.GetTree()
        if not tree:
            raise IOError("tree for entry {0} not valid in TChain".format(entry))
        return tree, entry - subentry

    def __len__(self):
        return self.chain.GetEntries()

##################################################################### ROOTDataset given a tree name and files

class ROOTDatasetFromFiles(ROOTDataset):
    def __init__(self, treepath, filepaths, prefix=None, cache=None, startpartition=0):
        self.treepath = treepath
        self.filepaths = [y for x in filepaths for y in sorted(glob.glob(os.path.expanduser(x)))]

        self._rewind()
        if not self._hasnext():
            raise IOError("empty file list")
        self._next(True)

        self.type, self.prefix, self._column2branch, self._column2dtype = tree2type(self.tree, prefix)
        self._startpartition = startpartition

        if hasattr(cache, "newuser"):
            self.cache = cache.newuser(dict(("{0}.{1}".format(self.prefix, self._startpartition + i), {"file": x, "tree": self.treepath}) for i, x in enumerate(self.filepaths)))
        else:
            self.cache = cache

    @property
    def startpartition(self):
        return self._startpartition

    @property
    def stoppartition(self):
        return self._startpartition + len(self.filepaths)

    def _gettree(self, filepath):
        file = ROOT.TFile(filepath)
        if not file or file.IsZombie():
            raise IOError("could not read file \"{0}\"".format(filepath))

        tree = file.Get(self.treepath)
        if not tree:
            raise IOError("tree \"{0}\" not found in file \"{1}\"".format(self.treepath, filepath))
        return file, tree

    def _rewind(self):
        self._fileindex = 0
        self._filename = ""

    def _hasnext(self):
        return self._fileindex < len(self.filepaths)

    def _next(self, loadroot):
        if not self._hasnext(): raise StopIteration

        if loadroot:
            self.file, self.tree = self._gettree(self.filepaths[self._fileindex])

        self._filename = self.filepaths[self._fileindex]
        self._fileindex += 1

    def _percent(self):
        return 100.0 * self._fileindex / len(self.filepaths)

    def _identity(self):
        return self._filename

    def _partition(self):
        return self._startpartition + self._fileindex

    def _findentry(self, entry):
        if not hasattr(self, "_numentries"):
            len(self)

        firstentry = 0
        lastentry = 0
        for i, numentries in enumerate(self._numentries):
            lastentry += numentries

            if entry < lastentry:
                if self._fileindex != i + 1:
                    self.file, self.tree = self._gettree(self.filepaths[i])
                    self._filename = self.filepaths[i]
                    self._fileindex = i + 1
                    
                return self.tree, firstentry

            firstentry += numentries

        raise IndexError("ROOTDataset index {0} out of range ({1})".format(entry, lastentry))

    def __len__(self):
        if not hasattr(self, "_numentries"):
            self._numentries = []
            for filepath in self.filepaths:
                file, tree = self._gettree(filepath)
                self._numentries.append(tree.GetEntries())

        return sum(self._numentries)

