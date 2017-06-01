class Type(object):
    def __init__(self, tag=None, repr=None):
        self._tag = tag
        self._repr = repr
        if tag is None:
            self._tags = {}
        else:
            self._tags = {tag: self}

    @property
    def tag(self):
        return self._tag

    @property
    def generic(self):
        return self.__class__.__name__

    @property
    def params(self):
        return ()

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
