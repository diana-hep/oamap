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

import oamap.generator
import oamap.inference
import oamap.fillcolumn

def toarrays(fillables):
    return dict((n, x[:]) for n, x in fillables.items())

################################################################ Python data, possibly made with json.load

def fromdata(value, generator=None, fillables=None):
    if generator is None:
        generator = oamap.inference.fromdata(value).generator()

    if not isinstance(generator, oamap.generator.Generator):
        generator = generator.generator()

    if fillables is None:
        fillables = oamap.fillcolumn.fillablearrays(generator)

    lastindex = {}
    def update(gen, recurse):
        if isinstance(gen, oamap.generator.PrimitiveGenerator):
            lastindex[id(gen)] = len(fillables[gen.data])
        elif isinstance(gen, oamap.generator.ListGenerator):
            if recurse:
                update(gen.content, True)
            assert fillables[gen.starts] == fillables[gen.stops]
            lastindex[id(gen)] = len(fillables[gen.stops])
        elif isinstance(gen, oamap.generator.UnionGenerator):
            if recurse:
                for x in gen.possibilities:
                    update(x, True)
            assert fillables[gen.tags] == fillables[gen.offsets]
            lastindex[id(gen)] = len(fillables[gen.tags])
        elif isinstance(gen, oamap.generator.RecordGenerator):
            if recurse:
                uniques = set(update(x, True) for x in gen.fields.values())
                assert len(uniques) == 1
                lastindex[id(gen)] = list(uniques)[0]
            else:
                lastindex[id(gen)] = update(list(gen.fields.values())[0], False)
        elif isinstance(gen, oamap.generator.TupleGenerator):
            if recurse:
                uniques = set(update(x, True) for x in gen.types)
                assert len(uniques) == 1
                lastindex[id(gen)] = list(uniques)[0]
            else:
                lastindex[id(gen)] = update(gen.types[0], False)
        elif isinstance(gen, oamap.generator.PointerGenerator):
            if recurse and not gen._internal:
                update(gen.target, True)
            lastindex[id(gen)] = len(fillables[gen.positions])
            if recurse and gen.target is generator and isinstance(generator, ListGenerator) and lastindex[id(generator)] != 0:
                raise TypeError("oamap.fill.fromdata can only be called multiple times on the same fillables if there are no Pointers to the top-level List")
        else:
            raise TypeError("unrecognized generator: {0}".format(repr(gen)))
        if isinstance(gen, Masked):
            assert lastindex[id(gen)] == fillables[gen.mask]
        return lastindex[id(gen)]

    update(generator, True)

    initindex = dict(lastindex)
    def revert(gen):
        if isinstance(gen, oamap.generator.PrimitiveGenerator):
            fillables[gen.data].revert(initindex[id(gen)])
        elif isinstance(gen, oamap.generator.ListGenerator):
            revert(gen.content)
            fillables[gen.starts].revert(initindex[id(gen)])
            fillables[gen.stops].revert(initindex[id(gen)])
        elif isinstance(gen, oamap.generator.UnionGenerator):
            for x in gen.possibilities: revert(x)
            fillables[gen.tags].revert(initindex[id(gen)])
            fillables[gen.offsets].revert(initindex[id(gen)])
        elif isinstance(gen, oamap.generator.RecordGenerator):
            for x in gen.fields.values(): revert(x)
        elif isinstance(gen, oamap.generator.TupleGenerator):
            for x in gen.types: revert(x)
        elif isinstance(gen, oamap.generator.PointerGenerator):
            if not gen._internal: revert(x.target)
            fillables[gen.positions].revert(initindex[id(gen)])
        if isinstance(gen, Masked):
            fillables[gen.mask].revert(initindex[id(gen)])

    def recurse(obj, gen):
        if isinstance(gen, oamap.generator.PrimitiveGenerator):
            fillables[gen.data].append(0 if obj is None else obj)

        elif isinstance(gen, oamap.generator.ListGenerator):
            if obj is None:
                start = stop = -1
            else:
                start = stop = lastindex[id(gen.content)]
                try:
                    if isinstance(obj, dict) or (isinstance(obj, tuple) and hasattr(obj, "_fields")):
                        raise TypeError
                    iter(obj)
                except TypeError:
                    raise TypeError("cannot fill {0} where expecting type {1}".format(repr(obj), gen.schema))
                else:
                    for x in obj:
                        recurse(x, gen.content)
                        stop += 1
                    update(gen.content, False)

            fillables[gen.starts].append(start)
            fillables[gen.stops].append(stop)

        elif isinstance(gen, oamap.generator.UnionGenerator):
            if obj is None:
                tag = offset = -1
            else:
                tag = None
                for i, possibility in gen.possibilities:
                    if obj in possibility:
                        tag = i
                        break
                if tag is None:
                    raise TypeError("cannot fill {0} where expecting type {1}".format(repr(obj), gen.schema))
                
                offset = lastindex[id(possibility)]
                recurse(obj, possibility)
                update(possibility, False)

            fillables[gen.tags].append(tag)
            fillables[gen.offsets].append(offset)

        elif isinstance(gen, oamap.generator.RecordGenerator):
            if obj is None:
                pass
            elif isinstance(obj, dict):
                for n, x in gen.fields.items():
                    if n not in obj:
                        raise TypeError("cannot fill {0} because its {1} field is missing".format(repr(obj), repr(n)))
                    recurse(obj[n], x)
            else:
                for n, x in gen.fields.items():
                    if not hasattr(obj, n):
                        raise TypeError("cannot fill {0} because its {1} field is missing".format(repr(obj), repr(n)))
                    recurse(getattr(obj, n), x)

        elif isinstance(gen, oamap.generator.TupleGenerator):
            if obj is None:
                pass
            else:
                for i, x in enumerate(gen.types):
                    try:
                        v = obj[i]
                    except (TypeError, IndexError):
                        raise TypeError("cannot fill {0} because it does not have a field {1}".format(repr(obj), i))
                    else:
                        recurse(v, x)

        elif isinstance(gen, oamap.generator.PointerGenerator):
            raise NotImplementedError
        
        if isinstance(gen, oamap.generator.Masked):
            if obj is None:
                fillables[gen.mask].append(True)
            else:
                fillables[gen.mask].append(False)

    if lastindex[id(generator)] != 0 and not isinstance(generator, ListGenerator):
        raise TypeError("oamap.fill.fromdata can only be called multiple times on the same fillables if the data type is a List (to append to the List)")

    try:
        recurse(value, generator)
    except:
        revert(generator)
        raise
    else:
        return fillables
