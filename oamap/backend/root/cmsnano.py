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

import oamap.backend.root
import oamap.schema
import oamap.dataset
import oamap.proxy
from oamap.util import OrderedDict

def dataset(path, namespace=None, **kwargs):
    import uproot

    if namespace is None:
        namespace = "root.cmsnano({0})".format(repr(path))

    if "localsource" not in kwargs:
        kwargs["localsource"] = lambda path: uproot.source.file.FileSource(path, chunkbytes=8*1024, limitbytes=None)
    kwargs["total"] = False
    kwargs["blocking"] = True

    paths2entries = uproot.tree.numentries(path, "Events", **kwargs)
    if len(paths2entries) == 0:
        raise ValueError("path {0} matched no TTrees".format(repr(path)))

    offsets = [0]
    paths = []
    for path, numentries in paths2entries.items():
        offsets.append(offsets[-1] + numentries)
        paths.append(path)

    sch = schema(paths[0], namespace=namespace)
    doc = sch.doc
    sch.doc = None

    return oamap.dataset.Dataset("Events",
                                 sch,
                                 {namespace: oamap.backend.root.ROOTBackend(paths, "Events", namespace)},
                                 oamap.dataset.SingleThreadExecutor(),
                                 offsets,
                                 extension=None,
                                 packing=None,
                                 doc=doc,
                                 metadata={"schemafrom": paths[0]})

def proxy(path, namespace=None, extension=oamap.extension.common):
    import uproot

    if namespace is None:
        namespace = "root.cmsnano({0})".format(repr(path))

    def localsource(path):
        return uproot.source.file.FileSource(path, chunkbytes=8*1024, limitbytes=None)

    return _proxy(uproot.open(path, localsource=localsource)["Events"], namespace=namespace, extension=extension)

def _proxy(tree, namespace=None, extension=oamap.extension.common):
    if namespace is None:
        namespace = "root.cmsnano({0})".format(repr(path))

    schema = _schema(tree, namespace=namespace)
    generator = schema.generator(extension=extension)

    return oamap.proxy.ListProxy(generator, oamap.backend.root.ROOTArrays(tree, oamap.backend.root.ROOTBackend([tree._context.sourcepath], tree._context.treename, namespace)), generator._newcache(), 0, 1, tree.numentries)

def schema(path, namespace=None):
    import uproot

    if namespace is None:
        namespace = "root.cmsnano({0})".format(repr(path))

    def localsource(path):
        return uproot.source.file.FileSource(path, chunkbytes=8*1024, limitbytes=None)

    return _schema(uproot.open(path, localsource=localsource)["Events"], namespace=namespace)

def _schema(tree, namespace=None):
    if namespace is None:
        namespace = "root.cmsnano({0})".format(repr(path))

    schema = oamap.backend.root._schema(tree, namespace=namespace)

    groups = OrderedDict()
    for name in list(schema.content.keys()):
        if isinstance(schema.content[name], oamap.schema.List) and "_" in name:
            try:
                branch = tree[schema.content[name].starts]
            except KeyError:
                pass
            else:
                underscore = name.index("_")
                groupname, fieldname = name[:underscore], name[underscore + 1:]
                countbranchname = branch.countbranch.name
                if not isinstance(countbranchname, str):
                    countbranchname = countbranchname.decode("ascii")
                if groupname not in groups:
                    groups[groupname] = schema.content[groupname] = \
                        oamap.schema.List(oamap.schema.Record({}, name=groupname), starts=countbranchname, stops=countbranchname, namespace=namespace)
                assert countbranchname == schema.content[groupname].starts
                groups[groupname].content[fieldname] = schema.content[name].content
                del schema.content[name]

        elif "MET_" in name or name.startswith("LHE_") or name.startswith("Pileup_") or name.startswith("PV_"):
            underscore = name.index("_")
            groupname, fieldname = name[:underscore], name[underscore + 1:]
            if groupname not in groups:
                groups[groupname] = schema.content[groupname] = \
                    oamap.schema.Record({}, name=groupname)
            groups[groupname][fieldname] = schema.content[name]
            del schema.content[name]

    hlt = oamap.schema.Record({}, name="HLT")
    flag = oamap.schema.Record({}, name="Flag")
    for name in schema.content.keys():
        if name.startswith("HLT_"):
            hlt[name[4:]] = schema.content[name]
            del schema.content[name]
        if name.startswith("Flag_"):
            flag[name[5:]] = schema.content[name]
            del schema.content[name]

    schema.content["HLT"] = hlt
    schema.content["Flag"] = flag
    schema.content.name = "Event"
    return schema
