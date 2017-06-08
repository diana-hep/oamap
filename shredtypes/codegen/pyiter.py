# import os; os.chdir("..")

import sys

from shredtypes.typesystem.np import *
from shredtypes.typesystem.lr import *
from shredtypes.flat.names import *
from shredtypes.shred import *

tpe = List(Record({"a": int32, "b": List(float64)}))
dtypes = declare(tpe, "x")
arrays = NumpyFillableGroup(dtypes)
toflat([{"a": 1, "b": [0.1, 1.1, 2.1]}, {"a": 2, "b": []}, {"a": 3, "b": [0.3, 3.3]}], tpe, arrays, "x")

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
            itemsgetter, itemsupdater, itemsids = \
                recurse(tpe.items, modifiers(tpe, name).list(tpe.items.label))

            itemsargs = ", ".join("index_{0}".format(i) for i in itemsids)
            selfitemsargs = ", ".join("self.index_{0}".format(i) for i in itemsids)

            namenum = getnamenum()
            getter = "get_{0}_{1}".format(prefix, namenum)
            updater = "update_{0}_{1}".format(prefix, namenum)

            countdowns = []
            ids = itemsids
            for n, i in arrayid.items():
                if n.issize and (n.startswith(name) or n.bylabelstartswith(name)):
                    countdowns.append(i)
                    if i not in ids:
                        ids += (i,)

            assert len(countdowns) > 0, "missing list index"
            selfcountdown = "self.countdown = int(array_{0}[index_{0}])".format(countdowns[0])
            subcountdown = "subcountdown = int(array_{0}[index_{0}])".format(countdowns[0])
            incrementcountdowns = "; ".join("index_{0} += 1".format(i) for i in countdowns)

            indexes = ", ".join("index_{0}".format(i) for i in ids)
            strindexes = ", ".join("\"index_{0}\"".format(i) for i in ids)
            assignindexes = "; ".join("self.index_{0} = index_{0}".format(i) for i in ids)
            selfindexes = ", ".join("self.index_{0}".format(i) for i in ids)

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

            return getter, updater, ids

        elif isinstance(tpe, Record):
            fieldsgetters = {}
            fieldsupdaters = {}
            fieldsids = {}
            ids = ()
            for fn, ft in tpe.fields.items():
                fgetter, fupdater, fids = recurse(ft, modifiers(tpe, name).field(fn))
                fieldsgetters[fn] = fgetter
                fieldsupdaters[fn] = fupdater
                fieldsids[fn] = fids
                ids += fids

            properties = ""
            for fn in tpe.fields:
                properties += """
    @property
    def {fn}(self):
        return {getter}({indexes})
""".format(fn = fn,
           getter = fieldsgetters[fn],
           indexes = ", ".join("self.index_{0}".format(i) for i in fieldsids[fn]))

            callfieldsupdaters = ""
            for fn in tpe.fields:
                callfieldsupdaters += "    {indexes} = {updater}(countdown, {indexes})\n".format(
                    updater = fieldsupdaters[fn],
                    indexes = ", ".join("index_{0}".format(i) for i in fieldsids[fn]))

            namenum = getnamenum()
            getter = "get_{0}_{1}".format(prefix, namenum)
            updater = "update_{0}_{1}".format(prefix, namenum)

            indexes = ", ".join("index_{0}".format(i) for i in ids)
            strindexes = ", ".join("\"index_{0}\"".format(i) for i in ids)
            assignindexes = "; ".join("self.index_{0} = index_{0}".format(i) for i in ids)

            code = """
class {getter}(object):
    __slots__ = [{strindexes}]

    def __init__(self, {indexes}):
        {assignindexes}
{properties}

def {updater}(countdown, {indexes}):
{callfieldsupdaters}
    return {indexes}
""".format(**vars())
            execute(code, namespace)
            print(code)

            return getter, updater, ids

        else:
            assert False, "unrecognized type: {0}".format(tpe)

    getter, updater, ids = recurse(tpe, Name(prefix))

    return eval("{0}({1})".format(getter, ", ".join("0" for i in ids)), namespace)
