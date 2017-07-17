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

class Option(Type):
    def __init__(self, of):
        def flatten(x):
            while isinstance(x, Option):
                x = x.of
            return x
        self.of = flatten(of)
        super(Option, self).__init__()

    @property
    def args(self):
        return (self.of,)

    def __contains__(self, element):
        return element is None or element in self.of

    def issubtype(self, supertype):
        return isinstance(supertype, Option) and self.rtname == supertype.rtname \
               and self.of.issubtype(supertype.of)        # options are covariant

    def toJson(self):
        return {"option": self.of.toJson()}
