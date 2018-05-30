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

import numpy

import oamap.database

class NumpyFileBackend(oamap.database.FilesystemBackend):
    def __init__(self, directory):
        super(NumpyFileBackend, self).__init__(directory, arraysuffix=".npy")

    @property
    def args(self):
        return (self._directory,)

    def tojson(self):
        return {"class": self.__class__.__module__ + "." + self.__class__.__name__,
                "directory": self._directory}

    @staticmethod
    def fromjson(obj, namespace):
        return NumpyFileBackend(obj["directory"])

    def instantiate(self, partitionid):
        return NumpyArrays(lambda name: self.fullname(partitionid, name, create=False),
                           lambda name: self.fullname(partitionid, name, create=True))

class NumpyArrays(object):
    def __init__(self, loadname, storename):
        self._loadname = loadname
        self._storename = storename

    def __getitem__(self, name):
        return numpy.load(self._loadname(name))

    def __setitem__(self, name, value):
        numpy.save(self._storename(name), value)

class NumpyFileDatabase(oamap.database.FilesystemDatabase):
    def __init__(self, directory, namespace=""):
        super(NumpyFileDatabase, self).__init__(directory, backends={namespace: NumpyFileBackend(directory)}, namespace=namespace)
