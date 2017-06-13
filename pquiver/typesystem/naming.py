import re

identifier = re.compile("^([a-zA-Z_][0-9a-zA-Z_]*)")
indexnumber = re.compile("^([0-9]+)")

class ArrayName(object):
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
        return "ArrayName({0}, {1})".format(repr(self._prefix), repr(self._path))

    def __str__(self):
        return self._prefix + "".join(map(str, self._path))

    def __eq__(self, other):
        return other.__class__ == ArrayName and self._prefix == other._prefix and self._path == other._path

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.__class__, self._prefix, self._path))

    class OPTIONAL(object):
        def __repr__(self):
            return "OPTIONAL()"
        def __str__(self):
            return "?"
        def __eq__(self, other):
            return other.__class__ == ArrayName.OPTIONAL
        def __ne__(self, other):
            return not self.__eq__(other)
        def __hash__(self):
            return hash((self.__class__,))

    def optional(self):
        return ArrayName(self._prefix, *(self._path + (self.OPTIONAL(),)))

    @property
    def isoptional(self):
        return len(self._path) > 0 and isinstance(self._path[0], Name.OPTIONAL)

    def dropoptional(self):
        return ArrayName(self._prefix, *self._path[1:])

    class RUNTIME(object):
        def __init__(self, rtname):
            self.rtname = rtname
        def __repr__(self):
            return "RUNTIME({0})".format(repr(self.rtname))
        def __str__(self):
            return "$" + self.rtname
        def __eq__(self, other):
            return other.__class__ == ArrayName.RUNTIME and self.rtname == other.rtname
        def __ne__(self, other):
            return not self.__eq__(other)
        def __hash__(self):
            return hash((self.__class__, self.rtname))

    def runtime(self, rtname):
        return ArrayName(self._prefix, *(self._path + (ArrayName.RUNTIME(rtname),)))

    @property
    def isruntime(self):
        return len(self._path) > 0 and isinstance(self._path[0], ArrayName.RUNTIME)

    def dropruntime(self):
        return self._path[0].rtname, ArrayName(self._prefix, *self._path[1:])

    class LIST(object):
        def __repr__(self):
            return "LIST()"
        def __str__(self):
            return "[]"
        def __eq__(self, other):
            return other.__class__ == ArrayName.LIST
        def __ne__(self, other):
            return not self.__eq__(other)
        def __hash__(self):
            return hash((self.__class__,))

    def list(self):
        return ArrayName(self._prefix, *(self._path + (self.LIST(),)))

    @property
    def islist(self):
        return len(self._path) > 0 and isinstance(self._path[0], Name.LIST)

    def droplist(self):
        return ArrayName(self._prefix, *self._path[1:])

    class UNION(object):
        def __init__(self, tag):
            self.tag = tag
        def __repr__(self):
            return "UNION({0})".format(self.tag)
        def __str__(self):
            return "{" + repr(self.tag) + "}"
        def __eq__(self, other):
            return other.__class__ == ArrayName.UNION and self.tag == other.tag
        def __ne__(self, other):
            return not self.__eq__(other)
        def __hash__(self):
            return hash((self.__class__, self.tag))

    def union(self, tag):
        return ArrayName(self._prefix, *(self._path + (self.UNION(tag),)))

    @property
    def isunion(self):
        return len(self._path) > 0 and isinstance(self._path[0], Name.UNION)

    def dropunion(self):
        return self._path[0].tag, ArrayName(self._prefix, *self._path[1:])

    class FIELD(object):
        def __init__(self, fname):
            self.fname = fname
        def __repr__(self):
            return "FIELD({0})".format(repr(self.fname))
        def __str__(self):
            return "-" + self.fname
        def __eq__(self, other):
            return other.__class__ == ArrayName.FIELD and self.fname == other.fname
        def __ne__(self, other):
            return not self.__eq__(other)
        def __hash__(self):
            return hash((self.__class__, self.fname))

    def field(self, fname):
        return ArrayName(self._prefix, *(self._path + (ArrayName.FIELD(fname),)))

    @property
    def isfield(self):
        return len(self._path) > 0 and isinstance(self._path[0], ArrayName.FIELD)

    def dropfield(self):
        return self._path[0].fname, ArrayName(self._prefix, *self._path[1:])

    class SIZE(object):
        def __repr__(self):
            return "SIZE()"
        def __str__(self):
            return "@size"
        def __eq__(self, other):
            return other.__class__ == ArrayName.SIZE
        def __ne__(self, other):
            return not self.__eq__(other)
        def __hash__(self):
            return hash((self.__class__,))

    def size(self):
        return ArrayName(self._prefix, *(self._path + (ArrayName.SIZE(),)))

    @property
    def issize(self):
        return len(self._path) > 0 and isinstance(self._path[-1], ArrayName.SIZE)

    class TAG(object):
        def __repr__(self):
            return "TAG()"
        def __str__(self):
            return "@tag"
        def __eq__(self, other):
            return other.__class__ == ArrayName.TAG
        def __ne__(self, other):
            return not self.__eq__(other)
        def __hash__(self):
            return hash((self.__class__,))

    def tag(self):
        return ArrayName(self._prefix, *(self._path + (ArrayName.TAG(),)))

    @property
    def istag(self):
        return len(self._path) > 0 and isinstance(self._path[-1], ArrayName.TAG)

    class PAGE(object):
        def __init__(self, number):
            self.number = number
        def __repr__(self):
            return "PAGE({0})".format(self.number)
        def __str__(self):
            return "#{0}".format(self.number)
        def __eq__(self, other):
            return other.__class__ == ArrayName.PAGE
        def __ne__(self, other):
            return not self.__eq__(other)
        def __hash__(self):
            return hash((self.__class__, self.number))

    def page(self, number):
        return ArrayName(self._prefix, *(self._path + (ArrayName.PAGE(number),)))

    @property
    def ispage(self):
        return len(self._path) > 0 and isinstance(self._path[-1], ArrayName.PAGE)

    @staticmethod
    def parse(prefix, string):
        if not string.startswith(prefix):
            return None

        path = []
        string = string[len(prefix):]
        expecttype = True
        expectsize = False
        expecttag = False

        while len(string) > 0:
            if expecttype and string[0] == "?":
                string = string[1:]
                path.append(ArrayName.OPTIONAL())

            elif expecttype and string[0] == "$":
                m = re.match(identifier, string[1:])
                if m is None:
                    raise ValueError("\"$\" in string \"{0}\" must be followed by an identifier /{1}/".format(string, identifier.pattern))
                rtname = m.group(1)
                string = string[m.end(1) + 1 : ]
                path.append(ArrayName.RUNTIME(rtname))

            elif expecttype and string[0:2] == "[]":
                string = string[2:]
                expectsize = True
                path.append(ArrayName.LIST())

            elif expecttype and string[0] == "{":
                m = re.match(indexnumber, string[1:])
                if m is None:
                    raise ValueError("\"{{\" in string \"{0}\" must be followed by an index number /{1}/".format(string, indexnumber.pattern))
                if string[m.end(1) : m.end(1) + 1] != "}":
                    raise ValueError("\"{{\" in string \"{0}\" must be closed by a \"}}\" after the index number".format(string))
                number = int(m.group(1))
                string = string[m.end(1) + 2 : ]
                expecttag = True
                path.append(ArrayName.UNION(number))

            elif expecttype and string[0] == "-":
                m = re.match(ArrayName.identifier, string[1:])
                if m is None:
                    raise ValueError("\"-\" in string \"{0}\" must be followed by an identifier /{1}/".format(string, identifier.pattern))
                fname = m.group(1)
                string = string[m.end(1) + 1 : ]
                path.append(ArrayName.FIELD(fname))

            elif expecttype and expectsize and string.startswith("@size"):
                string = string[5:]
                expecttype = False
                path.append(ArrayName.SIZE())

            elif expecttype and expecttag and string.startswith("@tag"):
                string = string[4:]
                expecttype = False
                path.append(ArrayName.SIZE())

            elif string[0] == "#":
                m = re.match(indexnumber, string[1:])
                if m is None:
                    raise ValueError("\"#\" in string \"{0}\" must be followed by an index number /{1}/".format(string, indexnumber.pattern))
                number = int(m.group(1))
                string = string[m.end(1) + 1 : ]
                path.append(ArrayName.PAGE(number))
                if string != "":
                    raise ValueError("unexpected content after page number: \"{0}\"".format(string))

            else:
                raise ValueError("unexpected content \"{0}\" with expecttype = {1}, expectsize = {2}, expecttag = {3}".format(string, expecttype, expectsize, expecttag))

        return ArrayName(prefix, *path)
