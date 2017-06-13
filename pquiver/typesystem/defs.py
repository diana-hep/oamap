import re

from pquiver.typesystem import naming

class TypeDefinitionError(Exception): pass

class Type(object):
    runtimes = {}

    @staticmethod
    def register(rtname, cls):
        if rtname in Type.runtimes and Type.runtimes[rtname] != cls:
            raise TypeDefinitionError("multiple types attempting to register runtime name \"{0}\"".format(rtname))
        Type.runtimes[rtname] = cls

    @staticmethod
    def materialize(rtname, iterator):
        if rtname not in Type.runtimes:
            raise RuntimeError("runtime name \"{0}\" is not recognized (not registered?)".format(rtname))
        Type.runtimes[rtname].materialize(iterator)

    @property
    def generic(self):
        return self.__class__.__name__

    @property
    def args(self):
        return ()

    @property
    def kwds(self):
        return {}

    @property
    def children(self):
        return ()

    @property
    def optional(self):
        return False

    @property
    def rtname(self):
        return None

    def __repr__(self):
        return self.generic + "(" + ", ".join([repr(v) for v in self.args] + [n + " = " + repr(v) for n, v in sorted(self.kwds)]) + ")"

    def __eq__(self, other):
        return self.generic == other.generic and self.args == other.args

    def __ne__(self, other):
        return not self.__eq__(self, other)

    def __lt__(self, other):
        if isinstance(other, Type):
            if self.generic == other.generic:
                return self.args < other.args
            else:
                return self.generic < other.generic
        else:
            return False

    def __hash__(self):
        return hash((self.generic, self.args))

    def __contains__(self, element):
        raise NotImplementedError

    def issubtype(self, supertype):
        raise NotImplementedError

class Optional(Type):
    def __init__(self, type):
        while isinstance(type, Optional):
            type = type._type
        self._type = type

    @property
    def type(self):
        return self._type

    @property
    def args(self):
        return (self._type,)

    @property
    def children(self):
        return (self._type,)

    @property
    def optional(self):
        return True

    def __contains__(self, element):
        return element is None or element in self._type

    def issubtype(self, supertype):
        return supertype.generic == "Optional" and self._type.issubtype(supertype._type)

class Primitive(Type):
    def __init__(self, dtype):
        self._dtype = dtype
        super(Primitive, self).__init__()

    @property
    def dtype(self):
        return self._dtype

    @property
    def args(self):
        return (self._dtype,)

    def __contains__(self, element):
        if isinstance(element, complex):
            return self._dtype.kind == "c"

        elif isinstance(element, float):
            return self._dtype.kind == "c" or self._dtype.kind == "f"

        elif isinstance(element, int):
            if self._dtype.kind == "c" or self._dtype.kind == "f":
                return True

            elif self._dtype.kind == "i":
                bits = self._dtype.itemsize * 8 - 1
                return -2**bits <= element < 2**bits

            elif self._dtype.kind == "u":
                bits = self._dtype.itemsize * 8
                return 0 <= element < 2**bits

            else:
                return False

        else:
            return False

    def issubtype(self, supertype):
        if supertype.generic == "Primitive":
            if supertype._dtype.kind == "c":
                if self._dtype.kind == "i" or self._dtype.kind == "u":
                    return True
                elif self._dtype.kind == "c" or self._dtype.kind == "f":
                    return self._dtype.itemsize <= supertype._dtype.itemsize
                else:
                    return False

            elif supertype._dtype.kind == "f":
                if self._dtype.kind == "i" or self._dtype.kind == "u":
                    return True
                elif self._dtype.kind == "f":
                    return self._dtype.itemsize <= supertype._dtype.itemsize
                else:
                    return False

            elif supertype._dtype.kind == "i":
                if self._dtype.kind == "i":
                    return self._dtype.itemsize <= supertype._dtype.itemsize
                elif self._dtype.kind == "u":
                    return self._dtype.itemsize <= supertype._dtype.itemsize - 0.125
                else:
                    return False

            elif supertype._dtype.kind == "u":
                if self._dtype.kind == "u":
                    return self._dtype.itemsize <= supertype._dtype.itemsize
                else:
                    return False

            else:
                return False

        else:
            return False

class PrimitiveWithRepr(Type):
    def __init__(self, dtype, repr):
        self._repr = repr
        Primitive.__init__(self, dtype)

    @property
    def generic(self):
        return "Primitive"

    def __repr__(self):
        return self._repr
