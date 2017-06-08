# import os; os.chdir("..")

import sys

from shredtypes.typesystem.np import *
from shredtypes.typesystem.lr import *
from shredtypes.flat.names import *
from shredtypes.shred import *

tpe = List(List(int32))
dtypes = declare(tpe, "x")
arrays = NumpyFillableGroup(dtypes)
toflat([[1, 2, 3], [], [4, 5]], tpe, arrays, "x")

def execute(code, namespace):
    exec(code, namespace)

def generate(arrays, tpe, prefix):
    namespace = {}
    if sys.version_info[0] > 2:
        namespace["xrange"] = range

    arrayid = {}
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
            execute(code, namespace)
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
                    countdowns.append(i)
                    if i not in arraysneeded:
                        arraysneeded += (i,)

            assert len(countdowns) > 0, "missing list index"
            selfcountdown = "self.countdown = int(array_{0}[index_{0}])".format(countdowns[0])
            subcountdown = "subcountdown = int(array_{0}[index_{0}])".format(countdowns[0])
            incrementcountdowns = "; ".join("index_{0} += 1".format(i) for i in countdowns)

            indexes = ", ".join("index_{0}".format(i) for i in arraysneeded)
            strindexes = ", ".join("\"index_{0}\"".format(i) for i in arraysneeded)
            assignindexes = "; ".join("self.index_{0} = index_{0}".format(i) for i in arraysneeded)
            selfindexes = ", ".join("self.index_{0}".format(i) for i in arraysneeded)

            code = """
class {getter}(object):
    __slots__ = ["countdown", {strindexes}]

    def __init__(self, {indexes}):
        {selfcountdown}
        {incrementcountdowns}
        {assignindexes}

    def __iter__(self):
        return self.Iterator(self.countdown, {selfindexes})

    class Iterator(object):
        __slots__ = ["countdown", {strindexes}]

        def __init__(self, countdown, {indexes}):
            self.countdown = countdown
            {assignindexes}

        def __next__(self):
            self.countdown -= 1
            if self.countdown >= 0:
                out = {itemsgetter}({selfitemsargs})
                {selfitemsargs} = {itemsupdater}(1, {selfitemsargs})
                return out

            else:
                raise StopIteration

        next = __next__

def {updater}(countdown, {indexes}):
    for i in xrange(countdown):
        {subcountdown}
        {incrementcountdowns}
        {itemsargs} = {itemsupdater}(subcountdown, {itemsargs})
    return {indexes}
""".format(**vars())
            execute(code, namespace)
            print(code)

            return getter, updater, arraysneeded

    getter, updater, arraysneeded = recurse(tpe, Name(prefix))

    return eval("{0}({1})".format(getter, ", ".join("0" for i in arraysneeded)), namespace)
