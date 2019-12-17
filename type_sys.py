from typing import Tuple as T
from typing import Mapping, Set
from ir import *
from typing import List


class Type(object):

    def apply(self, subst):
        raise NotImplementedError()

    def ftv(self) -> Set[str]:
        raise NotImplementedError()

    def gen(self, vars: Set[str]):
        vars = list(self.ftv().intersection(vars))
        vars.sort()
        return Schema(self, [TVar(v) for v in vars])


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

class TArr(Type):

    def __init__(self, in_type: Type, out_type: Type):
        super(TArr, self).__init__()
        self.in_type = in_type
        self.out_type = out_type

    def __str__(self):
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


Subst = Mapping[str, Type]
Constraint = T[Type, Type]
Unifer = Subst


class UniException(Exception):

    def __init__(self, why: str):
        super(UniException, self).__init__()
        self.why = why


class TypeMismatchException(UniException):

    def __init__(self, t1: Type, t2: Type):
        error = "type mismatch {}, {}".format(t1, t2)
        super(TypeMismatchException, self).__init__(error)


class RecursiveTypeException(UniException):

    def __init__(self, t1: Type, t2: Type):
        error = "type recursive {}, {}".format(t1, t2)
        super(RecursiveTypeException, self).__init__(error)


def compose(origin: Subst, new: Subst) -> Subst:
    ret = dict()
    for k1, v1 in origin.items():
        if isinstance(v1, TVar):
            if v1.v in new.keys():
                ret[k1] = new[v1.v]
            else:
                ret[k1] = v1.apply(new)
        else:
            ret[k1] = v1.apply(new)

    for k2, v2 in new.items():
        if k2 not in ret.keys():
            ret[k2] = v2
    return ret


def unifies(pairs: [(Type, Type)]) -> Subst:
    lefts = [pair[0] for pair in pairs]
    rights = [pair[1] for pair in pairs]
    ret = dict()
    for i in range(len(pairs)):
        su = unify(lefts[i], rights[i])
        for j in range(i, len(pairs)):
            lefts[j] = lefts[j].apply(su)
            rights[j] = rights[j].apply(su)
        ret = compose(ret, su)
    return ret


def unify(t1: Type, t2: Type) -> Subst:
    if t1 == t2:
        return dict()

    if isinstance(t1, TVar):
        if t1.v in t2.ftv():
            raise RecursiveTypeException(t1, t2)
        return {t1.v: t2}

    if isinstance(t2, TVar):
        if t2.v in t1.ftv():
            raise RecursiveTypeException(t2, t1)
        return {t2.v: t1}

    if isinstance(t1, TArr) and isinstance(t2, TArr):
        return unifies([(t1.in_type, t2.in_type), (t1.out_type, t2.out_type)])

    if isinstance(t1, Tuple) and isinstance(t2, Tuple):
        if len(t1.types) != len(t2.types):
            raise TypeMismatchException(t1, t2)
        pairs = [zip(t1.types, t2.types)]
        return unifies(pairs)

    if isinstance(t1, Defined) and isinstance(t2, Defined):
        if t1.name != t2.name:
            raise TypeMismatchException(t1, t2)
        pairs = [zip(t1.types, t2.types)]
        return unifies(pairs)

    raise TypeMismatchException(t1, t2)


class TypeEnv(object):

    def __init__(self, mapping: Mapping[str, Schema]):
        super(TypeEnv, self).__init__()
        self.internal = mapping

    def get(self, sym: IRVar) -> Schema:
        if sym.v in self.internal:
            return self.internal[sym.v]
        else:
            return None

    def add(self, sym: IRVar, schema: Schema):
        new_mapping = self.internal.copy()
        new_mapping[sym.v] = schema
        return TypeEnv(new_mapping)

    def extend(self, schemas: [(IRVar, Schema)]):
        new_mapping = self.internal.copy()

        new_mapping.update(((sym.v, schema) for (sym, schema) in schemas))
        return TypeEnv(new_mapping)

    def remove(self, sym: IRVar):
        new_mapping = self.internal.copy()
        del new_mapping[sym.v]
        return TypeEnv(new_mapping)

    @staticmethod
    def empty():
        return dict()

    def apply(self, subst):
        new_mapping = {k: v.apply(subst) for k, v in self.internal}
        return TypeEnv(new_mapping)

    def ftv(self) -> Set[str]:
        ret = set()
        for _, v in self.internal.items():
            ret = ret.union(v.ftv())
        return ret


class InferSys(object):

    def __init__(self):
        super(InferSys, self).__init__()
        self.count = 0
        self.equations = []
        self.env = TypeEnv.empty()

    def new_type_var(self):
        count = self.count
        self.count += 1
        ret = [ord('a') + count % 26]
        count //= 26
        while count > 0:
            ret.append(ord('a') + count % 26)
            count //= 26
        ret.reverse()
        return TVar(''.join(chr(c) for c in ret))

    def add_equation(self, left: Type, right: Type):
        print('add equation {} = {}'.format(left, right))
        self.equations.append((left, right))

    def inst(self, schema: Schema):
        new_type_vars = {v.v: self.new_type_var() for v in schema.vars}
        return schema.type.apply(new_type_vars)

    def infer_ir_lit(self, ir_lit: IRLit) -> Type:
        if isinstance(ir_lit, IRInt):
            return TConst("Number")
        elif isinstance(ir_lit, IRFloat):
            return TConst("Number")
        elif isinstance(ir_lit, IRBool):
            return TConst("Bool")
        elif isinstance(ir_lit, IRSymbol):
            return TConst("Symbol")
        elif isinstance(ir_lit, IRString):
            return TConst("String")
        elif isinstance(ir_lit, IRList):
            if len(ir_lit.v) == 0:
                return Defined("List", [self.new_type_var()])
            else:
                subs = [self.infer_ir_lit(t) for t in ir_lit.v]
                for i in range(1, len(ir_lit.v)):
                    self.add_equation(subs[0], subs[i])
                return Defined("List", [subs[0]])
        else:
            raise ValueError("unknown literal type for {}".format(ir_lit))

    def infer_ir_expr(self, env: TypeEnv, ir_expr: IRExpr) -> Type:
        if isinstance(ir_expr, IRLit):
            return self.infer_ir_lit(ir_expr)

        if isinstance(ir_expr, IRVar):
            out = env.get(ir_expr)
            if out is None:
                raise ValueError("unbound symbol {}", ir_expr.v)
            return self.inst(out)

        if isinstance(ir_expr, IRApply):
            ret_type = self.new_type_var()
            out_type = ret_type
            f_type = self.infer_ir_expr(env, ir_expr.f)
            for arg in reversed(ir_expr.args):
                arg_type = self.infer_ir_expr(env, arg)
                out_type = TArr(arg_type, out_type)
            self.add_equation(out_type, f_type)
            return ret_type

        if isinstance(ir_expr, IRLet):
            v = ir_expr.sym
            d = ir_expr.d
            body = ir_expr.e
            d_type = self.infer_ir_expr(env, d)
            subst = unifies(self.equations)
            d_type = d_type.apply(subst)
            new_env = env.add(v, d_type.gen(env.ftv()))

            return self.infer_ir_expr(new_env, body)

        if isinstance(ir_expr, IRLambda):
            args = []
            for arg in ir_expr.args:
                args.append((arg, Schema.none(self.new_type_var())))
            new_env = env.extend(args)
            body_type = self.infer_ir_expr(new_env, ir_expr.body)
            ret = body_type
            for arg, schema in reversed(args):
                ret = TArr(schema.type, ret)
            return ret

        if isinstance(ir_expr, IRIf):
            cond = ir_expr.cond
            then = ir_expr.then
            el = ir_expr.el
            cond_type = self.infer_ir_expr(env, cond)
            then_type = self.infer_ir_expr(env, then)
            el_type = self.infer_ir_expr(env, el)
            self.add_equation(then_type, el_type)
            self.add_equation(cond_type, TYPE_BOOL)
            return el_type

        if isinstance(ir_expr, IRCond):
            conds = ir_expr.conds
            types = [
                (self.infer_ir_expr(env, cond), self.infer_ir_expr(env, arm))
                for cond, arm in conds
            ]
            first_cond_type, first_arm_type = types[0]
            self.add_equation(first_cond_type, TYPE_BOOL)
            for (cond_type, arm_type) in types[1:]:
                self.add_equation(cond_type, TYPE_BOOL)
                self.add_equation(arm_type, first_arm_type)
            return first_arm_type

    def infer_ir_define(self, env: TypeEnv, define: IRDefine) -> Type:
        sym = define.sym
        args = define.args
        body = define.body
        args_type = [self.new_type_var() for _ in args]
        ret_type = self.new_type_var()

        define_type = ret_type
        for arg_type in reversed(args_type):
            define_type = TArr(arg_type, define_type)

        to_env = [(arg, Schema.none(arg_type)) for arg, arg_type in zip(args, args_type)]
        to_env.append((sym, Schema.none(define_type)))

        body_type = self.infer_ir_expr(
            env.extend(to_env),
            body
        )

        self.add_equation(ret_type, body_type)

        return define_type

    def solve_curr_equation(self) -> Subst:
        return unifies(self.equations)

