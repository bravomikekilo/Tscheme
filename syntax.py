class Formatter(object):

    def __init__(self, indent_width=2):
        super(Formatter, self).__init__()
        self.indent_width = indent_width
        self.stack = []
        self.lines = []
        self.curr_line = []
        self.curr_line_width = 0
        self.should_fold = False

    def add_whitespace(self):
        self.curr_line.append(' ')
        self.curr_line_width += 1

    def set_anchor(self, deepth=None):
        if deepth is None:
            self.stack.append(self.curr_line_width)

    def get_anchor(self):
        if len(self.stack) == 0:
            return 0
        else:
            return self.stack[-1]

    def pop_anchor(self):
        return self.stack.pop()

    def add_token(self, token):
        length = len(token)

        if token == ']' or token == ')':
            self.should_fold = True
            self.curr_line.append(token)
            self.curr_line_width += length
            self.stack.pop()
            return

        if self.should_fold:
            self.should_fold = False
            self.lines.append(''.join(self.curr_line))
            self.curr_line = []
            self.curr_line_width = 0
            indent = self.stack[-1] + self.indent_width
            self.curr_line.append(' ' * indent)

        if token == "'(" or \
                token == '(' or \
                token == '[' or \
                token == "'[":
            self.stack.append(self.curr_line_width)

        self.curr_line.append(token)
        self.curr_line_width += length
        return

    def to_str(self):
        if len(self.curr_line) > 0:
            self.lines.append(''.join(self.curr_line))
        return '\n'.join(self.lines)


class RExpr(object):
    def __init__(self):
        super(RExpr, self).__init__()

    def to_stream(self, stream: Formatter):
        return stream.add_token(str(self))

    def pretty_print(self, indent_width=2):
        stream = Formatter(indent_width=indent_width)
        self.to_stream(stream)
        return stream.to_str()


class RSymbol(RExpr):
    def __init__(self, v: str):
        super(RSymbol, self).__init__()
        self.v = v

    def __str__(self):
        return self.v

    def __repr__(self):
        return "RSymbol[{}]".format(self.__str__())

    def to_stream(self, stream: Formatter):
        stream.add_token(self.v)


class RString(RExpr):

    def __init__(self, v: str):
        super(RString, self).__init__()
        self.v = v

    def __str__(self):
        return repr(self.v)

    def __repr__(self):
        return 'RString[{}]'.format(repr(self.v))


class RFloat(RExpr):

    def __init__(self, v: float):
        super(RFloat, self).__init__()
        self.v = v

    def __str__(self):
        return str(self.v)

    def __repr__(self):
        return "RFloat[{}]".format(self.__str__())


class RInt(RExpr):

    def __init__(self, v: int):
        super(RInt, self).__init__()
        self.v = v

    def __str__(self):
        return str(self.v)

    def __repr__(self):
        return "RFloat[{}]".format(self.__str__())


class RBool(RExpr):

    def __init__(self, v: bool):
        super(RBool, self).__init__()
        self.v = v

    def __str__(self):
        if self.v:
            return "#t"
        else:
            return "#f"

    def __repr__(self):
        return "RBool[{}]".format(self.__str__())


class RList(RExpr):

    def __init__(self, v: [RExpr], sq=False):
        super(RList, self).__init__()
        self.v = v
        self.sq = sq

    def __str__(self):
        bulk = ' '.join([str(elem) for elem in self.v])
        if self.sq:
            return '[{}]'.format(bulk)
        else:
            return '({})'.format(bulk)

    def __repr__(self):
        bulk = ' '.join([repr(elem) for elem in self.v])
        return "RList[{}]".format(bulk)

    def to_stream(self, stream: Formatter):
        if len(self.v) == 2 and isinstance(self.v[0], RSymbol):
            if self.v[0].v == 'quote':
                stream.add_token("'")
                self.v[1].to_stream(stream)
                return

        stream.add_token('[' if self.sq else '(')
        if len(self.v) > 0:
            self.v[0].to_stream(stream)
        for v in self.v[1:]:
            stream.add_whitespace()
            v.to_stream(stream)
        stream.add_token(']' if self.sq else ')')
        return


def quote(expr: RExpr) -> RList:
    return RList([RSymbol('quote'), expr])
