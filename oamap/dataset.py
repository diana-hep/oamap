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

import copy
import numbers
import functools

import numpy

import oamap.generator
import oamap.operations
import oamap.proxy
import oamap.schema
import oamap.util
        
class SingleThreadExecutor(object):
    class PseudoFuture(object):
        def __init__(self, result):
            self._result = result
        def result(self, timeout=None):
            return self._result
        def done(self):
            return True
        def exception(self, timeout=None):
            raise NotImplementedError
        def traceback(self, timeout=None):
            raise NotImplementedError

    def submit(self, fcn, *args, **kwargs):
        args = tuple(x.result() if isinstance(x, self.PseudoFuture) else x for x in args)
        kwargs = dict((n, x.result() if isinstance(x, self.PseudoFuture) else x) for n, x in kwargs.items())
        return self.PseudoFuture(fcn(*args, **kwargs))

class Operation(object):
    def __init__(self, name, args, kwargs, function):
        self._name = name
        self._args = args
        self._kwargs = kwargs
        self._function = function

    def __repr__(self):
        return "<{0} {1} {2} {3}>".format(self.__class__.__name__, self._name, repr(self._args), repr(self._kwargs))

    def __str__(self):
        return ".{0}({1}{2})".format(self._name, ", ".join(repr(x) for x in self._args), "".join(", {0}={1}".format(n, repr(x)) for n, x in self._kwargs.items()))

    @property
    def name(self):
        return self._name

    @property
    def args(self):
        return self._args

    @property
    def kwargs(self):
        return self._kwargs

    @property
    def function(self):
        return self._function

    def apply(self, data):
        return self._function(*((data,) + self._args), **self._kwargs)

class Recasting(Operation): pass
class Transformation(Operation): pass
class Action(Operation): pass

class Operable(object):
    def __init__(self):
        self._operations = ()

    @staticmethod
    def update_operations():
        def newrecasting(name, function):
            @functools.wraps(function)
            def recasting(self, *args, **kwargs):
                out = self.__class__.__new__(self.__class__)
                Operable.__init__(out)
                out.__dict__ = self.__dict__.copy()
                out._operations = self._operations + (Recasting(name, args, kwargs, function),)
                return out
            return recasting

        def newtransformation(name, function):
            @functools.wraps(function)
            def transformation(self, *args, **kwargs):
                out = self.__class__.__new__(self.__class__)
                Operable.__init__(out)
                out.__dict__ = self.__dict__.copy()
                out._operations = self._operations + (Transformation(name, args, kwargs, function),)
                return out
            return transformation

        def newaction(name, function):
            @functools.wraps(function)
            def action(self, *args, **kwargs):
                try:
                    combiner = kwargs.pop("combiner")
                except KeyError:
                    combiner = function.combiner
                out = self.__class__.__new__(self.__class__)
                Operable.__init__(out)
                out.__dict__ = self.__dict__.copy()
                out._operations = self._operations + (Action(name, args, kwargs, function),)
                return out.act(combiner)
            return action

        for n, x in oamap.operations.recastings.items():
            setattr(Operable, n, oamap.util.MethodType(newrecasting(n, x), None, Operable))

        for n, x in oamap.operations.transformations.items():
            setattr(Operable, n, oamap.util.MethodType(newtransformation(n, x), None, Operable))

        for n, x in oamap.operations.actions.items():
            setattr(Operable, n, oamap.util.MethodType(newaction(n, x), None, Operable))

    def _notransformations(self):
        return all(isinstance(x, Recasting) for x in self._operations)

Operable.update_operations()

class _Data(Operable):
    def __init__(self, name, schema, backends, executor, extension=None, packing=None, doc=None, metadata=None):
        super(_Data, self).__init__()
        self._name = name
        self._schema = schema
        self._backends = backends
        self._executor = executor
        self._extension = extension
        self._packing = packing
        self._doc = doc
        self._metadata = metadata
        self._cachedobject = None

    def __repr__(self):
        return "<Data {0}>{1}".format(repr(self._name), "".join(str(x) for x in self._operations))

    def __str__(self):
        return "<Data {0}>{1}".format(repr(self._name), "".join("\n    " + str(x) for x in self._operations))
    
    @property
    def name(self):
        return self._name

    @property
    def schema(self):
        return self._schema.deepcopy()

    @property
    def extension(self):
        return self._extension

    @property
    def packing(self):
        return self._packing

    @property
    def doc(self):
        return self._doc

    @property
    def metadata(self):
        return self._metadata

    def arrays(self):
        return DataArrays(self._backends)

    def transform(self, name, namespace, update):
        if self._notransformations():
            result = self()
            for operation in self._operations:
                result = operation.apply(result)
            if isinstance(result, oamap.proxy.ListProxy):
                out = Dataset(name, result._generator.schema, self._backends, self._executor, [0, len(result)], extension=self._extension, packing=None, doc=self._doc, metadata=self._metadata)
            else:
                out = Data(name, result._generator.schema, self._backends, self._executor, extension=self._extension, packing=None, doc=self._doc, metadata=self._metadata)
            return [SingleThreadExecutor.PseudoFuture(update(out))]

        else:
            def task(name, dataset, namespace, update):
                result = dataset()
                for operation in dataset._operations:
                    result = operation.apply(result)

                backend = dataset._backends[namespace]
                schema, roles2arrays = oamap.operations._DualSource.collect(result._generator.namedschema(), result._arrays, namespace, backend.prefix(name), backend.delimiter())

                active = backend.instantiate(0)
                if hasattr(active, "putall"):
                    active.putall(roles2arrays)
                else:
                    for n, x in roles2arrays.items():
                        active[str(n)] = x
                
                if isinstance(result, oamap.proxy.ListProxy):
                    out = Dataset(name, schema, dataset._backends, dataset._executor, [0, len(result)], extension=dataset._extension, packing=None, doc=dataset._doc, metadata=dataset._metadata)
                else:
                    out = Data(name, schema, dataset._backends, dataset._executor, extension=dataset._extension, packing=None, doc=dataset._doc, metadata=dataset._metadata)
                return update(out)

            return [self._executor.submit(task, name, self, namespace, update)]

    def act(self, combiner):
        def task(dataset):
            result = dataset()
            for operation in dataset._operations:
                result = operation.apply(result)
            return result

        return combiner([self._executor.submit(task, self)])
            
class Data(_Data):
    def __call__(self):
        if self._cachedobject is None:
            if self._extension is None:
                extension = oamap.util.import_module("oamap.extension.common")
            elif isinstance(self._extension, basestring):
                extension = oamap.util.import_module(self._extension)
            else:
                extension = [oamap.util.import_module(x) for x in self._extension]

            self._cachedobject = self._schema(self.arrays(), extension=extension, packing=self._packing)

        return self._cachedobject

class DataArrays(object):
    def __init__(self, backends):
        self._backends = backends
        self._active = {}
        self._partitionid = 0

    def _toplevel(self, out, filtered):
        return filtered

    def getall(self, roles):
        out = {}
        for namespace, backend in self._backends.items():
            filtered = self._toplevel(out, [x for x in roles if x.namespace == namespace])

            if len(filtered) > 0:
                active = self._active.get(namespace, None)
                if active is None:
                    active = self._active[namespace] = backend.instantiate(self._partitionid)

                if hasattr(active, "getall"):
                    out.update(active.getall(filtered))
                else:
                    for x in roles:
                        out[x] = active[str(x)]

        return out

    def close(self):
        for namespace, active in self._active.items():
            if hasattr(active, "close"):
                active.close()
            self._active[namespace] = None
                
class Dataset(_Data):
    def __init__(self, name, schema, backends, executor, offsets, extension=None, packing=None, doc=None, metadata=None):
        if not isinstance(schema, oamap.schema.List):
            raise TypeError("Dataset must have a list schema, not\n\n    {0}".format(schema.__repr__(indent="    ")))

        super(Dataset, self).__init__(name, schema, backends, executor, extension=extension, packing=packing, doc=doc, metadata=metadata)

        if not isinstance(offsets, numpy.ndarray):
            try:
                if not all(isinstance(x, (numbers.Integral, numpy.integer)) and x >= 0 for x in offsets):
                    raise TypeError
            except TypeError:
                raise TypeError("offsets must be an iterable of non-negative integers")
            offsets = numpy.array(offsets, dtype=numpy.int64)
        if len(offsets.shape) != 1:
            raise ValueError("offsets must be one-dimensional")
        if len(offsets) < 2 or offsets[0] != 0:
            raise ValueError("offsets must have at least two items, and the first one must be zero")
        if not numpy.all(offsets[:-1] <= offsets[1:]):
            raise ValueError("offsets must be monotonically increasing")
        self._offsets = offsets
        self._cachedpartition = None

    def __repr__(self):
        return "<Dataset {0} {1} partitions {2} entries>{3}".format(repr(self._name), self.numpartitions, self.numentries, "".join(str(x) for x in self._operations))

    def __str__(self):
        return "<Dataset {0} {1} partitions {2} entries>{3}".format(repr(self._name), self.numpartitions, self.numentries, "".join("\n    " + str(x) for x in self._operations))

    @property
    def offsets(self):
        return self._offsets.tolist()

    @property
    def starts(self):
        return self._offsets[:-1].tolist()

    @property
    def stops(self):
        return self._offsets[1:].tolist()

    @property
    def partitions(self):
        return zip(self.start, self.stop)

    @property
    def numpartitions(self):
        return len(self._offsets) - 1

    @property
    def numentries(self):
        return int(self._offsets[-1])

    def partition(self, partitionid):
        if self._cachedpartition != partitionid:
            self._cachedpartition = partitionid

            if self._extension is None:
                extension = oamap.util.import_module("oamap.extension.common")
            elif isinstance(self._extension, basestring):
                extension = oamap.util.import_module(self._extension)
            else:
                extension = [oamap.util.import_module(x) for x in self._extension]

            self._cachedobject = self._schema(self.arrays(partitionid), extension=extension, packing=self._packing)

        return self._cachedobject

    def __iter__(self):
        for partitionid in range(self.numpartitions):
            for i in range(self._offsets[partitionid], self._offsets[partitionid + 1]):
                yield self[i]

    def __getitem__(self, index):
        if isinstance(index, slice):
            start, stop, step = oamap.util.slice2sss(index, self.numentries)
            partitionid = max(0, min(numpy.searchsorted(self._offsets, start, side="right") - 1, self.numpartitions - 1))
            localstart = start - self._offsets[partitionid]
            localstop = stop - self._offsets[partitionid]
            if localstop < -1 or localstop > (self._offsets[partitionid + 1] - self._offsets[partitionid]):
                raise IndexError("slice spans multiple partitions")

            out = self.partition(partitionid)
            out._whence = localstart
            out._stride = step

            # out._length = int(math.ceil(float(abs(localstop - localstart)) / abs(step)))
            d, m = divmod(abs(localstart - localstop), abs(step))
            out._length = d + (1 if m != 0 else 0)
            return out

        else:
            normindex = index if index >= 0 else index + self.numentries
            if not 0 <= normindex < self.numentries:
                raise IndexError("index {0} out of range for {1} entries".format(index, self.numentries))
            partitionid = numpy.searchsorted(self._offsets, normindex, side="right") - 1
            localindex = normindex - self._offsets[partitionid]
            return self.partition(partitionid)[localindex]

    def arrays(self, partitionid):
        normid = partitionid if partitionid >= 0 else partitionid + self.numpartitions
        if not 0 <= normid < self.numpartitions:
            raise IndexError("partitionid {0} out of range for {1} partitions".format(partitionid, self.numpartitions))

        startsrole = oamap.generator.StartsRole(self._schema._get_starts("object", "-"), self._schema.namespace, None)
        stopsrole = oamap.generator.StopsRole(self._schema._get_stops("object", "-"), self._schema.namespace, None)
        startsrole.stops = stopsrole
        stopsrole.starts = startsrole
        return DatasetArrays(normid, startsrole, stopsrole, self._offsets[normid + 1] - self._offsets[normid], self._backends)

    def transform(self, name, namespace, update):
        if self._notransformations():
            result = self.partition(0)
            for operation in self._operations:
                result = operation.apply(result)
            if isinstance(result, oamap.proxy.ListProxy):
                out = Dataset(name, result._generator.schema, self._backends, self._executor, self._offsets, extension=self._extension, packing=None, doc=self._doc, metadata=self._metadata)
            else:
                out = Data(name, result._generator.schema, self._backends, self._executor, extension=self._extension, packing=None, doc=self._doc, metadata=self._metadata)
            return [SingleThreadExecutor.PseudoFuture(update(out))]

        else:
            def task(name, dataset, namespace, partitionid):
                result = dataset.partition(partitionid)
                for operation in dataset._operations:
                    result = operation.apply(result)

                backend = dataset._backends[namespace]
                schema, roles2arrays = oamap.operations._DualSource.collect(result._generator.namedschema(), result._arrays, namespace, backend.prefix(name), backend.delimiter())

                active = backend.instantiate(partitionid)
                if hasattr(active, "putall"):
                    active.putall(roles2arrays)
                else:
                    for n, x in roles2arrays.items():
                        active[str(n)] = x
                if isinstance(result, oamap.proxy.ListProxy):
                    return schema, len(result)
                else:
                    return schema, 1

            tasks = [self._executor.submit(task, name, self, namespace, i) for i in range(self.numpartitions)]

            def collect(name, dataset, results, update):
                if isinstance(results[0], tuple) and len(results[0]) == 2 and isinstance(results[0][0], oamap.schema.Schema):
                    offsets = numpy.cumsum([0] + [numentries for schema, numentries in results], dtype=numpy.int64)
                    schema = results[0][0]
                else:
                    offsets = numpy.cumsum([0] + [x.result()[1] for x in results], dtype=numpy.int64)
                    schema = results[0].result()[0]

                if isinstance(schema, oamap.schema.List):
                    out = Dataset(name, schema, dataset._backends, dataset._executor, offsets, extension=dataset._extension, packing=None, doc=dataset._doc, metadata=dataset._metadata)
                else:
                    out = Data(name, schema, dataset._backends, dataset._executor, extension=dataset._extension, packing=None, doc=dataset._doc, metadata=dataset._metadata)
                return update(out)

            tasks.append(self._executor.submit(collect, name, self, tuple(tasks), update))
            return tasks

    def act(self, combiner):
        def task(dataset, partitionid):
            result = dataset.partition(partitionid)
            for operation in dataset._operations:
                result = operation.apply(result)
            return result

        return combiner([self._executor.submit(task, self, i) for i in range(self.numpartitions)])

class DatasetArrays(DataArrays):
    def __init__(self, partitionid, startsrole, stopsrole, numentries, backends):
        super(DatasetArrays, self).__init__(backends)
        self._partitionid = partitionid
        self._startsrole = startsrole
        self._stopsrole = stopsrole
        self._numentries = numentries

    def _toplevel(self, out, filtered):
        try:
            index = filtered.index(self._startsrole)
        except ValueError:
            pass
        else:
            del filtered[index]
            out[self._startsrole] = numpy.array([0], dtype=oamap.generator.ListGenerator.posdtype)

        try:
            index = filtered.index(self._stopsrole)
        except ValueError:
            pass
        else:
            del filtered[index]
            out[self._stopsrole] = numpy.array([self._numentries], dtype=oamap.generator.ListGenerator.posdtype)

        return filtered
    
