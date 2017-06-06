from shredtypes.typesystem.np import *
from shredtypes.typesystem.lr import *
from shredtypes.flat.np import *
from shredtypes.flat.names import *

sizetype = uint64
tagtype = uint8

def columns(tpe, name):
    def modifiers(tpe, name):
        if tpe.nullable:
            name = name.nullable()
        if tpe.label is not None:
            name = name.label(tpe.label)
        if tpe.runtime is not None:
            name = name.runtime(tpe.runtime)
        return name

    def recurse(tpe, name, sizename, memo):
        if isinstance(tpe, Primitive):
            if sizename is None:
                return {str(modifiers(tpe, name)): tpe.dtype}
            else:
                return {str(modifiers(tpe, name)): tpe.dtype, str(sizename.size()): sizetype}

        elif isinstance(tpe, List):
            if tpe.items.label is not None and tpe.items.label in memo:
                return {}
            else:
                if tpe.items.label is not None:
                    memo.add(tpe.items.label)
                name = modifiers(tpe, name).list(tpe.items.label)
                return recurse(tpe.items, name, name, memo)

        elif isinstance(tpe, Record):
            out = {}
            for fn, ft in tpe.fields.items():
                out.update(recurse(ft, modifiers(tpe, name).field(fn), sizename, memo))
            return out

        else:
            assert False, "unrecognized type: {0}".format(tpe)

    return recurse(tpe, Name(name), None, set())

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

    def recurse(dtypes):
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
                l, n = n.pulllist()
                trimmed[n] = d

            elif isrecord:
                field, n = n.pullfield()
                trimmed[field] = trimmed.get(field, {})
                trimmed[field][n] = d

            else:
                trimmed[n] = d

        print(check)

        assert not (islist and isrecord)

        if not islist and not isrecord:
            assert len(trimmed) == 1
            (n, d), = trimmed.items()
            return identifytype(Primitive(d, nullable, label, runtime))

        elif islist:
            return List(recurse(trimmed), nullable, label, runtime)

        elif isrecord:
            return Record(dict((fn, recurse(dts)) for fn, dts in trimmed.items()), nullable, label, runtime)

    parsed = {}
    for n, d in dtypes.items():
        p = Name.parse(name, n)
        if p is not None and not p.issize and not p.istag:
            parsed[p] = d

    def check(tpe):
        assert dtypes == columns(tpe, name)
        return tpe

    return check(recurse(parsed))
