

class RExpr(object):
    def __init__(self):
        super(RExpr, self).__init__()


class RSymbol(RExpr):
    def __init__(self, v: str):
        super(RSymbol, self).__init__()
        self.v = v

    def __str__(self):
        return self.v

    def __repr__(self):
        return "RSymbol[{}]".format(self.__str__())


class RString(RExpr):

    def __init__(self, v: str):
        super(RString, self).__init__()
        self.v = v

    def __str__(self):
        return '"{}"'.format(self.v)

    def __repr__(self):
        return 'RString["{}"]'.format(self.v)


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

    def __init__(self, v: [RExpr]):
        super(RList, self).__init__()
        self.v = v

    def __str__(self):
        bulk = ' '.join([str(elem) for elem in self.v])
        return '({})'.format(bulk)

    def __repr__(self):
        bulk = ' '.join([repr(elem) for elem in self.v])
        return "RList[{}]".format(bulk)

