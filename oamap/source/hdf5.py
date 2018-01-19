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
    import h5py
except ImportError:
    pass
else:
    def oamap(group):
        return OAMapGroup(group)

    h5py._hl.group.Group.oamap = property(oamap)

    class OAMapGroup(h5py._hl.group.Group):
        def __init__(self, group):
            self._group = group

        def __repr__(self):
            return "<OAMap HDF5 group \"{0}\" ({1} members)>".format(self.name, len(self))

        def __str__(self):
            return __repr__(self)

        def __contains__(self, name):
            raise NotImplementedError

        def __len__(self):
            raise NotImplementedError

        def __getitem__(self, name):
            raise NotImplementedError

        def __setitem__(self, name, value):
            raise NotImplementedError

        def __delitem__(self, name):
            raise NotImplementedError

        def keys(self):
            raise NotImplementedError

        def values(self):
            return (self[n] for n in self.keys())

        def items(self):
            return ((n, self[n]) for n in self.keys())

        def __iter__(self):
            return self.keys()

        def __dict__(self):
            return dict(self.items())

        def setdefault(self, key, default=None):
            if key not in self:
                self[key] = default
            return self[key]

        def pop(self, **args):
            return self.popitem(**args)[1]

        def popitem(self, **args):
            if len(args) == 0:
                if len(self) > 0:
                    key, = self.keys()
                else:
                    raise IndexError("pop from empty OAMapGroup")
            elif len(args) == 1:
                key, = args
            elif len(args) == 2:
                key, default = args
            else:
                raise TypeError("popitem expected at most 2 arguments, got {0}".format(len(args)))

            if key in self:
                out = (key, self[key])
                del self[key]
                return out
            elif len(args) == 2:
                return default
            else:
                raise KeyError(repr(key))

        def update(self, other):
            for n, x in other.items():
                self[n] = x

        def __eq__(self, other):
            if isinstance(other, OAMapGroup):
                return self._group.__eq__(other._group)
            else:
                return self._group.__eq__(other)

        def __ne__(self, other):
            if isinstance(other, OAMapGroup):
                return self._group.__ne__(other._group)
            else:
                return self._group.__ne__(other)

        def __lt__(self, other):
            if isinstance(other, OAMapGroup):
                return self._group.__lt__(other._group)
            else:
                return self._group.__lt__(other)

        def __gt__(self, other):
            if isinstance(other, OAMapGroup):
                return self._group.__gt__(other._group)
            else:
                return self._group.__gt__(other)

        def __le__(self, other):
            if isinstance(other, OAMapGroup):
                return self._group.__le__(other._group)
            else:
                return self._group.__le__(other)

        def __ge__(self, other):
            if isinstance(other, OAMapGroup):
                return self._group.__ge__(other._group)
            else:
                return self._group.__ge__(other)

        # pass-through

        def __bool__(self, *args, **kwds):
            return self._group.__bool__(*args, **kwds)

        def __delattr__(self, *args, **kwds):
            return self._group.__delattr__(*args, **kwds)

        def __dir__(self, *args, **kwds):
            return self._group.__dir__(*args, **kwds)

        def __format__(self, *args, **kwds):
            return self._group.__format__(*args, **kwds)

        def __hash__(self, *args, **kwds):
            return self._group.__hash__(*args, **kwds)

        def __nonzero__(self, *args, **kwds):
            return self._group.__nonzero__(*args, **kwds)

        def __reduce__(self, *args, **kwds):
            return self._group.__reduce__(*args, **kwds)

        def __reduce_ex__(self, *args, **kwds):
            return self._group.__reduce_ex__(*args, **kwds)

        def __setattr__(self, *args, **kwds):
            return self._group.__setattr__(*args, **kwds)

        def __sizeof__(self, *args, **kwds):
            return self._group.__sizeof__(*args, **kwds)

        def _d(self, *args, **kwds):
            return self._group._d(*args, **kwds)

        def _e(self, *args, **kwds):
            return self._group._e(*args, **kwds)

        @property
        def _id(self):
            return self._group._id

        @property
        def _lapl(self):
            return self._group._lapl

        @property
        def _lcpl(self):
            return self._group._lcpl

        @property
        def attrs(self):
            return self._group.attrs

        def clear(self, *args, **kwds):
            return self._group.clear(*args, **kwds)

        def copy(self, *args, **kwds):
            return self._group.copy(*args, **kwds)

        def create_dataset(self, *args, **kwds):
            return self._group.create_dataset(*args, **kwds)

        def create_group(self, *args, **kwds):
            return self._group.create_group(*args, **kwds)

        @property
        def file(self):
            return self._group.filea

        def get(self, *args, **kwds):
            return self._group.get(*args, **kwds)

        @property
        def id(self):
            return self._group.id

        def move(self, *args, **kwds):
            return self._group.move(*args, **kwds)

        @property
        def name(self):
            return self._group.name

        @property
        def parent(self):
            return self._group.parent

        @property
        def ref(self):
            return self._group.ref

        @property
        def regionref(self):
            return self._group.regionref

        def require_dataset(self, *args, **kwds):
            return self._group.require_dataset(*args, **kwds)

        def require_group(self, *args, **kwds):
            return self._group.require_group(*args, **kwds)

        def visit(self, *args, **kwds):
            return self._group.visit(*args, **kwds)

        def visititems(self, *args, **kwds):
            return self._group.visititems(*args, **kwds)
