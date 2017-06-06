import copy
import re

class Type(object):
    identifier = re.compile("^[a-zA-Z_][0-9a-zA-Z_]*$")
    runtimes = {}

    @staticmethod
    def register(runtime, cls):
        if runtime in Type.runtimes and Type.runtimes[runtime] != cls:
            raise RuntimeError("multiple types attempting to register runtime name {0}".format(runtime))
        Type.runtimes[runtime] = cls

    def __init__(self, nullable=False, label=None, runtime=None, repr=None):
        self._nullable = nullable
        self._label = label
        self._runtime = runtime
        self._repr = repr
        self._arrayname = None

        if label is None:
            self._labelstolinks = {}
        elif re.match(self.identifier, label) is not None:
            self._labelstolinks = {label: self}
        else:
            raise ValueError("labels must match [a-zA-Z_][0-9a-zA-Z_]*: {0}".format(label))

        if runtime is not None:
            if runtime not in self.runtimes:
                raise RuntimeError("no type has registered runtime name {0}".format(runtime))
            self.__class__ = self.runtimes[runtime]

    @property
    def nullable(self):
        return self._nullable

    @property
    def label(self):
        return self._label

    @property
    def runtime(self):
        return self._runtime

    @property
    def arrayname(self):
        return self._arrayname

    @property
    def generic(self):
        return self.__class__.__name__

    @property
    def params(self):
        return ()

    @property
    def children(self):
        return ()

    def resolve(self, labelstolinks):
        pass

    def __repr__(self):
        return self._repr_memo(set())

    def _repr_memo(self, memo):
        if self._repr is not None:
            return self._repr
        raise NotImplementedError

    def _update_memo(self, memo):
        if self._label is not None:
            if self._label in memo:
                return self._label
            else:
                memo.add(self._label)
                return None
        else:
            return None

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.nullable == other.nullable and self.params == other.params

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.__class__, self.params))

    def __contains__(self, other):
        return False

def resolve(*types):
    labelstolinks = {}

    def collect(tpe):
        for n, t in tpe._labelstolinks.items():
            if n in labelstolinks and t != labelsotlinks[n]:
                raise TypeError("redefined label {0}: {1} vs {2}".format(n, t, labelstolinks[n]))
        labelstolinks.update(tpe._labelstolinks)

        for t in tpe.children:
            if isinstance(t, Type):
                collect(t)

    for tpe in types:
        if isinstance(tpe, Type):
            collect(tpe)

    for tpe in types:
        tpe.resolve(labelstolinks)

    if len(types) == 1:
        return types[0]
    else:
        return types

def nullable(tpe):
    tpe = copy.copy(tpe)
    tpe._nullable = True
    if tpe._repr is not None:
        tpe._repr = "nullable({0})".format(tpe._repr)
    return tpe
