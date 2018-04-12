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

import math
import numbers
import sys

import numpy

import oamap.schema
import oamap.generator
import oamap.proxy

if sys.version_info[0] < 3:
    range = xrange

################################################################ utilities

def newvar(avoid, trial=None):
    while trial is None or trial in avoid:
        trial = "v" + str(len(avoid))
    avoid.add(trial)
    return trial

def trycompile(numba):
    if numba is None or numba is False:
        return lambda fcn: fcn
    else:
        try:
            import numba as nb
        except ImportError:
            return lambda fcn: fcn
        else:
            if numba is True:
                numbaopts = {}
            else:
                numbaopts = numba
            return lambda fcn: fcn if isinstance(fcn, nb.dispatcher.Dispatcher) else nb.jit(**numbaopts)(fcn)

class DualSource(object):
    def __init__(self, old, oldns):
        self.old = old
        self.new = {}

        i = 0
        self.namespace = None
        while self.namespace is None or self.namespace in oldns:
            self.namespace = "namespace-" + str(i)
            i += 1

        self._arraynum = 0

    def arrayname(self):
        trial = None
        while trial is None or trial in self.new:
            trial = "array-" + str(self._arraynum)
            self._arraynum += 1
        return trial

    def getall(self, roles):
        out = {}

        if hasattr(self.old, "getall"):
            out.update(self.old.getall([x for x in roles if x.namespace != self.namespace]))
        else:
            for x in roles:
                if x.namespace != self.namespace:
                    out[x] = self.old[str(x)]

        if hasattr(self.new, "getall"):
            out.update(self.new.getall([x for x in roles if x.namespace == self.namespace]))
        else:
            for x in roles:
                if x.namespace == self.namespace:
                    out[x] = self.new[str(x)]

        return out

    def put(self, schemanode, *arrays):
        if isinstance(schemanode, oamap.schema.Primitive):
            datarole = oamap.generator.DataRole(self.arrayname(), self.namespace)
            roles2arrays = {datarole: arrays[0]}
            schemanode.data = str(datarole)

        elif isinstance(schemanode, oamap.schema.List):
            startsrole = oamap.generator.StartsRole(self.arrayname(), self.namespace, None)
            stopsrole = oamap.generator.StopsRole(self.arrayname(), self.namespace, None)
            startsrole.stops = stopsrole
            stopsrole.starts = startsrole
            roles2arrays = {startsrole: arrays[0], stopsrole: arrays[1]}
            schemanode.starts = str(startsrole)
            schemanode.stops = str(stopsrole)

        elif isinstance(schemanode, oamap.schema.Union):
            tagsrole = oamap.generator.TagsRole(self.arrayname(), self.namespace, None)
            offsetsrole = oamap.generator.OffsetsRole(self.arrayname(), self.namespace, None)
            tagsrole.offsets = offsetsrole
            offsetsrole.tags = tagsrole
            roles2arrays = {tagsrole: arrays[0], offsetsrole: arrays[1]}
            schemanode.tags = str(tagsrole)
            schemanode.offsets = str(offsetsrole)

        elif isinstance(schemanode, oamap.schema.Record):
            pass

        elif isinstance(schemanode, oamap.schema.Tuple):
            pass

        elif isinstance(schemanode, oamap.schema.Pointer):
            positionsrole = oamap.generator.PositionsRole(self.arrayname(), self.namespace)
            roles2arrays = {positionsrole: arrays[0]}
            schemanode.positions = str(positionsrole)

        else:
            raise AssertionError(schemanode)

        if schemanode.nullable:
            maskrole = oamap.generator.MaskRole(self.arrayname(), self.namespace, roles2arrays)
            roles2arrays = dict(list(roles2arrays.items()) + [(maskrole, arrays[-1])])
            schemanode.mask = str(maskrole)

        schemanode.namespace = self.namespace
        self.putall(roles2arrays)

    def putall(self, roles2arrays):
        if hasattr(self.new, "putall"):
            self.new.putall(roles2arrays)
        else:
            for n, x in roles2arrays.items():
                self.new[str(n)] = x

    def close(self):
        if hasattr(self.old, "close"):
            self.old.close()
        if hasattr(self.new, "close"):
            self.new.close()

def _setindexes(input, output):
    if isinstance(input, oamap.proxy.ListProxy):
        output._whence, output._stride, output._length = input._whence, input._stride, input._length
    elif isinstance(input, oamap.proxy.RecordProxy):
        output._index = input._index
    elif isinstance(input, oamap.proxy.TupleProxy):
        output._index = input._index
    else:
        raise AssertionError(type(input))
    return output
    
################################################################ rename

def rename(data, path, fieldname):
    raise NotImplementedError

################################################################ project/keep/drop

def project(data, path):
    if isinstance(data, oamap.proxy.Proxy):
        schema = data._generator.namedschema().project(path)
        if schema is None:
            raise TypeError("projection resulted in no schema")
        return _setindexes(data, schema(data._arrays))
    else:
        raise TypeError("project can only be applied to an OAMap proxy (List, Record, Tuple)")

def keep(data, *paths):
    if isinstance(data, oamap.proxy.Proxy):
        schema = data._generator.namedschema().keep(*paths)
        if schema is None:
            raise TypeError("keep operation resulted in no schema")
        return _setindexes(data, schema(data._arrays))
    else:
        raise TypeError("keep can only be applied to an OAMap proxy (List, Record, Tuple)")

def drop(data, *paths):
    if isinstance(data, oamap.proxy.Proxy):
        schema = data._generator.namedschema().drop(*paths)
        if schema is None:
            raise TypeError("drop operation resulted in no schema")
        return _setindexes(data, schema(data._arrays))
    else:
        raise TypeError("drop can only be applied to an OAMap proxy (List, Record, Tuple)")

################################################################ split

def split(data, *paths):
    if isinstance(data, oamap.proxy.Proxy):
        schema = data._generator.namedschema()

        for path in paths:
            for nodes in schema.paths(path, parents=True):
                if len(nodes) >= 4 and isinstance(nodes[1], oamap.schema.Record) and isinstance(nodes[2], oamap.schema.List) and isinstance(nodes[3], oamap.schema.Record):
                    datanode, innernode, listnode, outernode = nodes[0], nodes[1], nodes[2], nodes[3]
                    for n, x in innernode.fields.items():
                        if x is datanode:
                            innername = n
                            break
                    for n, x in outernode.fields.items():
                        if x is listnode:
                            outername = n
                            break

                    del innernode[innername]
                    if len(innernode.fields) == 0:
                        del outernode[outername]

                    outernode[innername] = listnode.copy(content=datanode)

                else:
                    raise TypeError("path {0} matches a field that is not in a Record(List(Record({{field: ...}})))".format(repr(path)))

        return schema(data._arrays)

    else:
        raise TypeError("split can only be applied to an OAMap proxy (List, Record, Tuple)")

################################################################ merge

def merge(data, *paths):
    if isinstance(data, oamap.proxy.Proxy):
        schema = data._generator.namedschema()
        





    else:
        raise TypeError("merge can only be applied to an OAMap proxy (List, Record, Tuple)")

################################################################ mask

def mask(data, path, low, high=None):
    if isinstance(data, oamap.proxy.Proxy):
        schema = data._generator.namedschema()
        nodes = schema.path(path, parents=True)
        while isinstance(nodes[0], oamap.schema.List):
            nodes = (nodes[0].content,) + nodes
        node = nodes[0]

        arrays = DualSource(data._arrays, data._generator.namespaces())

        if isinstance(node, oamap.schema.Primitive):
            generator = data._generator.findbynames("Primitive", data=node.data, mask=node.mask)

            primitive = generator._getdata(data._arrays, data._cache).copy()
            if node.nullable:
                mask = generator._getmask(data._arrays, data._cache).copy()
            else:
                node.nullable = True
                mask = numpy.arange(len(primitive), dtype=oamap.generator.Masked.maskdtype)

            if high is None:
                if math.isnan(low):
                    selection = numpy.isnan(primitive)
                else:
                    selection = (primitive == low)
            else:
                if math.isnan(low) or math.isnan(high):
                    raise ValueError("if a range is specified, neither of the endpoints can be NaN")
                selection = (primitive >= low)
                numpy.bitwise_and(selection, (primitive <= high), selection)

            mask[selection] = oamap.generator.Masked.maskedvalue

            arrays.put(node, primitive, mask)

        else:
            raise NotImplementedError("mask operation only defined on primitive fields; {0} matches:\n\n    {1}".format(repr(path), node.__repr__(indent="    ")))

        return _setindexes(data, schema(arrays))

    else:
        raise TypeError("mask can only be applied to an OAMap proxy (List, Record, Tuple)")

################################################################ flatten

# FIXME: at=""

def flatten(data):
    if isinstance(data, oamap.proxy.ListProxy) and data._whence == 0 and data._stride == 1 and isinstance(data._generator.content, oamap.generator.ListGenerator):
        if isinstance(data._generator, oamap.generator.Masked) or isinstance(data._generator.content, oamap.generator.Masked):
            raise NotImplementedError("nullable; need to merge masks")

        schema = data._generator.namedschema()
        schema.content = schema.content.content

        starts, stops = data._generator.content._getstartsstops(data._arrays, data._cache)

        arrays = DualSource(data._arrays, data._generator.namespaces())

        if numpy.array_equal(starts[1:], stops[:-1]):
            # important special case: contiguous
            arrays.put(schema, starts[:1], stops[-1:])
            return schema(arrays)
        else:
            raise NotImplementedError("non-contiguous arrays: have to do some sort of concatenation")

    else:
        raise TypeError("flatten can only be applied to List(List(...))")

################################################################ filter

def filter(data, fcn, args=(), at="", numba=True):
    if not isinstance(args, tuple):
        try:
            args = tuple(args)
        except TypeError:
            args = (args,)

    if isinstance(data, oamap.proxy.ListProxy) and data._whence == 0 and data._stride == 1:
        schema = data._generator.namedschema()
        listnode = schema.path(at)
        if not isinstance(listnode, oamap.schema.List):
            raise TypeError("path {0} does not refer to a list:\n\n    {1}".format(repr(at), listnode.__repr__(indent="    ")))
        if listnode.nullable:
            raise NotImplementedError("nullable; need to merge masks")

        listgenerator = data._generator.findbynames("List", starts=listnode.starts, stops=listnode.stops)
        viewstarts, viewstops = listgenerator._getstartsstops(data._arrays, data._cache)
        viewschema = listgenerator.namedschema()
        viewarrays = DualSource(data._arrays, data._generator.namespaces())
        viewoffsets = numpy.array([viewstarts.min(), viewstops.max()], dtype=oamap.generator.ListGenerator.posdtype)
        viewarrays.put(viewschema, viewoffsets[:1], viewoffsets[-1:])
        view = viewschema(viewarrays)

        params = fcn.__code__.co_varnames[:fcn.__code__.co_argcount]
        avoid = set(params)
        fcnname = newvar(avoid, "fcn")
        fillname = newvar(avoid, "fill")
        lenname = newvar(avoid, "len")
        rangename = newvar(avoid, "range")

        fcn = trycompile(numba)(fcn)
        env = {fcnname: fcn, lenname: len, rangename: xrange if sys.version_info[0] <= 2 else range}
        exec("""
def {fill}({view}, {viewstarts}, {viewstops}, {stops}, {pointers}{params}):
    {numitems} = 0
    for {i} in {range}({len}({viewstarts})):
        for {j} in {range}({viewstarts}[{i}], {viewstops}[{i}]):
            {datum} = {view}[{j}]
            if {fcn}({datum}{params}):
                {pointers}[{numitems}] = {j}
                {numitems} += 1
        {stops}[{i}] = {numitems}
    return {numitems}
""".format(fill=fillname,
           view=newvar(avoid, "view"),
           viewstarts=newvar(avoid, "viewstarts"),
           viewstops=newvar(avoid, "viewstops"),
           stops=newvar(avoid, "stops"),
           pointers=newvar(avoid, "pointers"),
           params="".join("," + x for x in params[1:]),
           numitems=newvar(avoid, "numitems"),
           i=newvar(avoid, "i"),
           range=rangename,
           len=lenname,
           j=newvar(avoid, "j"),
           datum=newvar(avoid, "datum"),
           fcn=fcnname), env)
        fill = trycompile(numba)(env[fillname])

        offsets = numpy.empty(len(viewstarts) + 1, dtype=oamap.generator.ListGenerator.posdtype)
        offsets[0] = 0
        pointers = numpy.empty(len(view), dtype=oamap.generator.PointerGenerator.posdtype)
        numitems = fill(*((view, viewstarts, viewstops, offsets[1:], pointers) + args))
        pointers = pointers[:numitems]

        listnode.content = oamap.schema.Pointer(listnode.content)

        if isinstance(listgenerator.content, oamap.generator.PointerGenerator):
            if isinstance(listgenerator.content, oamap.generator.Masked):
                raise NotImplementedError("nullable; need to merge masks")
            innerpointers = listgenerator.content._getpositions(data._arrays, data._cache)
            pointers = innerpointers[pointers]
            listnode.content.target = listnode.content.target.target

        arrays = DualSource(data._arrays, data._generator.namespaces())
        arrays.put(listnode, offsets[:-1], offsets[1:])
        arrays.put(listnode.content, pointers)
        return schema(arrays)

    else:
        raise TypeError("filter can only be applied to a top-level List(...)")

################################################################ define

def define(data, fieldname, fcn, args=(), at="", fieldtype=oamap.schema.Primitive(numpy.float64), numba=True):
    if not isinstance(args, tuple):
        try:
            args = tuple(args)
        except TypeError:
            args = (args,)

    if isinstance(data, oamap.proxy.ListProxy) and data._whence == 0 and data._stride == 1:
        schema = data._generator.namedschema()
        nodes = schema.path(at, parents=True)
        while isinstance(nodes[0], oamap.schema.List):
            nodes = (nodes[0].content,) + nodes
        if not isinstance(nodes[0], oamap.schema.Record):
            raise TypeError("path {0} does not refer to a record:\n\n    {1}".format(repr(at), nodes[0].__repr__(indent="    ")))
        if len(nodes) < 2 or not isinstance(nodes[1], oamap.schema.List):
            raise TypeError("path {0} does not refer to a record in a list:\n\n    {1}".format(repr(at), nodes[1].__repr__(indent="    ")))
        recordnode = nodes[0]
        listnode = nodes[1]
        if recordnode.nullable or listnode.nullable:
            raise NotImplementedError("nullable; need to merge masks")

        recordnode[fieldname] = fieldtype.deepcopy()

        listgenerator = data._generator.findbynames("List", starts=listnode.starts, stops=listnode.stops)
        viewstarts, viewstops = listgenerator._getstartsstops(data._arrays, data._cache)
        viewschema = listgenerator.namedschema()
        viewarrays = DualSource(data._arrays, data._generator.namespaces())
        if numpy.array_equal(viewstarts[1:], viewstops[:-1]):
            viewarrays.put(viewschema, viewstarts[:1], viewstops[-1:])
        else:
            raise NotImplementedError("non-contiguous arrays: have to do some sort of concatenation")
        view = viewschema(viewarrays)

        params = fcn.__code__.co_varnames[:fcn.__code__.co_argcount]
        avoid = set(params)
        fcnname = newvar(avoid, "fcn")
        fillname = newvar(avoid, "fill")

        if isinstance(fieldtype, oamap.schema.Primitive) and not fieldtype.nullable:
            fcn = trycompile(numba)(fcn)
            env = {fcnname: fcn}
            exec("""
def {fill}({view}, {primitive}{params}):
    {i} = 0
    for {datum} in {view}:
        {primitive}[{i}] = {fcn}({datum}{params})
        {i} += 1
""".format(fill=fillname,
           view=newvar(avoid, "view"),
           primitive=newvar(avoid, "primitive"),
           params="".join("," + x for x in params[1:]),
           i=newvar(avoid, "i"),
           datum=newvar(avoid, "datum"),
           fcn=fcnname), env)
            fill = trycompile(numba)(env[fillname])

            primitive = numpy.empty(len(view), dtype=fieldtype.dtype)
            fill(*((view, primitive) + args))

            arrays = DualSource(data._arrays, data._generator.namespaces())
            arrays.put(recordnode[fieldname], primitive)
            return schema(arrays)

        elif isinstance(fieldtype, oamap.schema.Primitive):
            fcn = trycompile(numba)(fcn)
            env = {fcnname: fcn}
            exec("""
def {fill}({view}, {primitive}, {mask}{params}):
    {i} = 0
    {numitems} = 0
    for {datum} in {view}:
        {tmp} = {fcn}({datum}{params})
        if {tmp} is None:
            {mask}[{i}] = {maskedvalue}
        else:
            {mask}[{i}] = {numitems}
            {primitive}[{numitems}] = {tmp}
            {numitems} += 1
        {i} += 1
    return {numitems}
""".format(fill=fillname,
           view=newvar(avoid, "view"),
           primitive=newvar(avoid, "primitive"),
           mask=newvar(avoid, "mask"),
           params="".join("," + x for x in params[1:]),
           i=newvar(avoid, "i"),
           numitems=newvar(avoid, "numitems"),
           datum=newvar(avoid, "datum"),
           tmp=newvar(avoid, "tmp"),
           fcn=fcnname,
           maskedvalue=oamap.generator.Masked.maskedvalue), env)
            fill = trycompile(numba)(env[fillname])
            
            primitive = numpy.empty(len(view), dtype=fieldtype.dtype)
            mask = numpy.empty(len(view), dtype=oamap.generator.Masked.maskdtype)
            fill(*((view, primitive, mask) + args))

            arrays = DualSource(data._arrays, data._generator.namespaces())
            arrays.put(recordnode[fieldname], primitive, mask)
            return schema(arrays)

        else:
            raise NotImplementedError("define not implemented for fieldtype:\n\n    {0}".format(fieldtype.__repr__(indent="    ")))

    else:
        raise TypeError("define can only be applied to a top-level List(...)")

################################################################ quick test

# from oamap.schema import *

# dataset = List(Record(dict(x=List("int"), y=List("double")))).fromdata([{"x": [1, 2, 3], "y": [1.1, numpy.nan]}, {"x": [], "y": []}, {"x": [4, 5], "y": [3.3]}])

# dataset = List(Record(dict(x="int", y="double"))).fromdata([{"x": 1, "y": 1.1}, {"x": 2, "y": 2.2}, {"x": 3, "y": 3.3}])

# dataset = List(Record(dict(x=List(Record({"xx": "int", "yy": "double"})), y="double"))).fromdata([{"x": [{"xx": 1, "yy": 1.1}, {"xx": 2, "yy": 2.2}], "y": 1.1}, {"x": [], "y": 2.2}, {"x": [{"xx": 3, "yy": 3.3}], "y": 3.3}])

# dataset = List(List("int")).fromdata([[1, 2, 3], [], [4, 5]])

# dataset = List(List(List("int"))).fromdata([[[1, 2, 3], [4, 5], []], [], [[6], [7, 8]]])

# def f(x, y):
#   return len(x) == y

# filter(dataset, f, (0,), numba=False)
