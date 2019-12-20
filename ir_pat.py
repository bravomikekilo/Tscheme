from ir_lit import *


class IRPat(IRTerm):

    def __init__(self):
        super(IRPat, self).__init__()

    def to_raw(self) -> RExpr:
        raise NotImplementedError()

    def print(self, indent=0) -> [str]:
        raise NotImplementedError()


class IRVarPat(IRPat):

    def __init__(self, var: IRVar):
        super(IRVarPat, self).__init__()
        self.var = var

    def to_raw(self) -> RExpr:
        return self.var.to_raw()

    def print(self, indent=0) -> [str]:
        return self.var.print(indent=indent)


class IRListPat(IRPat):

    def __init__(self, vs: [IRPat]):
        super(IRListPat, self).__init__()
        self.vs = vs

    def to_raw(self) -> RExpr:
        ret = [RSymbol('list')]
        for v in self.vs:
            ret.append(v.to_raw())
        return RList(ret)

    def to_racket(self, env=None) -> RExpr:
        ret = [RSymbol('list')]
        for v in self.vs:
            ret.append(v.to_racket(env=env))
        return RList(ret)

    def print(self, indent=0) -> [str]:
        headline = indent * ' ' + 'list'
        ret = [headline]
        for v in self.vs:
            ret.extend(v.print(indent=indent + 2))
        return ret


class IRTuplePat(IRPat):

    def __init__(self, vs: [IRPat]):
        super(IRTuplePat, self).__init__()
        self.vs = vs

    def to_raw(self) -> RExpr:
        ret = [RSymbol('tuple')]
        for v in self.vs:
            ret.append(v.to_raw())
        return RList(ret)

    def to_racket(self, env=None) -> RExpr:
        ret = [RSymbol('vector')]
        for v in self.vs:
            ret.append(v.to_racket(env=env))
        return RList(ret)

    def print(self, indent=0) -> [str]:
        headline = indent * ' ' + 'tuple'
        ret = [headline]
        for v in self.vs:
            ret.extend(v.print(indent=indent + 2))
        return ret


class IRCtorPat(IRPat):

    def __init__(self, ctor: IRVar, vs: [IRPat]):
        super(IRCtorPat, self).__init__()
        self.ctor = ctor
        self.vs = vs

    def to_raw(self) -> RExpr:
        ret = [RSymbol(self.ctor.v)]
        for v in self.vs:
            ret.append(v.to_raw())
        return RList(ret)

    def to_racket(self, env=None) -> RExpr:
        ctor_name = self.ctor.v

        if env is not None:
            record_names = env.record_names
            if ctor_name in record_names:
                ret = [RSymbol('vector')]
                for v in self.vs:
                    ret.append(v.to_racket(env=env))
                return RList(ret)

        if ctor_name == 'Cons':
            ret = [RSymbol('cons')]
        elif ctor_name == 'Nil':
            return quote(RList([]))
        else:
            ret = [RSymbol('list'), quote(RSymbol(ctor_name))]
        for v in self.vs:
            ret.append(v.to_racket())
        return RList(ret)

    def print(self, indent=0) -> [str]:
        headline = indent * ' ' + self.ctor.v
        ret = [headline]
        for v in self.vs:
            ret.extend(v.print(indent=indent + 2))
        return ret


class IRLitPat(IRPat):

    def __init__(self, lit: IRLit):
        super(IRLitPat, self).__init__()
        self.lit = lit

    def to_raw(self) -> RExpr:
        return self.lit.to_raw()

    def print(self, indent=0) -> [str]:
        return self.lit.print(indent=indent)


class IRMatch(IRExpr):

    def __init__(self, v: IRExpr, arms: [(IRPat, IRExpr)]):
        super(IRMatch, self).__init__()
        self.v = v
        self.arms = arms

    def to_raw(self) -> RExpr:
        ret = [RSymbol("match"), self.v.to_raw()]
        for pat, arm in self.arms:
            ret.append(RList([pat.to_raw(), arm.to_raw()], sq=True))
        return RList(ret)

    def to_racket(self, env=None) -> RExpr:
        ret = [RSymbol("match"), self.v.to_racket(env=env)]
        for pat, arm in self.arms:
            ret.append(RList([pat.to_racket(env=env), arm.to_racket(env=env)], sq=True))
        return RList(ret)

    def print(self, indent=0) -> [str]:
        headline = indent * ' ' + 'match'
        ret = [headline]
        ret.extend(self.v.print(indent=indent + 2))

        for (pat, arm) in self.arms:
            ret.append(indent * ' ' + '[')
            ret.extend(pat.print(indent=indent + 2))
            ret.append(indent * ' ' + '->')
            ret.extend(arm.print(indent=indent + 2))
            ret.append(indent * ' ' + ']')
        return ret

