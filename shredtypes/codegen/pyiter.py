# import os; os.chdir("..")

import sys

from shredtypes.typesystem.np import *
from shredtypes.typesystem.lr import *
from shredtypes.flat.names import *
from shredtypes.shred import *

tpe = resolve(List(Record(dict(children=List("T"), data=float64), label="T")))
dtypes = declare(tpe, "x")
arrays = NumpyFillableGroup(dtypes)
toflat([{"children": [{"children": [{"children": [], "data": 3.3}], "data": 2.2}, {"children": [], "data": 4.4}], "data": 1.1}, {"children": [], "data": 5.5}], tpe, arrays, "x")

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

    def recurse(tpe, name, memo):
        if name.bylabelpath in memo:
            return memo[name.bylabelpath]

        global namenum
        if isinstance(tpe, Primitive):
            namenum = getnamenum()
            getter = "get_{0}_{1}".format(prefix, namenum)
            updater = "update_{0}_{1}".format(prefix, namenum)

            i = arrayid[Name.parse(prefix, tpe.arrayname)]
            memo[name.bylabelpath] = getter, updater, [i]

            code = """
def {getter}(index):
    return array_{i}[index]

def {updater}(countdown, index_{i}):
    return index_{i} + countdown
""".format(getter = getter, updater = updater, i = i)
            execute(code, namespace)
            print(code)

            return memo[name.bylabelpath]

        elif isinstance(tpe, List):
            namenum = getnamenum()
            getter = "get_{0}_{1}".format(prefix, namenum)
            updater = "update_{0}_{1}".format(prefix, namenum)

            ids = []
            countdowns = []
            for n, i in arrayid.items():
                if n.issize and (n.startswith(name) or n.bylabelstartswith(name)):
                    countdowns.append(i)
                    if i not in ids:
                        ids.append(i)
            memo[name.bylabelpath] = getter, updater, ids

            itemsgetter, itemsupdater, itemsids = \
                recurse(tpe.items, modifiers(tpe, name).list(tpe.items.label), memo)
            for i in itemsids:
                if i not in ids:
                    ids.append(i)

            itemsargs = ", ".join("index_{0}".format(i) for i in itemsids)
            selfitemsargs = ", ".join("self.index_{0}".format(i) for i in itemsids)

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

            return memo[name.bylabelpath]

        elif isinstance(tpe, Record):
            namenum = getnamenum()
            getter = "get_{0}_{1}".format(prefix, namenum)
            updater = "update_{0}_{1}".format(prefix, namenum)

            ids = []
            memo[name.bylabelpath] = getter, updater, ids

            fieldsgetters = {}
            fieldsupdaters = {}
            fieldsids = {}
            for fn, ft in tpe.fields.items():
                fgetter, fupdater, fids = recurse(ft, modifiers(tpe, name).field(fn), memo)
                fieldsgetters[fn] = fgetter
                fieldsupdaters[fn] = fupdater
                fieldsids[fn] = fids
                for i in fids:
                    if i not in ids:
                        ids.append(i)

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

            return memo[name.bylabelpath]

        else:
            assert False, "unrecognized type: {0}".format(tpe)

    getter, updater, ids = recurse(tpe, Name(prefix), {})

    return eval("{0}({1})".format(getter, ", ".join("0" for i in ids)), namespace)
