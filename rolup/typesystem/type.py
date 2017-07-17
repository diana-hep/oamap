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
    def materialize(rtname, iterator):
        if rtname not in Type.runtimes:
            raise TypeDefinitionError("runtime name \"{0}\" is not recognized (not registered?)".format(rtname))
        else:
            return Type.runtimes[rtname].materialize(iterator)

    @property
    def rtname(self):
        return None

    @property
    def args(self):
        return ()

    @property
    def kwds(self):
        return {}

    def __repr__(self):
        args = [repr(v) for v in self.args]
        kwds = [n + " = " + repr(v) for n, v in sorted(self.kwds)]
        return "{0}({1})".format(self.__class__.__name__, ", ".join(args + kwds))

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
        raise NotImplementedError

    def issubtype(self, supertype):
        raise NotImplementedError
