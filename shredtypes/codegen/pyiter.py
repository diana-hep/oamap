from shredtypes.typesystem.np import *
from shredtypes.typesystem.lr import *
from shredtypes.flat.names import *
from shredtypes.shred import *

tpe = List(int32)
dtypes = declare(tpe, "x")
arrays = NumpyFillableGroup(dtypes)
toflat([1, 2, 3], tpe, arrays, "x")

def generate(arrays, tpe, prefix):
    arrayid = {}
    namespace = {}
    for i, n in enumerate(arrays.names):
        print("array_{0} = arrays.byname(\"{1}\").array".format(i, n))
        namespace["array_{0}".format(i)] = arrays.byname(n).array
        arrayid[Name.parse(prefix, n)] = i

    def nn_generate():
        namenum = 0
        while True:
            yield namenum
            namenum += 1
    getnamenum = getattr(nn_generate(), "__next__", getattr(nn_generate(), "next"))

    def recurse(tpe, name):
        global namenum
        if isinstance(tpe, Primitive):
            namenum = getnamenum()
            getter = "get_{0}_{1}".format(prefix, namenum)
            updater = "update_{0}_{1}".format(prefix, namenum)

            i = arrayid[Name.parse(prefix, tpe.arrayname)]
            code = """
def {getter}(index):
    return array_{i}[index]

def {updater}(countdown, index_{i}):
    return index_{i} + countdown
""".format(getter = getter, updater = updater, i = i)
            # exec(code, namespace)
            print(code)

            return getter, updater, (i,)

        elif isinstance(tpe, List):
            itemsgetter, itemsupdater, itemsarraysneeded = \
                recurse(tpe.items, modifiers(tpe, name).list(tpe.items.label))

            itemsargs = ", ".join("index_{0}".format(i) for i in itemsarraysneeded)
            selfitemsargs = ", ".join("self.index_{0}".format(i) for i in itemsarraysneeded)

            namenum = getnamenum()
            getter = "get_{0}_{1}".format(prefix, namenum)
            updater = "update_{0}_{1}".format(prefix, namenum)

            countdowns = []
            arraysneeded = itemsarraysneeded
            for n, i in arrayid.items():
                if n.issize and (n.startswith(name) or n.bylabelstartswith(name)):
                    if i not in arraysneeded:
                        arraysneeded += (i,)
            selfcountdown = "; ".join("self.countdown = index_{0}".format(i) for i in countdowns)
            subcountdown = "; ".join("subcountdown = index_{0}".format(i) for i in countdowns)

            indexes = ", ".join("index_{0}".format(i) for i in arraysneeded)
            strindexes = ", ".join("\"index_{0}\"".format(i) for i in arraysneeded)
            assignindexes = "; ".join("self.index_{0} = index_{0}".format(i) for i in arraysneeded)
            selfindexes = ", ".join("self.index_{0}".format(i) for i in arraysneeded)

            code = """
from builtins import object

class {getter}(object):
    __slots__ = ["countdown", {strindexes}]

    class Iterator(object):
        __slots__ = [{strindexes}]

        def __init__(self, countdown, {indexes}):
            self.countdown = countdown
            {assignindexes}

        def __next__(self):
            self.countdown -= 1
            if self.countdown >= 0:
                out = {itemsgetter}({itemsargs})
                {selfitemsargs} = {itemsupdater}(1, {itemsargs})
                return out

            else:
                raise StopIteration

    def __init__(self, {indexes}):
        {selfcountdown}
        {assignindexes}

    def __iter__(self):
        return self.Iterator(self.countdown, {selfindexes})

def {updater}(countdown, {indexes}):
    countdown -= 1
    while countdown >= 0:
        {subcountdown}
        {itemsargs} = {itemsupdater}(subcountdown, {itemsargs})
    return {indexes}
""".format(**vars())
            # exec(code, namespace)
            print(code)

            return getter, updater, arraysneeded

    getter, updater, arraysneeded = recurse(tpe, Name(prefix))
    print(getter)
