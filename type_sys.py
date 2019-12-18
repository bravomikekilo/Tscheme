from typing import Set


class Type(object):

    def apply(self, subst):
        raise NotImplementedError()

    def ftv(self) -> Set[str]:
        raise NotImplementedError()

    def gen(self, vars: Set[str]):
        vars = list(self.ftv().intersection(vars))
        vars.sort()
        return Schema(self, [TVar(v) for v in vars])

    def find_defined(self, name: str):
        return []


class TVar(Type):

    def __init__(self, v: str):
        super(TVar, self).__init__()
        self.v = v

    def __str__(self):
        return self.v

    def __repr__(self):
        return 'TVar({})'.format(self.v)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def apply(self, subst):
        if self.v in subst:
            return subst[self.v]
        else:
            return self

    def ftv(self):
        return {self.v}


class TConst(Type):

    def __init__(self, name: str):
        super(TConst, self).__init__()
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return 'TConst({})'.format(self.name)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def apply(self, subst):
        return self

    def ftv(self):
        return set()


TYPE_BOOL = TConst("Bool")
TYPE_NUMBER = TConst("Number")
TYPE_STRING = TConst("String")
TYPE_SYMBOL = TConst("Symbol")
TYPE_UNIT = TConst("Unit")


class TArr(Type):

    def __init__(self, in_type: Type, out_type: Type):
        super(TArr, self).__init__()
        self.in_type = in_type
        self.out_type = out_type

    def __str__(self):
        if isinstance(self.in_type, TArr):
            return '({}) -> {}'.format(str(self.in_type), str(self.out_type))
        return '{} -> {}'.format(str(self.in_type), str(self.out_type))

    def __repr__(self):
        return '({})'.format(str(self))

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def apply(self, subst):
        new_in_type = self.in_type.apply(subst)
        new_out_type = self.out_type.apply(subst)
        if new_in_type == self.in_type and new_out_type == self.out_type:
            return self
        else:
            return TArr(new_in_type, new_out_type)

    def ftv(self) -> Set[str]:
        return self.in_type.ftv().union(self.out_type.ftv())


class Tuple(Type):

    def __init__(self, types: [Type]):
        super(Tuple, self).__init__()
        self.types = types

    def __str__(self):
        return '({})'.format(', '.join(str(t) for t in self.types))

    def __repr__(self):
        return 'Tuple({})'.format(', '.join(str(t) for t in self.types))

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def apply(self, subst):
        ok = True
        new_types = []
        for t in self.types:
            new_t = t.apply(subst)
            new_types.append(new_t)
            if new_t != t:
                ok = False
        if ok:
            return self
        else:
            return Tuple(new_types)

    def ftv(self) -> Set[str]:
        ret = set()
        for t in self.types:
            ret = ret.union(t.ftv())
        return ret


class Defined(Type):

    def __init__(self, name: str, types: [Type]):
        super(Defined, self).__init__()
        self.name = name
        self.types = types

    def __str__(self):
        ps = []
        for t in self.types:
            bulk = str(t)
            if isinstance(t, TArr):
                bulk = '({})'.format(bulk)
            if isinstance(t, Defined) and len(t.types) > 0:
                bulk = '({})'.format(bulk)
            ps.append(bulk)
        return "{} {}".format(self.name, ' '.join(ps))

    def __repr__(self):
        return 'Defined[{}]({})'.format(self.name, ', '.join(repr(t) for t in self.types))

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def apply(self, subst):
        ok = True
        new_types = []
        for t in self.types:
            new_t = t.apply(subst)
            new_types.append(new_t)
            if new_t != t:
                ok = False
        if ok:
            return self
        else:
            return Defined(self.name, new_types)

    def ftv(self) -> Set[str]:
        ret = set()
        for t in self.types:
            ret = ret.union(t.ftv())
        return ret

    def find_defined(self, name: str):
        if self.name == name:
            ret = [self]
        else:
            ret = []

        for t in self.types:
            ret.extend(t.find_defined(name))
        return ret


class Schema(object):

    def __init__(self, type: Type, vars: [TVar]):
        super(Schema, self).__init__()
        self.vars = vars
        self.type = type

    def __str__(self):
        vars_str = '.'.join(str(v) for v in self.vars)
        return 'forall {} => {}'.format(vars_str, str(self.type))

    def ftv(self):
        return self.type.ftv().difference(set(v.v for v in self.vars))

    def apply(self, subst):
        ftv = self.ftv()
        ok_subst = {k: v for k, v in subst.items() if k in ftv}
        if len(ok_subst) > 0:
            return Schema(self.type.apply(ok_subst), self.vars)
        else:
            return self

    @staticmethod
    def none(t: Type):
        return Schema(t, [])
