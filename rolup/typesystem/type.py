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

import json

from rolup.util import *

class Type(object):
    runtimes = {}

    @staticmethod
    def register(rtname, cls):
        if rtname in Type.runtimes and Type.runtimes[rtname] != cls:
            raise TypeDefinitionError("multiple types attempting to register runtime name \"{0}\"".format(rtname))
        else:
            Type.runtimes[rtname] = cls

    @staticmethod
    def withrt(tpe, rtname, *rtargs):
        if rtname in Type.runtimes:
            return Type.runtimes[rtname].fromtype(tpe, *rtargs)
        else:
            return tpe

    def materialize(self, iterator):
        raise NotImplementedError

    @property
    def rtname(self):
        return None

    @property
    def rtargs(self):
        return None
    
    @property
    def args(self):
        return ()

    @property
    def kwds(self):
        return {}
        
    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.rtname == other.rtname and self.args == other.args and self.kwds == other.kwds

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        if isinstance(other, Type):
            selfrtname = "" if self.rtname is None else self.rtname
            otherrtname = "" if other.rtname is None else other.rtname
            if selfrtname == otherrtname:
                if isinstance(other, self.__class__):
                    selfargs = self.args + tuple(sorted(self.kwds.items()))
                    otherargs = other.args + tuple(sorted(other.kwds.items()))
                    return selfargs < otherargs
                else:
                    return self.__class__.__name__ < other.__class__.__name__
            else:
                return selfrtname < otherrtname
        else:
            return False

    def __hash__(self):
        return hash((self.__class__, self.rtname, self.args, tuple(sorted(self.kwds.items()))))

    def __contains__(self, element):
        return False

    def issubtype(self, supertype):
        from rolup.typesystem.union import Union
        if isinstance(supertype, Union):
            # supertype is a Union; we must fit into any of its possibilities
            return any(self.issubtype(x) for x in supertype.of)
        else:
            return False

    def __repr__(self):
        args = [repr(v) for v in self.args]
        kwds = [n + " = " + repr(v) for n, v in sorted(self.kwds)]
        return "{0}({1})".format(self.__class__.__name__, ", ".join(args + kwds))

    def toJsonString(self):
        return json.dumps(self.toJson())

    def toJson(self):
        raise NotImplementedError

    @staticmethod
    def fromJsonString(string):
        return Type.fromJson(json.loads(string))

    @staticmethod
    def fromJson(obj):
        import numpy
        from rolup.typesystem.record import Record       # R
        from rolup.typesystem.option import Option       # O
        from rolup.typesystem.list import List           # L
        from rolup.typesystem.union import Union         # U
        from rolup.typesystem.primitive import Primitive # P
        from rolup.typesystem.primitive import withrepr

        if isinstance(obj, dict):
            if "record" in obj:
                objrecord = obj["record"]
                if isinstance(objrecord, dict):
                    objrecord = [objrecord]
                assert isinstance(objrecord, list)

                fields = []
                for x in objrecord:
                    for fn, ft in x.items():
                        fields.append((fn, Type.fromJson(ft)))

                tpe = Record.fromfields(fields)

            elif "option" in obj:
                tpe = Option(Type.fromJson(obj["option"]))

            elif "list" in obj:
                tpe = List(Type.fromJson(obj["list"]))

            elif "union" in obj:
                assert isinstance(obj["union"], list)
                tpe = Union(*[Type.fromJson(x) for x in obj["union"]])

            elif "primitive" in obj:
                tpe = withrepr(Primitive(numpy.dtype(obj["primitive"])))

            else:
                raise TypeDefinitionError("unrecognized type in JSON: {0}".format(obj))

            return Type.withrt(tpe, obj.get("rtname"), *obj.get("rtargs", []))

        else:
            return withrepr(Primitive(numpy.dtype(obj)))
