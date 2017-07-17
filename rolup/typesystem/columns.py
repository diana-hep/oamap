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

import numpy

from rolup.typesystem.record import Record       # R
from rolup.typesystem.option import Option       # O
from rolup.typesystem.list import List           # L
from rolup.typesystem.union import Union         # U
from rolup.typesystem.primitive import Primitive # P
from rolup.typesystem.primitive import withrepr
from rolup.typesystem.arrayname import ArrayName

def type2columns(tpe, prefix, delimiter="-", indextype=numpy.dtype(numpy.uint64)):
    def recurse(tpe, name):
        if tpe.rtname is not None:
            raise NotImplementedError

        if isinstance(tpe, Record):
            raise NotImplementedError            



        elif isinstance(tpe, Option):
            raise NotImplementedError



        elif isinstance(tpe, List):
            return [(str(name.toListSize()), indextype)] + recurse(tpe.of, name.toListData())



        elif isinstance(tpe, Union):
            raise NotImplementedError



        elif isinstance(tpe, Primitive):
            return [(str(name), tpe.of)]
            
        else:
            assert False, "unexpected type object: {0}".format(tpe)

    return dict(recurse(tpe, ArrayName(prefix, (), delimiter=delimiter)))

def columns2type(cols):
    return None

