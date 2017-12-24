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

def fromdata(value, generator=None, fillables=None, pointer_equality_search=True):
    if generator is None:
        generator = oamap.inference.fromdata(value).generator()

    if not isinstance(generator, oamap.generator.Generator):
        generator = generator.generator()

    if fillables is None:
        fillables = oamap.fillcolumn.fillablearrays(generator)

    # get a list of generators (innermost outward) and make sure they're all starting at the last good entry
    gens = []
    pointerobjs = {}
    targetids = {}
    def initialize(gen):
        if isinstance(gen, oamap.generator.PrimitiveGenerator):
            fillables[gen.data].revert()
            forefront = len(fillables[gen.data])

        elif isinstance(gen, oamap.generator.ListGenerator):
            initialize(gen.content)
            fillables[gen.starts].revert()
            fillables[gen.stops].revert()
            assert len(fillables[gen.starts]) == len(fillables[gen.stops])
            forefront = len(fillables[gen.stops])

        elif isinstance(gen, oamap.generator.UnionGenerator):
            for x in gen.possibilities:
                initialize(x)
            fillables[gen.tags].revert()
            fillables[gen.offsets].revert()
            assert len(fillables[gen.tags]) == len(fillables[gen.offsets])
            forefront = len(fillables[gen.tags])

        elif isinstance(gen, oamap.generator.RecordGenerator):
            uniques = set(initialize(x) for x in gen.fields.values())
            assert len(uniques) == 1
            forefront = list(uniques)[0]

        elif isinstance(gen, oamap.generator.TupleGenerator):
            uniques = set(initialize(x) for x in gen.types)
            assert len(uniques) == 1
            forefront = list(uniques)[0]

        elif isinstance(gen, oamap.generator.PointerGenerator):
            if gen._internal and gen.target is generator and len(generator) != 0:
                raise TypeError("the root of a Schema may be the target of a Pointer, but if so, it can only be filled from data once")

            pointerobjs[id(gen)] = []
            targetids[id(gen.target)] = {}

            if not gen._internal:
                initialize(gen.target)
            fillables[gen.positions].revert()
            forefront = len(fillables[gen.positions])

        else:
            raise TypeError("unrecognized generator: {0}".format(repr(gen)))

        if isinstance(gen, Masked):
            fillables[gen.mask].revert()
            assert forefront == len(fillables[gen.mask])

        gens.append(gen)
        return forefront

    # do the initialize
    initialize(generator)

    # how to get the forefront of various objects (used in 'fill')
    def forefront(gen):
        if isinstance(gen, oamap.generator.Masked):
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
            return fillables[gen.positions].forefront()

    if forefront(generator) != 0 and not isinstance(generator, ListGenerator):
        raise TypeError("non-Lists can only be filled from data once")

    # the fill function (recursive)
    def fill(obj, gen):
        if id(gen) in targetids:
            targetids[id(gen)][id(obj)] = (forefront(gen), obj)

        if isinstance(gen, oamap.generator.PrimitiveGenerator):
            fillables[gen.data].append(0 if obj is None else obj)

        elif isinstance(gen, oamap.generator.ListGenerator):
            if obj is None:
                start = stop = -1
            else:
                start = stop = forefront(gen.content)
                try:
                    if isinstance(obj, dict) or (isinstance(obj, tuple) and hasattr(obj, "_fields")):
                        raise TypeError
                    iter(obj)
                except TypeError:
                    raise TypeError("cannot fill {0} where expecting type {1}".format(repr(obj), gen.schema))
                else:
                    for x in obj:
                        fill(x, gen.content)
                        stop += 1

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
                
                offset = forefront(possibility)
                fill(obj, possibility)

            fillables[gen.tags].append(tag)
            fillables[gen.offsets].append(offset)

        elif isinstance(gen, oamap.generator.RecordGenerator):
            if obj is None:
                pass
            elif isinstance(obj, dict):
                for n, x in gen.fields.items():
                    if n not in obj:
                        raise TypeError("cannot fill {0} because its {1} field is missing".format(repr(obj), repr(n)))
                    fill(obj[n], x)
            else:
                for n, x in gen.fields.items():
                    if not hasattr(obj, n):
                        raise TypeError("cannot fill {0} because its {1} field is missing".format(repr(obj), repr(n)))
                    fill(getattr(obj, n), x)

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
                        fill(v, x)

        elif isinstance(gen, oamap.generator.PointerGenerator):
            # Pointers will be set after we see all the target values
            pointerobjs[id(gen)].append(obj)
        
        if isinstance(gen, oamap.generator.Masked):
            if obj is None:
                fillables[gen.mask].append(True)
            else:
                fillables[gen.mask].append(False)

    # attempt to fill (fillables won't update their 'len' until we 'update')
    fill(value, generator)

    # do the pointers after everything else
    for gen in gens:
        if isinstance(gen, oamap.generator.PointerGenerator):
            for obj in pointerobjs[id(gen)]:
                if id(obj) in targetids[id(gen.target)] and targetids[id(gen.target)][id(obj)] == obj:
                    # case 1: an object in the target *is* the object in the pointer (same ids)
                    position, _ = targetids[id(gen.target)][id(obj)]
                    del targetids[id(gen.target)][id(obj)]

                else:
                    position = None
                    if pointer_equality_search:
                        # fallback to quadratic complexity search
                        for key, (pos, obj2) in targetids[id(gen.target)].items():
                            if obj == obj2:
                                position = pos
                                break

                    if position is not None:
                        # case 2: an object in the target *is equal to* the object in the pointer
                        del targetids[id(gen.target)][key]

                    else:
                        # case 3: the object was not found; it must be added to the target (beyond indexes where it can be found)
                        fill(obj, gen.target)
                        position, _ = targetids[id(gen.target)][id(obj)]
                        del targetids[id(gen.target)][id(obj)]

                # every obj in pointerobjs[id(gen)] gets *one* append
                fillables[gen.positions].append(position)

    # success! (we're still here)
    for gen in gens:
        gen.update()  # updates from innermost outward, so even an exception here would leave it in a good state

    # return fillables, which can be evaluated to become arrays
    return fillables
