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

import oamap.schema
import oamap.dataset
import oamap.database
import oamap.proxy
import oamap.backend.packing
from oamap.util import OrderedDict

def dataset(path, treepath, namespace=None, **kwargs):
    import uproot

    if namespace is None:
        namespace = "root({0}, {1})".format(repr(path), repr(treepath))

    if "localsource" not in kwargs:
        kwargs["localsource"] = lambda path: uproot.source.file.FileSource(path, chunkbytes=8*1024, limitbytes=None)
    kwargs["total"] = False
    kwargs["blocking"] = True

    paths2entries = uproot.tree.numentries(path, treepath, **kwargs)
    if len(paths2entries) == 0:
        raise ValueError("path {0} matched no TTrees".format(repr(path)))

    offsets = [0]
    paths = []
    for path, numentries in paths2entries.items():
        offsets.append(offsets[-1] + numentries)
        paths.append(path)

    sch = schema(paths[0], treepath, namespace=namespace)
    doc = sch.doc
    sch.doc = None

    return oamap.dataset.Dataset(treepath.split("/")[-1].split(";")[0],
                                 sch,
                                 {namespace: ROOTBackend(paths, treepath, namespace)},
                                 oamap.dataset.SingleThreadExecutor(),
                                 offsets,
                                 extension=None,
                                 packing=None,
                                 doc=doc,
                                 metadata={"schemafrom": paths[0]})

def proxy(path, treepath, namespace="", extension=oamap.extension.common):
    import uproot
    def localsource(path):
        return uproot.source.file.FileSource(path, chunkbytes=8*1024, limitbytes=None)
    return _proxy(uproot.open(path, localsource=localsource)[treepath], namespace=namespace, extension=extension)

def _proxy(tree, namespace="", extension=oamap.extension.common):
    schema = _schema(tree, namespace=namespace)
    generator = schema.generator(extension=extension)
    return oamap.proxy.ListProxy(generator, ROOTArrays(tree, ROOTBackend([tree._context.sourcepath], tree._context.treename, namespace)), generator._newcache(), 0, 1, tree.numentries)

def schema(path, treepath, namespace=""):
    import uproot
    def localsource(path):
        return uproot.source.file.FileSource(path, chunkbytes=8*1024, limitbytes=None)
    return _schema(uproot.open(path, localsource=localsource)[treepath], namespace=namespace)

def _schema(tree, namespace=None):
    import uproot

    if namespace is None:
        namespace = "root({0}, {1})".format(repr(path), repr(treepath))

    def accumulate(node):
        out = oamap.schema.Record(OrderedDict(), namespace=namespace)
        for branchname, branch in node.iteritems(aliases=False) if isinstance(node, uproot.tree.TTreeMethods) else node.iteritems():
            if not isinstance(branchname, str):
                branchname = branchname.decode("ascii")
            fieldname = branchname.split(".")[-1]

            if len(branch.fBranches) > 0:
                subrecord = accumulate(branch)
                if len(subrecord.fields) > 0:
                    out[fieldname] = subrecord

            elif isinstance(branch.interpretation, (uproot.interp.asdtype, uproot.interp.numerical.asdouble32)):
                subnode = oamap.schema.Primitive(branch.interpretation.todtype, data=branchname, namespace=namespace)
                for i in range(len(branch.interpretation.todims)):
                    subnode = oamap.schema.List(subnode, starts="{0}:/{1}".format(branchname, i), stops="{0}:/{1}".format(branchname, i), namespace=namespace)
                out[fieldname] = subnode

            elif isinstance(branch.interpretation, uproot.interp.asjagged) and isinstance(branch.interpretation.asdtype, uproot.interp.asdtype):
                subnode = oamap.schema.Primitive(branch.interpretation.asdtype.todtype, data=branchname, namespace=namespace)
                for i in range(len(branch.interpretation.asdtype.todims)):
                    subnode = oamap.schema.List(subnode, starts="{0}:/{1}".format(branchname, i), stops="{0}:/{1}".format(branchname, i), namespace=namespace)
                out[fieldname] = oamap.schema.List(subnode, starts=branchname, stops=branchname, namespace=namespace)

            elif isinstance(branch.interpretation, uproot.interp.asstrings):
                out[fieldname] = oamap.schema.List(oamap.schema.Primitive(oamap.interp.strings.CHARTYPE, data=branchname, namespace=namespace), starts=branchname, stops=branchname, namespace=namespace, name="ByteString")
        
        return out

    def combinelists(schema):
        if isinstance(schema, oamap.schema.Record) and all(isinstance(x, oamap.schema.List) for x in schema.fields.values()):
            out = oamap.schema.List(oamap.schema.Record(OrderedDict(), namespace=namespace), namespace=namespace)

            countbranch = None
            for fieldname, field in schema.items():
                try:
                    branch = tree[field.starts]
                except KeyError:
                    return schema

                if branch.countbranch is None:
                    return schema

                if countbranch is None:
                    countbranch = branch.countbranch
                elif countbranch is not branch.countbranch:
                    return schema

                out.content[fieldname] = field.content

            if countbranch is not None:
                countbranchname = countbranch.name
                if not isinstance(countbranchname, str):
                    countbranchname = countbranchname.decode("ascii")
                out.starts = countbranchname
                out.stops = countbranchname
                return out

        return schema

    entries = accumulate(tree).replace(combinelists)
    entries.name = "Entry"

    doc = tree.title
    if not isinstance(doc, str):
        doc = doc.decode("ascii")
        
    return oamap.schema.List(entries, namespace=namespace, doc=doc)

class ROOTBackend(oamap.database.Backend):
    def __init__(self, paths, treepath, namespace):
        self._paths = tuple(paths)
        self._treepath = treepath
        self._namespace = namespace

    @property
    def args(self):
        return (self._paths, self._treepath)

    def tojson(self):
        return {"class": self.__class__.__module__ + "." + self.__class__.__name__,
                "paths": list(self._paths),
                "treepath": self._treepath}

    @staticmethod
    def fromjson(obj, namespace):
        return ROOTBackend(obj["paths"], obj["treepath"], namespace)

    @property
    def namespace(self):
        return self._namespace

    def instantiate(self, partitionid):
        return ROOTArrays.frompath(self._paths[partitionid], self._treepath, self)
        
class ROOTArrays(object):
    @staticmethod
    def frompath(path, treepath, backend):
        import uproot
        file = uproot.open(path)
        out = ROOTArrays(file[treepath], backend)
        out._source = file._context.source
        return out

    def __init__(self, tree, backend):
        self._tree = tree
        self._backend = backend
        self._keycache = {}

    @property
    def tree(self):
        return self._tree

    @property
    def backend(self):
        return self._backend

    def getall(self, roles):
        import uproot

        def chop(role):
            name = str(role).encode("ascii")
            try:
                colon = name.rindex(b":")
            except ValueError:
                return name, None
            else:
                return name[:colon], name[colon + 1:]
            
        arrays = self._tree.arrays(set(chop(x)[0] for x in roles), keycache=self._keycache)

        out = {}
        for role in roles:
            branchname, leafname = chop(role)
            array = arrays[branchname]

            if leafname is not None and leafname.startswith(b"/"):
                if isinstance(array, (uproot.interp.jagged.JaggedArray, uproot.interp.strings.Strings)):
                    array = array.content

                length = array.shape[0]
                stride = 1
                for depth in range(int(leafname[1:])):
                    length *= array.shape[depth + 1]
                    stride *= array.shape[depth + 1]

                if isinstance(role, oamap.generator.StartsRole) and role not in out:
                    offsets = numpy.arange(0, (length + 1)*stride, stride)
                    out[role] = offsets[:-1]
                    out[role.stops] = offsets[1:]

                elif isinstance(role, oamap.generator.StopsRole) and role not in out:
                    offsets = numpy.arange(0, (length + 1)*stride, stride)
                    out[role.starts] = offsets[:-1]
                    out[role] = offsets[1:]

            elif isinstance(array, numpy.ndarray):
                if isinstance(role, oamap.generator.StartsRole) and role not in out:
                    starts, stops = oamap.backend.packing.ListCounts.fromcounts(array)
                    out[role] = starts
                    out[role.stops] = stops

                elif isinstance(role, oamap.generator.StopsRole) and role not in out:
                    starts, stops = oamap.backend.packing.ListCounts.fromcounts(array)
                    out[role.starts] = starts
                    out[role] = stops

                elif isinstance(role, oamap.generator.DataRole):
                    if leafname is None:
                        out[role] = array.reshape(-1)
                    else:
                        out[role] = array[leafname].reshape(-1)

            elif isinstance(array, (uproot.interp.jagged.JaggedArray, uproot.interp.strings.Strings)):
                if isinstance(role, oamap.generator.StartsRole):
                    out[role] = array.starts

                elif isinstance(role, oamap.generator.StopsRole):
                    out[role] = array.stops

                elif isinstance(role, oamap.generator.DataRole):
                    if leafname is None:
                        out[role] = array.content.reshape(-1)
                    else:
                        out[role] = array.content[leafname].reshape(-1)

            if role not in out:
                raise AssertionError(role)

        return out

    def close(self):
        if hasattr(self, "_source"):
            self._source.close()
        self._tree = None
