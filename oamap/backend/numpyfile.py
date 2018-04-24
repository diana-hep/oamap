#!/usr/bin/env python

# Copyright (c) 2017, DIANA-HEP
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# 
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# 
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os

import numpy

import oamap.dataset
import oamap.database

class NumpyFileBackend(oamap.database.WritableBackend):
    def __init__(self, directory):
        if not os.path.exists(directory):
            os.mkdir(directory)
        self._directory = directory
        super(NumpyFileBackend, self).__init__(directory)

    @property
    def directory(self):
        return self._directory

    def instantiate(self, partitionid):
        return NumpyArrays(self._directory, partitionid)

    def prefix(self, dataset):
        return os.path.join(dataset, "PART", "obj")

    def incref(self, dataset, partitionid, arrayname):
        print "incref", dataset, partitionid, arrayname

        otherdataset_part, array = os.path.split(arrayname)
        otherdataset, part = os.path.split(otherdataset_part)
        if otherdataset != dataset:
            src = os.path.join(self._directory, otherdataset, str(partitionid), array) + ".npy"
            dst = os.path.join(self._directory, dataset, str(partitionid), array) + ".npy"
            os.link(src, dst)

    def decref(self, dataset, partitionid, arrayname):
        print "decref", dataset, partitionid, arrayname

        otherdataset_part, array = os.path.split(arrayname)
        path = os.path.join(self._directory, dataset, str(partitionid), array) + ".npy"
        os.unlink(path)

class NumpyArrays(object):
    def __init__(self, directory, partitionid):
        self._directory = directory
        self._partitionid = partitionid

    @property
    def directory(self):
        return self._directory

    @property
    def partitionid(self):
        return self._partitionid

    def fullname(self, name, create=False):
        dataset_part, array = os.path.split(name)
        dataset, part = os.path.split(dataset_part)
        if create:
            if not os.path.exists(os.path.join(self._directory, dataset)):
                os.mkdir(os.path.join(self._directory, dataset))
            if not os.path.exists(os.path.join(self._directory, dataset, str(self._partitionid))):
                os.mkdir(os.path.join(self._directory, dataset, str(self._partitionid)))

        return os.path.join(self._directory, dataset, str(self._partitionid), array) + ".npy"

    def __getitem__(self, name):
        return numpy.load(self.fullname(name))

    def __setitem__(self, name, value):
        numpy.save(self.fullname(name, create=True), value)

    def __delitem__(self, name):
        try:
            os.remove(self.fullname(name))
        except Exception as err:
            raise KeyError(str(err))
