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
