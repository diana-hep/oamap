import copy

class Type(object):
    def __init__(self, nullable=False, tag=None, repr=None):
        self._nullable = nullable
        self._tag = tag
        self._repr = repr
        if tag is None:
            self._tagstolinks = {}
        else:
            self._tagstolinks = {tag: self}

    @property
    def nullable(self):
        return self._nullable

    @property
    def tag(self):
        return self._tag

    @property
    def generic(self):
        return self.__class__.__name__

    @property
    def params(self):
        return ()

    @property
    def children(self):
        return ()

    def resolve(self, tagstolinks):
        pass

    def __repr__(self):
        return self._repr_memo(set())

    def _repr_memo(self, memo):
        if self._repr is not None:
            return self._repr
        raise NotImplementedError

    def _update_memo(self, memo):
        if self._tag is not None:
            if self._tag in memo:
                return self._tag
            else:
                memo.add(self._tag)
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
    tagstolinks = {}

    def collect(tpe):
        for n, t in tpe._tagstolinks.items():
            if n in tagstolinks and t != tagsotlinks[n]:
                raise TypeError("redefined tag {0}: {1} vs {2}".format(n, t, tagstolinks[n]))
            tagstolinks.update(tpe._tagstolinks)

        for t in tpe.children:
            if isinstance(t, Type):
                collect(t)

    for tpe in types:
        if isinstance(tpe, Type):
            collect(tpe)

    for tpe in types:
        tpe.resolve(tagstolinks)

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
