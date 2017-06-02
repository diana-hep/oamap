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