import re

from shredtypes.typesystem.np import *
from shredtypes.typesystem.lr import *
from shredtypes.flat.np import *

sizetype = uint64
tagtype = uint8

class Name(object):
    identifier = re.compile("^[a-zA-Z_][0-9a-zA-Z_]*")

    @staticmethod
    def parse(prefix, string):
        if not string.startswith(prefix):
            return None
        
        path = []
        string = string[len(prefix):]

        while len(string) > 0:
            if string[0] == "?":
                string = string[1:]
                path.append(Name.NULLABLE())

            elif string[0] == "%":
                m = re.match(Name.identifier, string[1:])
                if m is None:
                    raise ValueError("\"%\" in string \"{0}\" not followed by an identifier ([a-zA-Z_][0-9a-zA-Z_]*)".format(string))
                label = string[1 : m.end(0) + 1]
                string = string[m.end(0) + 1 : ]
                path.append(Name.LABEL(label))

            elif string[0] == "$":
                m = re.match(Name.identifier, string[1:])
                if m is None:
                    raise ValueError("\"$\" in string \"{0}\" not followed by an identifier ([a-zA-Z_][0-9a-zA-Z_]*)".format(string))
                runtime = string[1 : m.end(0) + 1]
                string = string[m.end(0) + 1 : ]
                path.append(Name.RUNTIME(runtime))

            elif string[0:2] == "[]":
                string = string[2:]
                path.append(Name.LIST())

            elif string[0] == "#":
                string = string[1:]
                path.append(Name.UNION())

            elif string[0] == "-":
                m = re.match(Name.identifier, string[1:])
                if m is None:
                    raise ValueError("\"-\" in string \"{0}\" not followed by an identifier ([a-zA-Z_][0-9a-zA-Z_]*)".format(string))
                field = string[1 : m.end(0) + 1]
                string = string[m.end(0) + 1 : ]
                path.append(Name.FIELD(field))
                
            elif string == "@size":
                string = ""
                path.append(Name.SIZE())

            elif string == "@tag":
                string = ""
                path.append(Name.TAG())

        return Name(prefix, *path)

    def __init__(self, prefix, *path):
        self._prefix = prefix
        self._path = path

    @property
    def prefix(self):
        return self._prefix

    @property
    def path(self):
        return self._path

    def __repr__(self):
        return "Name({0}, {1})".format(self._prefix, self._path)

    def __str__(self):
        return self._prefix + "".join(map(str, self._path))

    def __eq__(self, other):
        return other.__class__ == Name and self._prefix == other._prefix and self._path == other._path

    def __hash__(self):
        return hash((self.__class__, self._prefix, self._path))

    class NULLABLE(object):
        def __repr__(self):
            return "NULLABLE()"
        def __str__(self):
            return "?"
        def __eq__(self, other):
            return other.__class__ == Name.NULLABLE
        def __hash__(self):
            return hash((self.__class__,))

    def nullable(self):
        return Name(self._prefix, *(self._path + (self.NULLABLE(),)))

    @property
    def isnullable(self):
        return len(self._path) > 0 and isinstance(self._path[0], Name.NULLABLE)

    def pullnullable(self):
        return Name(self._prefix, *self._path[1:])

    class LABEL(object):
        def __init__(self, label):
            self.label = label
        def __repr__(self):
            return "LABEL({0})".format(self.label)
        def __str__(self):
            return "%" + self.label
        def __eq__(self, other):
            return other.__class__ == Name.LABEL and self.label == other.label
        def __hash__(self):
            return hash((self.__class__, self.label))

    def label(self, label):
        return Name(self._prefix, *(self._path + (self.LABEL(label),)))

    @property
    def islabel(self):
        return len(self._path) > 0 and isinstance(self._path[0], Name.LABEL)

    def pulllabel(self):
        return self._path[0].label, Name(self._prefix, *self._path[1:])

    class RUNTIME(object):
        def __init__(self, runtime):
            self.runtime = runtime
        def __repr__(self):
            return "RUNTIME({0})".format(self.runtime)
        def __str__(self):
            return "$" + self.runtime
        def __eq__(self, other):
            return other.__class__ == Name.RUNTIME and self.runtime == other.runtime
        def __hash__(self):
            return hash((self.__class__, self.runtime))

    def runtime(self, runtime):
        return Name(self._prefix, *(self._path + (self.RUNTIME(runtime),)))

    @property
    def isruntime(self):
        return len(self._path) > 0 and isinstance(self._path[0], Name.RUNTIME)

    def pullruntime(self):
        return self._path[0].runtime, Name(self._prefix, *self._path[1:])

    class LIST(object):
        def __repr__(self):
            return "LIST()"
        def __str__(self):
            return "[]"
        def __eq__(self, other):
            return other.__class__ == Name.LIST
        def __hash__(self):
            return hash((self.__class__,))

    def list(self):
        return Name(self._prefix, *(self._path + (self.LIST(),)))

    @property
    def islist(self):
        return len(self._path) > 0 and isinstance(self._path[0], Name.LIST)

    def pulllist(self):
        return Name(self._prefix, *self._path[1:])

    class UNION(object):
        def __repr__(self):
            return "UNION()"
        def __str__(self):
            return "#"
        def __eq__(self, other):
            return other.__class__ == Name.UNION
        def __hash__(self):
            return hash((self.__class__,))

    def union(self):
        return Name(self._prefix, *(self._path + (self.UNION(),)))

    @property
    def isunion(self):
        return len(self._path) > 0 and isinstance(self._path[0], Name.UNION)

    def pullunion(self):
        return Name(self._prefix, *self._path[1:])

    class FIELD(object):
        def __init__(self, field):
            self.field = field
        def __repr__(self):
            return "FIELD({0})".format(self.field)
        def __str__(self):
            return "-" + self.field
        def __eq__(self, other):
            return other.__class__ == Name.FIELD and self.field == other.field
        def __hash__(self):
            return hash((self.__class__, self.field))

    def field(self, field):
        return Name(self._prefix, *(self._path + (self.FIELD(field),)))

    @property
    def isfield(self):
        return len(self._path) > 0 and isinstance(self._path[0], Name.FIELD)

    def pullfield(self):
        return self._path[0].field, Name(self._prefix, *self._path[1:])

    class SIZE(object):
        def __repr__(self):
            return "SIZE()"
        def __str__(self):
            return "@size"
        def __eq__(self, other):
            return other.__class__ == Name.SIZE
        def __hash__(self):
            return hash((self.__class__,))

    def size(self):
        return Name(self._prefix, *(self._path + (self.SIZE(),)))

    @property
    def issize(self):
        return len(self._path) > 0 and isinstance(self._path[-1], Name.SIZE)

    class TAG(object):
        def __repr__(self):
            return "TAG()"
        def __str__(self):
            return "@tag"
        def __eq__(self, other):
            return other.__class__ == Name.TAG
        def __hash__(self):
            return hash((self.__class__,))

    def tag(self):
        return Name(self._prefix, *(self._path + (self.TAG(),)))

    @property
    def istag(self):
        return len(self._path) > 0 and isinstance(self._path[-1], Name.TAG)
        
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
            name = modifiers(tpe, name).list()
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
                n = n.pulllist()
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





    # if name in dtypes:
    #     return identifytype(Primitive(dtypes[name]))

    # elif name + "#" in dtypes:
    #     return identifytype(Primitive(dtypes[name + "#"], nullable=True))

    # elif any(not n.endswith("@size") and (n.startswith(name + "[]") or n.startswith(name + "#[]")) for n in dtypes):
    #     trimmed = dict((name + n[len(name) + 3:], v) for n, v in dtypes.items() if n.startswith(name + "#[]") and n != name + "#[]@size")
    #     if len(trimmed) == 0:
    #         nullable = False
    #         trimmed = dict((name + n[len(name) + 2:], v) for n, v in dtypes.items() if n.startswith(name + "[]") and n != name + "[]@size")
    #     else:
    #         nullable = True
    #     return List(extracttype(trimmed, name), nullable=nullable)    

    # else:
    #     trimmed = dict((n[len(name) + 2:], v) for n, v in dtypes.items() if n.startswith(name + "#-"))
    #     if len(trimmed) == 0:
    #         nullable = False
    #         trimmed = dict((n[len(name) + 1:], v) for n, v in dtypes.items() if n.startswith(name + "-"))
    #     else:
    #         nullable = True

    #     fields = {}
    #     for n in trimmed:
    #         if not n.endswith("@size"):
    #             fn = re.match(r"([^-@[$#]*)", n).group(1)
    #             fields[fn] = extracttype(trimmed, fn)
    #     return Record(fields, nullable=nullable)
