import numpy

from shredtypes.typesystem.np import *
from shredtypes.typesystem.lr import *
from shredtypes.flat.np import *
from shredtypes.flat.names import *

sizetype = numpy.dtype(numpy.uint64)               # max list size is 18446744073709551613
sizetypenull = int(numpy.cast[sizetype.type](-1))  # 18446744073709551615
sizetypeterm = int(numpy.cast[sizetype.type](-2))  # 18446744073709551614

tagtype = numpy.dtype(numpy.uint8)                 # max number of union possibilities is 253
tagtypenull = int(numpy.cast[tagtype.type](-1))    # 255
tagtypeterm = int(numpy.cast[tagtype.type](-2))    # 254

def modifiers(tpe, name):
    if tpe.nullable:
        name = name.nullable()
    if tpe.label is not None:
        name = name.label(tpe.label)
    if tpe.runtime is not None:
        name = name.runtime(tpe.runtime)
    return name

def declare(tpe, name):
    def assign(name, dtype, out, memo):
        oldname = None
        for n in out:
            if n.bylabelequal(name):
                memo.add(n.lastlabel)
                oldname = n
                break
        if oldname is None:
            out[name] = dtype
            return name
        elif oldname.depth > name.depth:
            assert out[oldname] == dtype
            return oldname
        else:
            del out[oldname]
            out[name] = dtype
            return name

    def recurse(tpe, tpename, sizes, sizename, out, memo):
        if isinstance(tpe, Primitive):
            tpe._arrayname = assign(modifiers(tpe, tpename), tpe.dtype, out, memo)

            if sizename is not None:
                n = assign(sizename.size(), sizetype, out, memo)
                for s in sizes:
                    s._arrayname = n

        elif isinstance(tpe, List):
            if tpe.items.label not in memo:
                name = modifiers(tpe, tpename).list(tpe.items.label)
                recurse(tpe.items, name, sizes + (tpe,), name, out, memo)

        elif isinstance(tpe, Record):
            for fn, ft in tpe.fields.items():
                recurse(ft, modifiers(tpe, tpename).field(fn), sizes, sizename, out, memo)

        else:
            assert False, "unrecognized type: {0}".format(tpe)

    dtypes = {}
    recurse(tpe, Name(name), (), None, dtypes, set())

    def stringnames(tpe, memo):
        if tpe._arrayname is not None:
            tpe._arrayname = str(tpe._arrayname)
        memo.add(id(tpe))
        for t in tpe.children:
            if id(t) not in memo:
                stringnames(t, memo)

    stringnames(tpe, set())

    return dict((str(n), t) for n, t in dtypes.items())

def extracttype(dtypes, name):
    def modifiers(name):
        nullable = name.isnullable
        if name.isnullable:
            name = name.pullnullable()

        label = None
        if name.islabel:
            label, name = name.pulllabel()

        runtime = None
        if name.isruntime:
            runtime, name = name.pullruntime()

        return name, nullable, label, runtime

    def recurse(dtypes, memo):
        assert len(dtypes) > 0

        check = {}
        trimmed = {}
        for n, d in dtypes.items():
            n, nullable, label, runtime = modifiers(n)
            islist = n.islist
            isrecord = n.isfield

            if "nullable" in check: assert nullable == check["nullable"]
            else: check["nullable"] = nullable

            if "label" in check: assert label == check["label"]
            else: check["label"] = label

            if "runtime" in check: assert runtime == check["runtime"]
            else: check["runtime"] = runtime

            if "islist" in check: assert islist == check["islist"]
            else: check["islist"] = islist

            if "isrecord" in check: assert isrecord == check["isrecord"]
            else: check["isrecord"] = isrecord

            if islist:
                listof, n = n.pulllist()
                trimmed[n] = d
                if "listof"in check: assert listof == check["listof"]
                else: check["listof"] = listof

            elif isrecord:
                field, n = n.pullfield()
                trimmed[field] = trimmed.get(field, {})
                trimmed[field][n] = d

            else:
                trimmed[n] = d

        assert not (islist and isrecord)

        if not islist and not isrecord:
            assert len(trimmed) == 1
            (n, d), = trimmed.items()
            out = identifytype(Primitive(d, nullable, label, runtime))

        elif islist:
            out = List(recurse(trimmed, memo), nullable, label, runtime)

        elif isrecord:
            out = Record(dict((fn, recurse(dts, memo)) for fn, dts in trimmed.items()), nullable, label, runtime)
            if label in memo:
                out._fields.update(memo[label].fields)

        if label is not None:
            memo[label] = out
        return out

    parsed = {}
    for n, d in dtypes.items():
        p = Name.parse(name, n)
        if p is not None and not p.issize and not p.istag:
            parsed[p] = d

    def check(tpe):
        # important! also assigns arraynames via declare()
        assert dtypes == declare(tpe, name)
        return tpe

    return check(recurse(parsed, {}))

def toflat(obj, tpe, arrays, prefix):
    arrays = dict((Name.parse(n), a) for n, a in arrays.items())

    def has(x, n):
        if x is None:
            return False
        elif isinstance(x, dict):
            return n in x
        else:
            return hasattr(x, n)

    def get(x, n):
        if isinstance(x, dict):
            return x[n]
        else:
            return getattr(x, n)

    def recurse(obj, tpe, name):
        if isinstance(tpe, Primitive):
            if tpe.nullable and obj is None:
                arrays[tpe.arrayname].append(null[tpe])
            else:
                arrays[tpe.arrayname].append(obj)

        elif isinstance(tpe, List):
            if tpe.nullable and obj is None:
                length = sizetypenull
            else:
                length = len(obj)
            for n, a in arrays.items():
                if n.issize and n.startswith(name):
                    a.append(length)
            if not tpe.nullable or obj is not None:
                for x in obj:
                    recurse(x, tpe.items, modifiers(tpe, name).list(tpe.items.label))

        elif isinstance(tpe, Record):
            for fn, ft in tpe.fields.items():
                if tpe.nullable and not has(obj, fn):
                    recurse(None, ft, modifiers(tpe, name).field(fn))
                else:
                    recurse(get(obj, fn), ft, modifiers(tpe, name).field(fn))

        else:
            assert False

    recurse(obj, tpe, Name(prefix))
