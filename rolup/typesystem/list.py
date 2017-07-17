from rolup.util import *
from rolup.typesystem.type import Type

class List(Type):
    def __init__(self, of):
        self.of = of
        super(List, self).__init__()

    @property
    def args(self):
        return (self.of,)

    def __contains__(self, element):
        try:
            iter(element)
        except TypeError:
            return False
        else:
            return all(x in self.of for x in element)     # lists are covariant

    def issubtype(self, supertype):
        return isinstance(supertype, List) and self.rtname == supertype.rtname \
               and self.of.issubtype(supertype.of)        # lists are covariant

    def toJson(self):
        return {"list": self.of.toJson()}
