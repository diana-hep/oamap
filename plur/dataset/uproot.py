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

import os.path
import glob
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

uproot = __import__("uproot")

class UprootFileRange(object):
    def __init__(self, path, entrystart, entryend):
        self.path = path
        self.entrystart = entrystart
        self.entryend = entryend

    @property
    def numentries(self):
        return self.entryend - self.entrystart

    def __repr__(self):
        return "<UprootFileRange {0} {1}:{2}>".format(repr(self.path), self.entrystart, self.entryend)

class UprootPartition(object):
    def __init__(self, number, fileranges):
        self.number = number
        self.fileranges = fileranges

    @property
    def numentries(self):
        return sum(x.numentries for x in self.fileranges)

    def __repr__(self):
        return "<UprootPartition {0}>".format(self.number)

class UprootDataset(object):
    def __init__(self, treepath, *filepaths, **options):
        def getoption(name, default):
            out = options.get(name, default)
            try:
                del options[name]
            except KeyError:
                pass
            return out

        self.branchdtypes = getoption("branchdtypes", lambda branch: getattr(branch, "dtype", None))
        self.prefix = getoption("prefix", None)
        self.cache = getoption("cache", None)
        self.memmap = getoption("memmap", True)
        self.startpartition = getoption("startpartition", 0)
        self.maxpartitionbytes = getoption("maxpartitionbytes", 10*1024**2)   # 10 MB
        if len(options) != 0:
            raise TypeError("unrecognized options: {0}".format(" ".join(options)))

        self.treepath = treepath

        localfilepaths = []
        remotefilepaths = []
        for path in filepaths:
            parsed = urlparse(path)
            if parsed.scheme == "file" or parsed.scheme == "":
                path = parsed.netloc + parsed.path
                for file in glob.glob(path):
                    localfilepaths.append(file)
            else:
                remotefilepaths.append(path)
        localfilepaths.sort()
        remotefilepaths.sort()

        filepaths = localfilepaths + remotefilepaths
        if len(filepaths) == 0:
            raise IOError("no filepaths have been provided")

        firsttree = uproot.open(filepaths[0], memmap=self.memmap)[self.treepath]
        # self.type, self.prefix, self._column2branch, self._column2dtype = self.tree2type(firsttree, prefix, self.branchdtypes)

        self.partitions = []
        # branchnames = sorted(self._column2branch.values())
        branchnames = firsttree.branchnames
        assert len(branchnames) > 0
        filenumber = 0
        entrynumber = 0
        trees = {}
        while filenumber < len(filepaths):
            minentriesPartition = None

            for branchname in branchnames:
                print "check branch", branchname

                bfilenumber = filenumber
                bentrynumber = entrynumber

                if bfilenumber not in trees:
                    trees[bfilenumber] = uproot.open(filepaths[bfilenumber])[self.treepath]

                # find out which basket and entry we're starting at
                basketentrystart = 0
                for basketnumber in range(trees[bfilenumber][branchname].numbaskets):
                    if basketnumber + 1 == trees[bfilenumber][branchname].numbaskets or basketentrystart + trees[bfilenumber][branchname].basketentries(basketnumber + 1) > bentrynumber:
                        break
                    else:
                        basketentrystart += trees[bfilenumber][branchname].basketentries(basketnumber)

                print "start filenumber", bfilenumber, "basket", basketnumber, "entry", bentrynumber

                # now just add up bytes until we're about to exceed the maximum
                bytes = 0
                while True:
                    if bentrynumber >= trees[bfilenumber].numentries:
                        bfilenumber += 1
                        bentrynumber = 0
                        basketnumber = 0
                        if bfilenumber >= len(filepaths):
                            break
                        if bfilenumber not in trees:
                            trees[bfilenumber] = uproot.open(filepaths[bfilenumber])[self.treepath]

                    if bytes + trees[bfilenumber][branchname].basketbytes(basketnumber) > self.maxpartitionbytes:
                        break
                    else:
                        bytes += trees[bfilenumber][branchname].basketbytes(basketnumber)
                        bentrynumber += trees[bfilenumber][branchname].basketentries(basketnumber)
                        basketnumber += 1

                print "end filenumber", bfilenumber, "basket", basketnumber, "entry", bentrynumber, "has", bytes, "bytes"

                # create a possible partition based on this file range
                fileranges = []
                for fn in range(filenumber, bfilenumber + (1 if bentrynumber > 0 else 0)):
                    if fn == filenumber and fn == bfilenumber:
                        fileranges.append(UprootFileRange(filepaths[fn], entrynumber, bentrynumber))
                    elif fn == filenumber:
                        fileranges.append(UprootFileRange(filepaths[fn], entrynumber, trees[fn].numentries))
                    elif fn == bfilenumber:
                        fileranges.append(UprootFileRange(filepaths[fn], 0, bentrynumber))
                    else:
                        fileranges.append(UprootFileRange(filepaths[fn], 0, trees[fn].numentries))

                if len(fileranges) == 0 or fileranges[0].entrystart == fileranges[0].entryend:
                    raise ValueError("branch {0} starting at entry {1} in file {2} cannot satisfy numbytes < {3} for any number of entries".format(repr(branchname), entrynumber, filepaths[filenumber], self.maxpartitionbytes))

                print "fileranges", fileranges

                # if this partition has the smallest number of entries we've seen, take it
                partition = UprootPartition(len(self.partitions), fileranges)
                if minentriesPartition is None or partition.numentries < minentriesPartition.numentries:
                    minentriesPartition = partition
                    newfilenumber = bfilenumber
                    newentrynumber = bentrynumber

            filenumber = newfilenumber
            entrynumber = newentrynumber
            self.partitions.append(minentriesPartition)

            print "add partition", self.partitions[-1], "fileranges", self.partitions[-1].fileranges

        # if hasattr(cache, "newuser"):
        #     self.cache = cache.newuser(dict(("{0}.{1}".format(self.prefix, self.startpartition + i), {"file": x, "tree": self.treepath}) for i, x in enumerate(filepaths)))
        # else:
        #     self.cache = cache
        
    # @property
    # def stoppartition(self):
    #     return self.startpartition + len(self.filepaths)

    # def arrayiterator(self, partitions, executor=None):
    #     pass

