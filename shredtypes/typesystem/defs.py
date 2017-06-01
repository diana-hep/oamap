class Type(object):
    def __init__(self, tag=None, repr=None):
        self._tag = tag
        self._repr = repr
        if tag is None:
            self._tagstolinks = {}
        else:
            self._tagstolinks = {tag: self}

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
        if self._repr is not None:
            return self._repr
        else:
            return self._repr_memo(set())

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
        return self.__class__ == other.__class__ and self.params == other.params

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.__class__, self.params))

def resolve(*types):
    tagstolinks = {}

    def collect(tpe):
        for n, t in tpe._tagstolinks.items():
            if n in tagstolinks and t != tagsotlinks[n]:
                raise TypeError("redefined tag {0}:\n\n{1}".format(n, compare(t, tagstolinks[n], header=("original", "redefinition"))))
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
