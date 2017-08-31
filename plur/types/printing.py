#!/usr/bin/env python

# Copyright 2017 DIANA-HEP
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from plur.types import *
from plur.types.primitive import PrimitiveWithRepr

def __recurse(tpe, depth, comma, help):
    # P
    if tpe.__class__ == Primitive or tpe.__class__ == PrimitiveWithRepr:
        return [(depth, repr(tpe) + comma, tpe)]

    # L
    elif tpe.__class__ == List:
        return [(depth, "List(", tpe)] + __recurse(tpe.of, depth + 1, "", help) + [(depth + 1, ")" + comma, tpe)]

    # U
    elif tpe.__class__ == Union:
        inner = []
        for i, t in enumerate(tpe.of):
            sub = __recurse(t, depth + 1, "," if i < len(tpe.of) - 1 else "", help)
            inner.extend(sub)
        return [(depth, "Union(", tpe)] + inner + [(depth + 1, ")" + comma, tpe)]

    # R
    elif tpe.__class__ == Record:
        content = []
        widest = 0
        for i, (n, t) in enumerate(tpe.of):
            sub = __recurse(t, depth + 1, "," if i < len(tpe.of) - 1 else "", help)
            first, rest = sub[0], sub[1:]
            fdepth, ftxt, ftpe = first
            if Record._checkPositional.match(n) is None:   # NOT positional, a named field
                ftxt = n + " = " + ftxt

            content.append((fdepth, ftxt, ftpe, rest))
            widest = max(widest, len(ftxt))

        inner = []
        for c, (i, (n, t)) in zip(content, enumerate(tpe.of)):
            fdepth, ftxt, ftpe, rest = c

            if help:
                h = getattr(t, "help", "")
                if h != "":
                    spaces = widest + 1 - len(ftxt)
                    ftxt = ftxt + " " * spaces + "# " + h

            inner.extend([(fdepth, ftxt, ftpe)] + rest)

        return [(depth, "Record(", tpe)] + inner + [(depth + 1, ")" + comma, tpe)]

    # runtime types
    else:
        return [(depth, repr(tpe), tpe)]

def formattype(tpe, highlight=lambda t: "", indent="  ", prefix="", help=True):
    return "\n".join("{0}{1}{2}{3}".format(prefix, highlight(t), indent * depth, line)
                     for depth, line, t in __recurse(tpe, 0, "", help))

def formatdiff(one, two, header=None, between=lambda t1, t2: " " if t1 == t2 or t1 is None or t2 is None else ">", indent="  ", prefix="", width=None):
    one = __recurse(one, 0, "", False)
    two = __recurse(two, 0, "", False)
    i1 = 0
    i2 = 0
    if width is None:
        width = max(max([len(indent)*depth + len(line) for depth, line, _ in one]), max([len(indent)*depth + len(line) for depth, line, _ in two]))
        if header is not None:
            width = max([width, len(header[0]), len(header[1])])

    if header is not None:
        left, right = header   # assuming header is a 2-tuple of strings
        out = [(prefix + "{0:%d} {1:%d} {2:%d}" % (width, len(between(None, None)), width)).format(left[:width], "|", right[:width]),
               (prefix + "-" * width) + "-+-" + ("-" * width)]
    else:
        out = []

    while i1 < len(one) or i2 < len(two):
        d1, line1, t1 = one[i1] if i1 < len(one) else (d1, "", None)
        d2, line2, t2 = two[i2] if i2 < len(two) else (d2, "", None)

        if d1 >= d2:
            line1 = indent * d1 + line1
            line1 = ("{0:%d}" % width).format(line1[:width])
        if d2 >= d1:
            line2 = indent * d2 + line2
            line2 = ("{0:%d}" % width).format(line2[:width])
        
        if d1 == d2:
            out.append(prefix + line1 + " " + between(t1, t2) + " " + line2)
            i1 += 1
            i2 += 1
        elif d1 > d2:
            out.append(prefix + line1 + " " + between(t1, None) + " " + (" " * width))
            i1 += 1
        elif d2 > d1:
            out.append(prefix + (" " * width) + " " + between(None, t2) + " " + line2)
            i2 += 1

    return "\n".join(out)
