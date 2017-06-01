import re

from shredtypes.typesystem.np import *
from shredtypes.typesystem.lr import *
from shredtypes.flat.np import *

sizetype = uint64

def columns(tpe, name):
    def recurse(tpe, name, sizename):
        if tpe.nullable:
            name = name + "#"

        # TODO: when we have custom types, append a "$typename" to name

        if isinstance(tpe, Primitive):
            if sizename is None:
                return {name: tpe.dtype}
            else:
                return {name: tpe.dtype, sizename + "@size": sizetype}

        elif isinstance(tpe, List):
            name = name + "[]"
            return recurse(tpe.items, name, name)

        elif isinstance(tpe, Record):
            out = {}
            for fn, ft in tpe.fields.items():
                out.update(recurse(ft, name + "-" + fn, sizename))
            return out

        else:
            assert False, "unrecognized type: {0}".format(tpe)

    return recurse(tpe, name, None)

def extracttype(dtypes, name):
    # TODO: when we have custom types, handle the "$typename" in name

    if name in dtypes:
        return identifytype(Primitive(dtypes[name]))

    elif name + "#" in dtypes:
        return identifytype(Primitive(dtypes[name + "#"], nullable=True))

    elif any(not n.endswith("@size") and (n.startswith(name + "[]") or n.startswith(name + "#[]")) for n in dtypes):
        trimmed = dict((name + n[len(name) + 3:], v) for n, v in dtypes.items() if n.startswith(name + "#[]") and n != name + "#[]@size")
        if len(trimmed) == 0:
            nullable = False
            trimmed = dict((name + n[len(name) + 2:], v) for n, v in dtypes.items() if n.startswith(name + "[]") and n != name + "[]@size")
        else:
            nullable = True
        return List(extracttype(trimmed, name), nullable=nullable)    

    else:
        trimmed = dict((n[len(name) + 2:], v) for n, v in dtypes.items() if n.startswith(name + "#-"))
        if len(trimmed) == 0:
            nullable = False
            trimmed = dict((n[len(name) + 1:], v) for n, v in dtypes.items() if n.startswith(name + "-"))
        else:
            nullable = True

        fields = {}
        for n in trimmed:
            if not n.endswith("@size"):
                fn = re.match(r"([^-@[$#]*)", n).group(1)
                fields[fn] = extracttype(trimmed, fn)
        return Record(fields, nullable=nullable)
