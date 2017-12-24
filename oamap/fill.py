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

    gens = []
    def sync(gen):
        if isinstance(gen, oamap.generator.PrimitiveGenerator):
            fillables[gen.data].revert()
            forefront = len(fillables[gen.data])

        elif isinstance(gen, oamap.generator.ListGenerator):
            sync(gen.content)
            fillables[gen.starts].revert()
            fillables[gen.stops].revert()
            assert len(fillables[gen.starts]) == len(fillables[gen.stops])
            forefront = len(fillables[gen.stops])

        elif isinstance(gen, oamap.generator.UnionGenerator):
            for x in gen.possibilities:
                sync(x)
            fillables[gen.tags].revert()
            fillables[gen.offsets].revert()
            assert len(fillables[gen.tags]) == len(fillables[gen.offsets])
            forefront = len(fillables[gen.tags])

        elif isinstance(gen, oamap.generator.RecordGenerator):
            uniques = set(sync(x) for x in gen.fields.values())
            assert len(uniques) == 1
            forefront = list(uniques)[0]

        elif isinstance(gen, oamap.generator.TupleGenerator):
            uniques = set(sync(x) for x in gen.types)
            assert len(uniques) == 1
            forefront = list(uniques)[0]

        elif isinstance(gen, oamap.generator.PointerGenerator):
            if not gen._internal:
                sync(gen.target)
            fillables[gen.positions].revert()
            forefront = len(fillables[gen.positions])

        else:
            raise TypeError("unrecognized generator: {0}".format(repr(gen)))

        if isinstance(gen, Masked):
            fillables[gen.mask].revert()
            assert forefront == len(fillables[gen.mask])

        gens.append(gen)
        return forefront

    sync(generator)

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

    def fill(obj, gen):
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
            raise NotImplementedError
        
        if isinstance(gen, oamap.generator.Masked):
            if obj is None:
                fillables[gen.mask].append(True)
            else:
                fillables[gen.mask].append(False)

    if forefront(generator) != 0 and not isinstance(generator, ListGenerator):
        raise TypeError("only call oamap.fill.fromdata multiple times on objects with List schema (to append to the List)")

    # attempt to fill (fillables won't update their 'len' until we 'update')
    fill(value, generator)

    # success! (we're still here)
    for gen in gens:
        gen.update()  # updates from innermost outward, so even an exception here would leave it in a good state

    # return fillables, which can be evaluated to become arrays
    return fillables
