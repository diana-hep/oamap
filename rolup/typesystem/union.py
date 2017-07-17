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

from rolup.util import *
from rolup.typesystem.type import Type

class Union(Type):
    def __init__(self, *of):
        def flatten(x):
            while isinstance(x, Union):
                x = x.of
            return x
        self.of = tuple(map(flatten, of))
        super(Union, self).__init__()

    @property
    def args(self):
        return self.of

    def __contains__(self, element):
        return any(element in x for x in self.of)

    def issubtype(self, supertype):
        if isinstance(supertype, Union) and self.rtname == supertype.rtname:
            # everything that supertype can be must also be allowed for self
            for supert in supertype.of:
                if not any(selft.issubtype(supert) for selft in self.of):
                    return False
            return True

        else:
            # supertype is not a Union; some unioned primitives might be contained within a primitive
            if not any(selft.issubtype(supertype) for selft in self.of):
                return False
            return True

    def toJson(self):
        return {"union": [x.toJson() for x in self.of]}
