from ir import *


class IRLit(IRExpr):

    def __init__(self):
        super(IRLit, self).__init__()

    def to_lit(self) -> RExpr:
        raise NotImplementedError()

    def print(self, indent=0) -> [str]:
        raise NotImplementedError()

    def to_raw(self) -> RExpr:
        return self.to_lit()


class IRInt(IRLit):
    def __init__(self, v: int):
        super(IRInt, self).__init__()
        self.v = v

    def to_lit(self) -> RExpr:
        return RInt(self.v)

    def print(self, indent=0) -> [str]:
        return [' ' * indent + str(self.v)]


class IRBool(IRLit):
    def __init__(self, v: bool):
        super(IRBool, self).__init__()
        self.v = v

    def to_lit(self) -> RExpr:
        return RBool(self.v)

    def print(self, indent=0) -> [str]:
        return [' ' * indent + ("#t" if self.v else "#f")]


class IRFloat(IRLit):

    def __init__(self, v: float):
        super(IRFloat, self).__init__()
        self.v = v

    def to_lit(self) -> RExpr:
        return RFloat(self.v)

    def print(self, indent=0) -> [str]:
        return [' ' * indent + str(self.v)]


class IRSymbol(IRLit):

    def __init__(self, v: str):
        super(IRSymbol, self).__init__()
        self.v = v

    def to_lit(self) -> RExpr:
        return RSymbol(self.v)

    def to_raw(self) -> RExpr:
        return RList([RSymbol('quote'), RSymbol(self.v)])

    def print(self, indent=0) -> [str]:
        return [' ' * indent + "'" + str(self.v)]


class IRString(IRLit):

    def __init__(self, v: str):
        super(IRString, self).__init__()
        self.v = v

    def to_lit(self) -> RExpr:
        return RString(self.v)

    def print(self, indent=0) -> [str]:
        return [' ' * indent + repr(self.v)]


class IRChar(IRLit):

    def __init__(self, v: str):
        super(IRChar, self).__init__()
        self.v = v

    def to_lit(self) -> RExpr:
        return RChar(self.v)

    def print(self, indent=0) -> [str]:
        return [' ' * indent + repr(self.v)]


class IRList(IRLit):

    def __init__(self, v: [IRLit], sq=False):
        super(IRList, self).__init__()
        self.v = v
        self.sq = sq

    def to_lit(self) -> RExpr:
        return RList([lit.to_lit() for lit in self.v], sq=self.sq)

    def to_raw(self) -> RExpr:
        return RList([RSymbol("quote"), self.to_lit()])

    def print(self, indent=0) -> [str]:
        ret = [' ' * indent + '[']
        for lit in self.v:
            out = lit.print(indent=indent + 2)
            ret.extend(out)
        ret.append(' ' * indent + ']')
        return ret
