from syntax import *


class IRTerm(object):

    def to_raw(self) -> RExpr:
        raise NotImplementedError()

    def print(self, indent=0) -> [str]:
        raise NotImplementedError()


class IRExpr(IRTerm):
    """
    base class for IRExpr
    """
    def __init__(self):
        super(IRExpr, self).__init__()

    def to_raw(self) -> RExpr:
        raise NotImplementedError()


class IRVar(IRExpr):

    def __init__(self, v: str):
        super(IRVar, self).__init__()
        self.v = v

    def __str__(self):
        return 'IRVar()'.format(self.v)

    def to_raw(self) -> RExpr:
        return RSymbol(self.v)

    def print(self, indent=0) -> [str]:
        return [indent * ' ' + self.v]


class IRApply(IRExpr):

    def __init__(self, f: IRExpr, args: [IRExpr]):
        super(IRApply, self).__init__()
        self.f = f
        self.args = args

    def to_raw(self) -> RExpr:
        head = [self.f.to_raw()]
        head.extend(arg.to_raw() for arg in self.args)
        return RList(head)

    def print(self, indent=0) -> [str]:
        headline = indent * ' ' + 'apply'
        ret = [headline]
        f_lines = self.f.print(indent=indent + 2)
        ret.extend(f_lines)
        for arg in self.args:
            ret.extend(arg.print(indent=indent + 2))
        return ret


class IRLet(IRExpr):

    def __init__(self, sym: IRVar, d: IRExpr, e: IRExpr):
        super(IRLet, self).__init__()
        self.sym = sym
        self.d = d
        self.e = e

    def to_raw(self) -> RExpr:
        return RList([
            RSymbol("let"),
            RList([self.sym.to_raw(), self.d.to_raw()]),
            self.e.to_raw()
        ])

    def print(self, indent=0) -> [str]:
        headline = indent * ' ' + 'let {} ='.format(self.sym.v)
        ret = [headline]
        ret.extend(self.d.print(indent + 2))
        ret.append(indent * ' ' + 'in')
        ret.extend(self.e.print(indent + 2))
        return ret


class IRIf(IRExpr):

    def __init__(self, cond: IRExpr, then: IRExpr, el: IRExpr):
        super(IRIf, self).__init__()
        self.cond = cond
        self.then = then
        self.el = el

    def to_raw(self) -> RExpr:
        return RList([RSymbol('if'), self.then.to_raw(), self.el.to_raw()])

    def print(self, indent=0) -> [str]:
        headline = indent * ' ' + 'if'
        ret = [headline]
        ret.extend(self.cond.print(indent + 2))
        ret.append(indent * ' ' + 'then')
        ret.extend(self.then.print(indent + 2))
        ret.append(indent * ' ' + 'else')
        ret.extend(self.el.print(indent + 2))
        return ret


class IRCond(IRExpr):

    def __init__(self, conds: [(IRExpr, IRExpr)]):
        super(IRCond, self).__init__()
        self.conds = conds

    def to_raw(self) -> RExpr:
        conds = [RList([cond.to_raw(), body.to_raw()]) for (cond, body) in self.conds]
        ret = [RSymbol('cond')]
        ret.extend(conds)
        return RList(ret)

    @staticmethod
    def print_arm(cond: IRExpr, arm: IRExpr, indent):
        ret = []
        ret.extend(cond.print(indent + 2))
        ret.append(' ' * indent + '->')
        ret.extend(arm.print(indent + 2))
        return ret

    def print(self, indent=0) -> [str]:
        headline = indent * ' ' + 'cond'
        ret = [headline]
        for (cond, arm) in self.conds:
            ret.extend(self.print_arm(cond, arm, indent + 2))
        return ret


class IRLambda(IRExpr):

    def __init__(self, args: [IRVar], body: IRExpr):
        super(IRLambda, self).__init__()
        self.args = args
        self.body = body

    def to_raw(self) -> RExpr:
        args = RList(list(arg.to_raw() for arg in self.args))
        return RList([RSymbol("lambda"), args, self.body.to_raw()])

    def print(self, indent=0) -> [str]:
        headline = indent * ' ' + 'lambda'
        ret = [headline]
        for arg in self.args:
            ret.extend(arg.print(indent + 2))
        ret.append(indent * ' ' + 'to')
        ret.extend(self.body.print(indent + 2))
        return ret


class IRListCtor(IRExpr):

    def __init__(self, args: [IRExpr]):
        super(IRListCtor, self).__init__()
        self.args = args

    def to_raw(self) -> RExpr:
        ret = [RSymbol("list")]
        ret.extend((arg.to_raw() for arg in self.args))
        return RList(ret)

    def print(self, indent=0) -> [str]:
        headline = indent * ' ' + 'list'
        ret = [headline]
        for arg in self.args:
            ret.extend(arg.print(indent=indent + 2))
        return ret


class IRTupleCtor(IRExpr):

    def __init__(self, args: [IRExpr]):
        super(IRTupleCtor, self).__init__()
        self.args = args

    def to_raw(self) -> RExpr:
        ret = [RSymbol("tuple")]
        ret.extend((arg.to_raw() for arg in self.args))
        return RList(ret)

    def print(self, indent=0) -> [str]:
        headline = indent * ' ' + 'tuple'
        ret = [headline]
        for arg in self.args:
            ret.extend(arg.print(indent=indent + 2))
        return ret


class IRSet(IRExpr):

    def __init__(self, sym: IRVar, var: IRExpr):
        super(IRSet, self).__init__()
        self.sym = sym
        self.var = var

    def to_raw(self) -> RExpr:
        ret = [RSymbol("set!"), self.sym.to_raw(), self.var.to_raw()]
        return RList(ret)

    def print(self, indent=0) -> [str]:
        headline = indent * ' ' + 'set! {}'.format(self.sym.v)
        ret = [headline]
        ret.extend(self.var.print(indent=indent + 2))
        return ret


class IRBegin(IRExpr):

    def __init__(self, args: [IRExpr]):
        super(IRBegin, self).__init__()
        self.args = args

    def to_raw(self) -> RExpr:
        ret = [RSymbol("begin!")]
        ret.extend((arg.to_raw() for arg in self.args))
        return RList(ret)

    def print(self, indent=0) -> [str]:
        headline = indent * ' ' + 'begin'
        ret = [headline]
        for arg in self.args:
            ret.extend(arg.print(indent=indent + 2))
        return ret


class IRDefine(IRTerm):

    def __init__(self, sym: IRVar, args: [IRVar], body: IRExpr):
        super(IRDefine, self).__init__()
        self.sym = sym
        self.args = args
        self.body = body

    def to_raw(self) -> RExpr:
        head = [self.sym]
        head.extend(var.to_raw() for var in self.args)
        return RList([RSymbol("define"), RList(head), self.body.to_raw()])

    def print(self, indent=0) -> [str]:
        headline = indent * ' ' + 'define {}'.format(self.sym.v)
        ret = [headline]
        for arg in self.args:
            ret.extend(arg.print(indent + 2))
        ret.append(indent * ' ' + 'to')
        ret.extend(self.body.print(indent + 2))
        return ret


