from pquiver.typesystem.defs import *
from pquiver.typesystem.np import *
from pquiver.typesystem.lrup import *
from pquiver.typesystem.naming import *

def declare(tpe, prefix, sizetype=uint64, tagtype=uint8):
    def modifiers(tpe, name):
        if tpe.optional:
            name = name.optional()
        if tpe.rtname is not None:
            name = name.runtime(tpe.rtname)
        return name

    def recurse(tpe, name, sizename):
        if isinstance(tpe, Primitive):
            if sizename is None:
                return {str(modifiers(tpe, name)): tpe.dtype}
            else:
                return {str(modifiers(tpe, name)): tpe.dtype, str(sizename.size()): sizetype}

        elif isinstance(tpe, List):
            name = modifiers(tpe, name).list()
            return recurse(tpe.items, name, name)

        elif isinstance(tpe, Record):
            out = {}
            for n, t in tpe.fields.items():
                out.update(recurse(t, modifiers(tpe, name).field(n), sizename))
            return out

        else:
            assert False, "unrecognized type: {0}".format(tpe)

    return recurse(tpe, ArrayName(prefix), None)

def extracttype(dtypes, prefix):
    def modifiers(name):
        optional = name.isoptional
        if name.isoptional:
            name = name.dropoptional()
        rtname = None
        if name.isruntime:
            rtname, name = name.dropruntime()
        return name, optional, rtname

    def recurse(dtypes):
        assert len(dtypes) > 0

        check = {}
        trimmed = {}
        for n, d in dtypes.items():
            n, optional, rtname = modifiers(n)
            islist = n.islist
            isrecord = n.isrecord

            if "optional" in check: assert optional == check["optional"]
            else: check["optional"] = optional

            if "rtname" in check: assert rtname == check["rtname"]
            else: check["rtname"] = rtname

            if "islist" in check: assert islist == check["islist"]
            else: check["islist"] = islist

            if "isrecord" in check: assert isrecord == check["isrecord"]
            else: check["isrecord"] = isrecord

            if islist:
                n = n.droplist()
                trimmed[n] = d

            elif isrecord:
                fname, n = n.dropfield()
                trimmed[fname] = trimmed.get(fname, {})
                trimmed[fname][n] = d

            else:
                trimmed[n] = d

        assert not (islist and isrecord)

        if not islist and not isrecord:
            assert len(trimmed) == 1
            (n, d), = trimmed.items()
            out = identifytype(Primitive(d))

        elif islist:
            out = List(recurse(trimmed))

        elif isrecord:
            out = Record(**dict((n, recurse(dts)) for n, dts in trimmed.items()))

        if optional:
            out = Optional(out)

        if rtname is None:
            return out
        else:
            return Type.materialize(rtname, out)

    parsed = {}
    for n, d in dtypes.items():
        p = ArrayName.parse(prefix, n)
        if p is not None:
            if p.ispage:
                p = p.droppage()
            if not p.issize and not p.istag:
                parsed[p] = d

    return recurse(parsed)

def toflat(obj, tpe, group, prefix):
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

    def recurse(obj, tpe, name, optional):





        if isinstance(tpe, Optional):
            recurse(obj, tpe.type, name, True)

        elif isinstance(tpe, Primitive):
            if optional and obj is None:
                group.byname(






    recurse(obj, tpe, ArrayName(prefix), False)
