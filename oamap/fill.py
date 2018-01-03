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

import re
import json

import oamap.generator
import oamap.inference
import oamap.fillable

def toarrays(fillables):
    return dict((n, x[:]) for n, x in fillables.items())

################################################################ Python data, possibly made by json.load

def fromiterdata(values, generator=None, fillables=None, pointer_fromequal=False):
    for value in values:
        if generator is None:
            generator = List(oamap.inference.fromdata(value)).generator()

        if not isinstance(generator, oamap.generator.Generator):
            generator = generator.generator()

        if fillables is None:
            fillables = oamap.fillable.arrays(generator)

        fromdata(value, generator=generator, fillables=fillables, pointer_fromequal=pointer_fromequal)

    return fillables

def fromdata(value, generator=None, fillables=None, pointer_fromequal=False):
    if generator is None:
        generator = oamap.inference.fromdata(value).generator()

    if not isinstance(generator, oamap.generator.Generator):
        generator = generator.generator()

    if fillables is None:
        fillables = oamap.fillable.arrays(generator)

    # get a list of generators (innermost outward) and make sure they're all starting at the last good entry
    pointers = []
    pointerobjs_keys = []
    targetids_keys = []
    fillables_leaf_to_root = []
    def initialize(gen):
        if isinstance(gen, oamap.generator.PrimitiveGenerator):
            fillables[gen.data].revert()
            forefront = len(fillables[gen.data])
            fillables_leaf_to_root.append(fillables[gen.data])

        elif isinstance(gen, oamap.generator.ListGenerator):
            initialize(gen.content)
            fillables[gen.starts].revert()
            fillables[gen.stops].revert()
            assert len(fillables[gen.starts]) == len(fillables[gen.stops])
            forefront = len(fillables[gen.stops])
            fillables_leaf_to_root.append(fillables[gen.starts])
            fillables_leaf_to_root.append(fillables[gen.stops])

        elif isinstance(gen, oamap.generator.UnionGenerator):
            for x in gen.possibilities:
                initialize(x)
            fillables[gen.tags].revert()
            fillables[gen.offsets].revert()
            assert len(fillables[gen.tags]) == len(fillables[gen.offsets])
            forefront = len(fillables[gen.tags])
            fillables_leaf_to_root.append(fillables[gen.tags])
            fillables_leaf_to_root.append(fillables[gen.offsets])

        elif isinstance(gen, oamap.generator.RecordGenerator):
            uniques = set(initialize(x) for x in gen.fields.values())
            assert len(uniques) == 1
            forefront = list(uniques)[0]

        elif isinstance(gen, oamap.generator.TupleGenerator):
            uniques = set(initialize(x) for x in gen.types)
            assert len(uniques) == 1
            forefront = list(uniques)[0]

        elif isinstance(gen, oamap.generator.PointerGenerator):
            if gen._internal and gen.target is generator and len(fillables[gen.positions]) != 0:
                raise TypeError("the root of a Schema may be the target of a Pointer, but if so, it can only be filled from data once")

            if gen not in pointers:
                pointers.append(gen)
            pointerobjs_keys.append(id(gen))
            targetids_keys.append(id(gen.target))

            if not gen._internal:
                initialize(gen.target)
            fillables[gen.positions].revert()
            forefront = len(fillables[gen.positions])
            fillables_leaf_to_root.append(fillables[gen.positions])

        elif isinstance(gen, oamap.generator.ExtendedGenerator):
            forefront = initialize(gen.generic)

        else:
            raise TypeError("unrecognized generator: {0}".format(repr(gen)))

        if isinstance(gen, oamap.generator.Masked):
            fillables[gen.mask].revert()
            # mask forefront overrides any other arrays
            forefront = len(fillables[gen.mask])
            fillables_leaf_to_root.append(fillables[gen.mask])

        return forefront

    # do the initialize
    initialize(generator)

    # how to get the forefront of various objects (used in 'fill')
    def forefront(gen, secondary=False):
        if not secondary and isinstance(gen, oamap.generator.Masked):
            # mask forefront overrides any other arrays
            return fillables[gen.mask].forefront()

        elif isinstance(gen, oamap.generator.PrimitiveGenerator):
            return fillables[gen.data].forefront()

        elif isinstance(gen, oamap.generator.ListGenerator):
            return fillables[gen.stops].forefront()

        elif isinstance(gen, oamap.generator.UnionGenerator):
            return fillables[gen.tags].forefront()

        elif isinstance(gen, oamap.generator.RecordGenerator):
            for x in gen.fields.values():
                return forefront(x)

        elif isinstance(gen, oamap.generator.TupleGenerator):
            for x in gen.types:
                return forefront(x)

        elif isinstance(gen, oamap.generator.PointerGenerator):
            return len(pointerobjs[id(gen)])

        elif isinstance(gen, oamap.generator.ExtendedGenerator):
            return forefront(gen.generic)

    if forefront(generator) != 0 and not isinstance(generator, oamap.generator.ListGenerator):
        raise TypeError("non-Lists can only be filled from data once")

    def unionnullable(union):
        for possibility in union.possibilities:
            if isinstance(possibility, oamap.generator.Masked):
                return True
            elif isinstance(possibility, oamap.generator.UnionGenerator):
                return unionnullable(possibility)
        return False

    # the fill function (recursive)
    pointerat = {}
    def fill(obj, gen, targetids, pointerobjs, at):
        if id(gen) in targetids:
            targetids[id(gen)][id(obj)] = (forefront(gen), obj)

        if obj is None:
            if isinstance(gen, oamap.generator.Masked):
                fillables[gen.mask].append(gen.maskedvalue)
                return   # only mask is filled
            elif isinstance(gen, oamap.generator.UnionGenerator) and unionnullable(gen):
                pass     # mask to fill is in a Union possibility
            elif isinstance(gen, oamap.generator.ExtendedGenerator) and isinstance(gen.generic, oamap.generator.Masked):
                fill(obj, gen.generic, targetids, pointerobjs, at)
                return   # filled the generic generator's mask
            else:
                raise TypeError("cannot fill None where expecting type {0} at {1}".format(gen.schema, at))

        # obj is not None (except for the Union case)
        if isinstance(gen, oamap.generator.Masked):
            fillables[gen.mask].append(forefront(gen, secondary=True))

        if isinstance(gen, oamap.generator.PrimitiveGenerator):
            fillables[gen.data].append(obj)

        elif isinstance(gen, oamap.generator.ListGenerator):
            start = stop = forefront(gen.content)
            try:
                if isinstance(obj, dict) or (isinstance(obj, tuple) and hasattr(obj, "_fields")):
                    raise TypeError
                iter(obj)
            except TypeError:
                raise TypeError("cannot fill {0} where expecting type {1} at {2}".format(repr(obj), gen.schema, at))
            else:
                for x in obj:
                    fill(x, gen.content, targetids, pointerobjs, at + (stop - start,))
                    stop += 1

            fillables[gen.starts].append(start)
            fillables[gen.stops].append(stop)

        elif isinstance(gen, oamap.generator.UnionGenerator):
            tag = None
            for i, possibility in enumerate(gen.possibilities):
                if obj in possibility.schema:
                    tag = i
                    break
            if tag is None:
                raise TypeError("cannot fill {0} where expecting type {1} at {2}".format(repr(obj), gen.schema, at))

            offset = forefront(possibility)
            fill(obj, possibility, targetids, pointerobjs, at + ("tag" + repr(tag),))

            fillables[gen.tags].append(tag)
            fillables[gen.offsets].append(offset)

        elif isinstance(gen, oamap.generator.RecordGenerator):
            if isinstance(obj, dict):
                for n, x in gen.fields.items():
                    if n not in obj:
                        raise TypeError("cannot fill {0} because its {1} field is missing at {2}".format(repr(obj), repr(n), at))
                    fill(obj[n], x, targetids, pointerobjs, at + (n,))
            else:
                for n, x in gen.fields.items():
                    if not hasattr(obj, n):
                        raise TypeError("cannot fill {0} because its {1} field is missing at {2}".format(repr(obj), repr(n), at))
                    fill(getattr(obj, n), x, targetids, pointerobjs, at + (n,))

        elif isinstance(gen, oamap.generator.TupleGenerator):
            for i, x in enumerate(gen.types):
                try:
                    v = obj[i]
                except (TypeError, IndexError):
                    raise TypeError("cannot fill {0} because it does not have a field {1} at {2}".format(repr(obj), i, at))
                else:
                    fill(v, x, targetids, pointerobjs, at + (i,))

        elif isinstance(gen, oamap.generator.PointerGenerator):
            # Pointers will be set after we see all the target values
            pointerobjs[id(gen)].append(obj)
            if id(gen) not in pointerat:
                pointerat[id(gen)] = at

        elif isinstance(gen, oamap.generator.ExtendedGenerator):
            fill(gen.degenerate(obj), gen.generic, targetids, pointerobjs, at)

    # attempt to fill (fillables won't update their 'len' until we 'update')
    targetids = dict((x, {}) for x in targetids_keys)
    pointerobjs = dict((x, []) for x in pointerobjs_keys)
    fill(value, generator, targetids, pointerobjs, ())

    # do the pointers after everything else
    for pointer in pointers:
        while len(pointerobjs[id(pointer)]) > 0:
            pointerobjs2 = {id(pointer): []}
            for obj in pointerobjs[id(pointer)]:
                if id(obj) in targetids[id(pointer.target)] and targetids[id(pointer.target)][id(obj)][1] == obj:
                    # case 1: an object in the target *is* the object in the pointer (same ids)
                    position, _ = targetids[id(pointer.target)][id(obj)]

                else:
                    position = None
                    if pointer_fromequal:
                        # fallback to quadratic complexity search
                        for key, (pos, obj2) in targetids[id(pointer.target)].items():
                            if obj == obj2:
                                position = pos
                                break

                    if position is not None:
                        # case 2: an object in the target *is equal to* the object in the pointer (only check if pointer_fromequal)
                        pass

                    else:
                        # case 3: the object was not found; it must be added to the target (beyond indexes where it can be found)
                        fill(obj, pointer.target, targetids, pointerobjs2, pointerat[id(pointer)])
                        position, _ = targetids[id(pointer.target)][id(obj)]

                # every obj in pointerobjs[id(pointer)] gets *one* append
                fillables[pointer.positions].append(position)

            pointerobjs[id(pointer)] = pointerobjs2[id(pointer)]

    # success! (we're still here)
    for fillable in fillables_leaf_to_root:
        fillable.update()

    # return fillables, which can be evaluated to become arrays
    return fillables

################################################################ helper functions for JSON-derived data and iterables

def fromjson(value, generator=None, fillables=None, pointer_fromequal=False):
    return fromdata(oamap.inference.jsonconventions(value), generator=generator, fillables=fillables, pointer_fromequal=pointer_fromequal)

def fromjsonfile(value, generator=None, fillables=None, pointer_fromequal=False):
    return fromdata(oamap.inference.jsonconventions(json.load(value)), generator=generator, fillables=fillables, pointer_fromequal=pointer_fromequal)

def fromjsonstring(value, generator=None, fillables=None, pointer_fromequal=False):
    return fromdata(oamap.inference.jsonconventions(json.loads(value)), generator=generator, fillables=fillables, pointer_fromequal=pointer_fromequal)

def fromjsonfilestream(values, generator=None, fillables=None, pointer_fromequal=False):
    def iterator():
        j = json.JSONDecoder()
        buf = ""
        while True:
            try:
                obj, i = j.raw_decode(buf)
            except ValueError:
                extra = values.read(8192)
                if len(extra) == 0:
                    break
                else:
                    buf = buf.lstrip() + extra
            else:
                yield oamap.inference.jsonconventions(obj)
                buf = buf[i:].lstrip()

    return fromiterdata(iterator(), generator=generator, fillables=fillables, pointer_fromequal=pointer_fromequal)

def fromjsonstream(values, generator=None, fillables=None, pointer_fromequal=False):
    def iterator():
        j = json.JSONDecoder()
        index = 0
        while True:
            try:
                obj, i = j.raw_decode(values[index:])
            except ValueError:
                break
            yield oamap.inference.jsonconventions(obj)
            _, index = fromjsonstream._pattern.match(values, index + i).span()

    return fromiterdata(iterator(), generator=generator, fillables=fillables, pointer_fromequal=pointer_fromequal)

fromjsonstream._pattern = re.compile("\s*")
