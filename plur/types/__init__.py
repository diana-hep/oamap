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

from plur.types.type import Type

from plur.types.primitive import Primitive # P
from plur.types.list import List           # L
from plur.types.union import Union         # U
from plur.types.record import Record       # R

# logical primitives
from plur.types.primitive import boolean

# signed integer primitives
from plur.types.primitive import int8
from plur.types.primitive import int16
from plur.types.primitive import int32
from plur.types.primitive import int64

# unsigned integer primitives
from plur.types.primitive import uint8
from plur.types.primitive import uint16
from plur.types.primitive import uint32
from plur.types.primitive import uint64

# floating point primitives
from plur.types.primitive import float32
from plur.types.primitive import float64
from plur.types.primitive import float128

# complex primitives (real float followed by imaginary float)
from plur.types.primitive import complex64
from plur.types.primitive import complex128
from plur.types.primitive import complex256
