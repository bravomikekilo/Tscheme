from abc import ABCMeta, abstractmethod

from syntax import *
from type_sys import *


class IRTerm(object, metaclass=ABCMeta):

    @abstractmethod
    def to_raw(self) -> RExpr:
        raise NotImplementedError()

    def to_racket(self, env=None) -> RExpr:
        return self.to_raw()

    @abstractmethod
    def print(self, indent=0) -> [str]:
        raise NotImplementedError()


class IRExpr(IRTerm, metaclass=ABCMeta):
    """
    base class for IRExpr
    """
    def __init__(self):
        super(IRExpr, self).__init__()

    def has_ref(self, syms: Set[str]) -> Set[str]:
        raise NotImplementedError()

class IRVar(IRExpr):

    def __init__(self, v: str):
        super(IRVar, self).__init__()
        self.v = v

    def __str__(self):
        return self.v

    def __hash__(self):
        return hash(self.v)

    def to_raw(self) -> RExpr:
        return RSymbol(self.v)

    def print(self, indent=0) -> [str]:
        return [indent * ' ' + self.v]

    def has_ref(self, syms: Set[str]) -> Set[str]:
        if self.v in syms:
            return {self.v}
        else:
            return set()


class IRApply(IRExpr):

    def __init__(self, f: IRExpr, args: [IRExpr]):
        super(IRApply, self).__init__()
        self.f = f
        self.args = args

    def to_raw(self) -> RExpr:
        head = [self.f.to_raw()]
        head.extend(arg.to_raw() for arg in self.args)
        return RList(head)

    def to_racket(self, env=None) -> RExpr:
        head = [self.f.to_racket()]
        head.extend(arg.to_racket(env=env) for arg in self.args)
        return RList(head)

    def print(self, indent=0) -> [str]:
        headline = indent * ' ' + 'apply'
        ret = [headline]
        f_lines = self.f.print(indent=indent + 2)
        ret.extend(f_lines)
        for arg in self.args:
            ret.extend(arg.print(indent=indent + 2))
        return ret

    def has_ref(self, syms: Set[str]) -> Set[str]:
        ret = self.f.has_ref(syms)
        for arg in self.args:
            ret = ret.union(arg.has_ref(syms))
        return ret


class IRLet(IRExpr):

    def __init__(self, envs: [(IRVar, IRExpr)], body: IRExpr):
        super(IRLet, self).__init__()
        self.envs = envs
        self.body = body

    def to_raw(self) -> RExpr:
        envs = [RList([sym.to_raw(), d.to_raw()]) for sym, d in self.envs]
        return RList([
            RSymbol("let"),
            RList(envs),
            self.body.to_raw()
        ])

    def to_racket(self, env=None) -> RExpr:
        envs = [RList([sym.to_racket(env=env), d.to_racket(env=env)], sq=True) for sym, d in self.envs]
        return RList([
            RSymbol("let"),
            RList(envs),
            self.body.to_racket()
        ])

    def print(self, indent=0) -> [str]:
        headline = indent * ' ' + 'let'
        ret = [headline]
        for (sym, d) in self.envs:
            ret.append(indent * ' ' + sym.v + ' =')
            ret.extend(d.print(indent=indent + 2))
        ret.append(indent * ' ' + 'in')
        ret.extend(self.body.print(indent + 2))
        return ret

    def has_ref(self, syms: Set[str]) -> Set[str]:
        ret = self.body.has_ref(syms)
        binds = [env[0].v for env in self.envs]
        ret = ret.difference(binds)

        for _, d in self.envs:
            ret = ret.union(d.has_ref(syms))
        return ret


class IRIf(IRExpr):

    def __init__(self, cond: IRExpr, then: IRExpr, el: IRExpr):
        super(IRIf, self).__init__()
        self.cond = cond
        self.then = then
        self.el = el

    def to_raw(self) -> RExpr:
        return RList([RSymbol('if'), self.then.to_raw(), self.el.to_raw()])

    def to_racket(self, env=None) -> RExpr:
        return RList([RSymbol('if'), self.then.to_racket(env=env), self.el.to_racket(env=env)])

    def print(self, indent=0) -> [str]:
        headline = indent * ' ' + 'if'
        ret = [headline]
        ret.extend(self.cond.print(indent + 2))
        ret.append(indent * ' ' + 'then')
        ret.extend(self.then.print(indent + 2))
        ret.append(indent * ' ' + 'else')
        ret.extend(self.el.print(indent + 2))
        return ret

    def has_ref(self, syms: Set[str]) -> Set[str]:
        ret = self.cond.has_ref(syms)
        ret = ret.union(self.then.has_ref(syms))
        ret = ret.union(self.el.has_ref(syms))
        return ret


class IRCond(IRExpr):

    def __init__(self, conds: [(IRExpr, IRExpr)]):
        super(IRCond, self).__init__()
        self.conds = conds

    def to_raw(self) -> RExpr:
        conds = [RList([cond.to_raw(), body.to_raw()], sq=True) for (cond, body) in self.conds]
        ret = [RSymbol('cond')]
        ret.extend(conds)
        return RList(ret)

    def to_racket(self, env=None) -> RExpr:
        conds = [RList([cond.to_racket(env=env), body.to_racket(env=env)], sq=True) for (cond, body) in self.conds]
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

    def has_ref(self, syms: Set[str]) -> Set[str]:
        ret = set()
        for cond, arm in self.conds:
            ret = ret.union(cond.has_ref(syms))
            ret = ret.union(arm.has_ref(syms))

        return ret


class IRLambda(IRExpr):

    def __init__(self, args: [IRVar], body: IRExpr):
        super(IRLambda, self).__init__()
        self.args = args
        self.body = body

    def to_raw(self) -> RExpr:
        args = RList(list(arg.to_raw() for arg in self.args))
        return RList([RSymbol("lambda"), args, self.body.to_raw()])

    def to_racket(self, env=None) -> RExpr:
        args = RList(list(arg.to_racket(env=env) for arg in self.args))
        return RList([RSymbol("lambda"), args, self.body.to_racket(env=env)])

    def print(self, indent=0) -> [str]:
        headline = indent * ' ' + 'lambda'
        ret = [headline]
        for arg in self.args:
            ret.extend(arg.print(indent + 2))
        ret.append(indent * ' ' + 'to')
        ret.extend(self.body.print(indent + 2))
        return ret

    def has_ref(self, syms: Set[str]) -> Set[str]:
        ret = self.body.has_ref(syms)
        args = set([arg.v for arg in self.args])
        ret = ret.difference(args)
        return ret


class IRListCtor(IRExpr):

    def __init__(self, args: [IRExpr]):
        super(IRListCtor, self).__init__()
        self.args = args

    def to_raw(self) -> RExpr:
        ret = [RSymbol("list")]
        ret.extend((arg.to_raw() for arg in self.args))
        return RList(ret)

    def to_racket(self, env=None) -> RExpr:
        ret = [RSymbol("list")]
        ret.extend((arg.to_racket(env=env) for arg in self.args))
        return RList(ret)

    def print(self, indent=0) -> [str]:
        headline = indent * ' ' + 'list'
        ret = [headline]
        for arg in self.args:
            ret.extend(arg.print(indent=indent + 2))
        return ret

    def has_ref(self, syms: Set[str]) -> Set[str]:
        ret = set()
        for arg in self.args:
            ret = ret.union(arg.has_ref(syms))
        return ret


class IRTupleCtor(IRExpr):

    def __init__(self, args: [IRExpr]):
        super(IRTupleCtor, self).__init__()
        self.args = args

    def to_raw(self) -> RExpr:
        ret = [RSymbol("tuple")]
        ret.extend((arg.to_raw() for arg in self.args))
        return RList(ret)

    def to_racket(self, env=None) -> RExpr:
        ret = [RSymbol("vector")]
        ret.extend((arg.to_racket(env=env) for arg in self.args))
        return RList(ret)

    def print(self, indent=0) -> [str]:
        headline = indent * ' ' + 'tuple'
        ret = [headline]
        for arg in self.args:
            ret.extend(arg.print(indent=indent + 2))
        return ret

    def has_ref(self, syms: Set[str]) -> Set[str]:
        ret = set()
        for arg in self.args:
            ret = ret.union(arg.has_ref(syms))
        return ret


class IRSet(IRExpr):

    def __init__(self, sym: IRVar, var: IRExpr):
        super(IRSet, self).__init__()
        self.sym = sym
        self.var = var

    def to_raw(self) -> RExpr:
        ret = [RSymbol("set!"), self.sym.to_raw(), self.var.to_raw()]
        return RList(ret)

    def to_racket(self, env=None) -> RExpr:
        ret = [RSymbol("set!"),
               self.sym.to_racket(env=env),
               self.var.to_racket(env=env)]
        return RList(ret)

    def print(self, indent=0) -> [str]:
        headline = indent * ' ' + 'set! {}'.format(self.sym.v)
        ret = [headline]
        ret.extend(self.var.print(indent=indent + 2))
        return ret

    def has_ref(self, syms: Set[str]) -> Set[str]:
        return self.var.has_ref(syms)


class IRBegin(IRExpr):

    def __init__(self, args: [IRExpr]):
        super(IRBegin, self).__init__()
        self.args = args

    def to_raw(self) -> RExpr:
        ret = [RSymbol("begin")]
        ret.extend((arg.to_raw() for arg in self.args))
        return RList(ret)

    def to_racket(self, env=None) -> RExpr:
        ret = [RSymbol("begin")]
        ret.extend((arg.to_racket(env=env) for arg in self.args))
        return RList(ret)

    def print(self, indent=0) -> [str]:
        headline = indent * ' ' + 'begin'
        ret = [headline]
        for arg in self.args:
            ret.extend(arg.print(indent=indent + 2))
        return ret

    def has_ref(self, syms: Set[str]) -> Set[str]:
        ret = set()
        for arg in self.args:
            ret = ret.union(arg.has_ref(syms))
        return ret


class IRDef(IRTerm):

    def print(self, indent=0) -> [str]:
        raise NotImplementedError()

    def to_raw(self) -> RExpr:
        raise NotImplementedError()

    def __init__(self, sym: IRVar, anno: Type):
        super(IRDef, self).__init__()
        self.sym = sym
        self.anno = anno

    def get_name(self):
        raise NotImplementedError()

    def has_ref(self, syms: Set[str]) -> Set[str]:
        raise NotImplementedError()


class IRDefine(IRDef):

    def __init__(self, sym: IRVar, args: [IRVar], body: IRExpr, anno: Type):
        super(IRDefine, self).__init__(sym, anno)
        self.args = args
        self.body = body

    def get_name(self):
        return self.sym.v

    def to_raw(self) -> RExpr:
        head = [self.sym.to_raw()]
        head.extend(var.to_raw() for var in self.args)
        return RList([RSymbol("define"), RList(head), self.body.to_raw()])

    def to_racket(self, env=None) -> RExpr:
        head = [self.sym.to_racket(env=env)]
        head.extend(var.to_racket(env=env) for var in self.args)
        return RList([RSymbol("define"), RList(head), self.body.to_racket(env=env)])

    def print(self, indent=0) -> [str]:
        headline = indent * ' ' + 'define {}'.format(self.sym.v)
        ret = [headline]
        for arg in self.args:
            ret.extend(arg.print(indent + 2))
        ret.append(indent * ' ' + 'to')
        ret.extend(self.body.print(indent + 2))
        return ret

    def has_ref(self, syms: Set[str]) -> Set[str]:
        return self.body.has_ref(syms)


class IRVarDefine(IRDef):

    def __init__(self, sym: IRVar, body: IRExpr, anno: Type):
        super(IRVarDefine, self).__init__(sym, anno)
        self.body = body

    def get_name(self):
        return self.sym.v

    def to_raw(self) -> RExpr:
        ret = [RSymbol('define'), RSymbol(self.sym.v)]
        if self.anno is not None:
            ret.append(self.anno.to_raw())
        ret.append(self.body.to_raw())
        return RList(ret)

    def print(self, indent=0) -> [str]:
        ret = [indent * ' ' + 'define {} to'.format(self.sym.v)]
        ret.extend(self.body.print(indent + 2))
        return ret

    def to_racket(self, env=None) -> RExpr:
        ret = [RSymbol('define'), RSymbol(self.sym.v), self.body.to_racket(env=env)]
        return RList(ret)

    def has_ref(self, sym: Set[str]) -> Set[str]:
        return self.body.has_ref(sym)
