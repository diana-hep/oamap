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

try:
    from collections import OrderedDict
except ImportError:
    # simple OrderedDict implementation for Python 2.6
    class OrderedDict(dict):
        def __init__(self, items=(), **kwds):
            items = list(items)
            self._order = [k for k, v in items] + [k for k, v in kwds.items()]
            super(OrderedDict, self).__init__(items)
        def keys(self):
            return self._order
        def values(self):
            return [self[k] for k in self._order]
        def items(self):
            return [(k, self[k]) for k in self._order]
        def __setitem__(self, name, value):
            if name not in self._order:
                self._order.append(name)
            super(OrderedDict, self).__setitem__(name, value)
        def __delitem__(self, name):
            if name in self._order:
                self._order.remove(name)
            super(OrderedDict, self).__delitem__(name)
        def __repr__(self):
            return "OrderedDict([{0}])".format(", ".join("({0}, {1})".format(repr(k), repr(v)) for k, v in self.items()))

try:
    from UserDict import DictMixin as MutableMapping
except ImportError:
    from collections import MutableMapping

try:
    from importlib import import_module
except ImportError:
    def import_module(modulename):
        module = __import__(modulename)
        for name in modulename.split(".")[1:]:
            module = module.__dict__[name]
        return module

def slice2sss(index, length):
    step = 1 if index.step is None else index.step

    if step == 0:
        raise ValueError("slice step cannot be zero")

    elif step > 0:
        if index.start is None:
            start = 0                                         # in-range
        elif index.start >= 0:
            start = min(index.start, length)                  # in-range or length
        else:
            start = max(0, index.start + length)              # in-range

        if index.stop is None:
            stop = length                                     # length
        elif index.stop >= 0:
            stop = max(start, min(length, index.stop))        # in-range or length
        else:
            stop = max(start, index.stop + length)            # in-range or length

    else:
        if index.start is None:
            start = length - 1                                # in-range
        elif index.start >= 0:
            start = min(index.start, length - 1)              # in-range
        else:
            start = max(index.start + length, -1)             # in-range or -1

        if index.stop is None:
            stop = -1                                         # -1
        elif index.stop >= 0:
            stop = min(start, index.stop)                     # in-range or -1
        else:
            stop = min(start, max(-1, index.stop + length))   # in-range or -1

    return start, stop, step
