import numpy

from shredtypes.typesystem.np import *
from shredtypes.typesystem.lr import *
from shredtypes.flat.np import *
from shredtypes.flat.names import *

sizetype = numpy.dtype(numpy.uint64)
tagtype = numpy.dtype(numpy.uint8)

def columns(tpe, name):
    def modifiers(tpe, name):
        if tpe.nullable:
            name = name.nullable()
        if tpe.label is not None:
            name = name.label(tpe.label)
        if tpe.runtime is not None:
            name = name.runtime(tpe.runtime)
        return name

    def deepest(name, dtype, out, memo):
        oldname = None
        for n in out:
            if n.eqbylabel(name):
                memo.add(n.lastlabel)
                oldname = n
                break
        if oldname is None:
            out[name] = dtype
        elif oldname.depth > name.depth:
            assert out[oldname] == dtype
        else:
            del out[oldname]
            out[name] = dtype

    def recurse(tpe, name, sizename, out, memo):
        if isinstance(tpe, Primitive):
            deepest(modifiers(tpe, name), tpe.dtype, out, memo)
            if sizename is not None:
                deepest(sizename.size(), sizetype, out, memo)

        elif isinstance(tpe, List):
            if tpe.items.label not in memo:
                name = modifiers(tpe, name).list(tpe.items.label)
                recurse(tpe.items, name, name, out, memo)

        elif isinstance(tpe, Record):
            for fn, ft in tpe.fields.items():
                recurse(ft, modifiers(tpe, name).field(fn), sizename, out, memo)

        else:
            assert False, "unrecognized type: {0}".format(tpe)

    out = {}
    recurse(tpe, Name(name), None, out, set())
    return dict((str(n), t) for n, t in out.items())

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
        assert dtypes == columns(tpe, name)
        return tpe

    return check(recurse(parsed, {}))
