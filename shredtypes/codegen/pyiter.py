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

    def firstpass(tpe, name, funcnames):
        if name.bylabelpath in funcnames:
            return funcnames[name.bylabelpath]

        if isinstance(tpe, Primitive):
            namenum = getnamenum()
            getter = "get_{0}_{1}".format(prefix, namenum)
            updater = "update_{0}_{1}".format(prefix, namenum)

            i = arrayid[Name.parse(prefix, tpe.arrayname)]
            funcnames[name.bylabelpath] = getter, updater, [i]

        elif isinstance(tpe, List):
            namenum = getnamenum()
            getter = "get_{0}_{1}".format(prefix, namenum)
            updater = "update_{0}_{1}".format(prefix, namenum)

            ids = []
            for n, i in arrayid.items():
                if n.issize and (n.startswith(name) or n.bylabelstartswith(name)):
                    ids.append(i)

            funcnames[name.bylabelpath] = getter, updater, ids

            itemsgetter, itemsupdater, itemsids = \
                firstpass(tpe.items, modifiers(tpe, name).list(tpe.items.label), funcnames)
            ids.append(itemsids)

        elif isinstance(tpe, Record):
            namenum = getnamenum()
            getter = "get_{0}_{1}".format(prefix, namenum)
            updater = "update_{0}_{1}".format(prefix, namenum)

            ids = []
            funcnames[name.bylabelpath] = getter, updater, ids

            for fn, ft in tpe.fields.items():
                fgetter, fupdater, fids = firstpass(ft, modifiers(tpe, name).field(fn), funcnames)
                ids.append(fids)

        else:
            assert False, "unrecognized type: {0}".format(tpe)

        return funcnames[name.bylabelpath]

    def flatten(lst):
        def recurse(lst, memo):
            if id(lst) not in memo:
                memo.add(id(lst))
                for x in lst:
                    if isinstance(x, list):
                        for y in recurse(x, memo):
                            yield y
                    else:
                        yield x
        return sorted(set(recurse(lst, set())))

    def secondpass(tpe, name, funcnames, memo):
        if name.bylabelpath in memo:
            return funcnames[name.bylabelpath]
        memo.add(name.bylabelpath)

        if isinstance(tpe, Primitive):
            getter, updater, ids = funcnames[name.bylabelpath]
            i, = ids

            code = """
def {getter}(index):
    return array_{i}[index]

def {updater}(countdown, index_{i}):
    return index_{i} + countdown
""".format(getter = getter, updater = updater, i = i)
            execute(code, namespace)
            print(code)

            return funcnames[name.bylabelpath]

        elif isinstance(tpe, List):
            getter, updater, ids = funcnames[name.bylabelpath]

            countdowns = []
            for n, i in arrayid.items():
                if n.issize and (n.startswith(name) or n.bylabelstartswith(name)):
                    countdowns.append(i)

            itemsgetter, itemsupdater, itemsids = \
                secondpass(tpe.items, modifiers(tpe, name).list(tpe.items.label), funcnames, memo)
            
            itemsargs = ", ".join("index_{0}".format(i) for i in flatten(itemsids))
            selfitemsargs = ", ".join("self.index_{0}".format(i) for i in flatten(itemsids))

            assert len(countdowns) > 0, "missing list index"
            selfcountdown = "self.countdown = int(array_{0}[index_{0}])".format(countdowns[0])
            subcountdown = "subcountdown = int(array_{0}[index_{0}])".format(countdowns[0])
            incrementcountdowns = "; ".join("index_{0} += 1".format(i) for i in countdowns)

            indexes = ", ".join("index_{0}".format(i) for i in flatten(ids))
            strindexes = ", ".join("\"index_{0}\"".format(i) for i in flatten(ids))
            assignindexes = "; ".join("self.index_{0} = index_{0}".format(i) for i in flatten(ids))
            selfindexes = ", ".join("self.index_{0}".format(i) for i in flatten(ids))

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

            return funcnames[name.bylabelpath]

        elif isinstance(tpe, Record):
            getter, updater, ids = funcnames[name.bylabelpath]

            fieldsgetters = {}
            fieldsupdaters = {}
            fieldsids = {}
            for fn, ft in tpe.fields.items():
                fgetter, fupdater, fids = secondpass(ft, modifiers(tpe, name).field(fn), funcnames, memo)
                fieldsgetters[fn] = fgetter
                fieldsupdaters[fn] = fupdater
                fieldsids[fn] = fids

            properties = ""
            for fn in tpe.fields:
                properties += """
    @property
    def {fn}(self):
        return {getter}({indexes})
""".format(fn = fn,
           getter = fieldsgetters[fn],
           indexes = ", ".join("self.index_{0}".format(i) for i in flatten(fieldsids[fn])))

            callfieldsupdaters = ""
            for fn in tpe.fields:
                callfieldsupdaters += "    {indexes} = {updater}(countdown, {indexes})\n".format(
                    updater = fieldsupdaters[fn],
                    indexes = ", ".join("index_{0}".format(i) for i in flatten(fieldsids[fn])))

            indexes = ", ".join("index_{0}".format(i) for i in flatten(ids))
            strindexes = ", ".join("\"index_{0}\"".format(i) for i in flatten(ids))
            assignindexes = "; ".join("self.index_{0} = index_{0}".format(i) for i in flatten(ids))

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

            return funcnames[name.bylabelpath]

    funcnames = {}
    firstpass(tpe, Name(prefix), funcnames)
    getter, updater, ids = secondpass(tpe, Name(prefix), funcnames, set())

    return eval("{0}({1})".format(getter, ", ".join("0" for i in ids)), namespace)

iterator = generate(arrays, tpe, "x")

def analyze(tree, indent=""):
    print(indent + "data " + str(tree.data))
    for child in tree.children:
        analyze(child, indent + "  ")

for x in iterator:
    analyze(x)
