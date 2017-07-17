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
