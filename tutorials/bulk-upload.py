#!/usr/bin/env python

import sys

import numpy
import blosc

from plur.dataset.root import ROOTDataset

job = sys.argv[1]          # which job is this, running in parallel?
outof = sys.argv[2]        # how many are running in parallel?
treename = sys.argv[3]     # what is the common TTree name in all the files?
filenames = sys.argv[4:]   # what are the file names (glob-style wildcards allowed)?

# selection function for files to load in this job
filenumbers = lambda n: n % int(outof) == int(job)

# dataset; use startfilenumber and prefix to ensure uniqueness
dataset = ROOTDataset.fromfiles(treename, *filenames, prefix="mydataset", startfilenumber=0)

# save the type JSON somewhere (there's also a .toJson() to get this as lists/dicts)
print dataset.type.toJsonString()

# loop over everything
for filenumber, column, array in dataset.arrayiterator(filenumbers=filenumbers):
    # filenumbers can be split or joined into groupids somehow
    print filenumber,

    # column is a name identifying where the array belongs in the structure
    print column,

    # should save the dtype with the groupids and column name so we can interpret the bytes
    print str(array.dtype),

    # compress the data in the array; this is what we want to download
    # LZ4 level 4 optimizes speed and size
    compressed = blosc.compress(numpy.asarray(array), typesize=array.itemsize, cname="lz4", clevel=4)
    print "({0} bytes)".format(len(compressed))
