from typing import Tuple as T
from typing import Mapping, Set
from ir import *
from typing import List
from ir_lit import *
from ir_pat import *
from type_sys import *

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
        pairs = list(zip(t1.types, t2.types))
        return unifies(pairs)

    if isinstance(t1, Defined) and isinstance(t2, Defined):
        if t1.name != t2.name:
            raise TypeMismatchException(t1, t2)
        pairs = list(zip(t1.types, t2.types))
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
        return TypeEnv(dict())

    @staticmethod
    def ops_to_env(ops: Mapping[str, Type]):
        tvar_gen = ('t' + str(i) for i in range(1000))
        ret = dict()
        for k, v in ops.items():
            ftv = v.ftv()
            subst = {f: TVar(next(tvar_gen)) for f in ftv}
            ret[k] = Schema(v.apply(subst), list(subst.values()))
        return ret

    @staticmethod
    def default():
        number = TYPE_NUMBER
        bool = TYPE_BOOL

        a = TVar('a')
        b = TVar('b')
        c = TVar('c')
        d = TVar('d')

        def listof(t_var: TVar):
            return Defined("List", [t_var])

        ops = {
            '+': TArr.func(number, number, number),
            '-': TArr.func(number, number, number),
            '*': TArr.func(number, number, number),
            '/': TArr.func(number, number, number),
            '=': TArr.func(number, number, bool),
            '>': TArr.func(number, number, bool),
            '<': TArr.func(number, number, bool),
            'and': TArr.func(bool, bool, bool),
            'or': TArr.func(bool, bool, bool),
            'not': TArr.func(bool, bool),
            'rand': TArr.func(TYPE_UNIT, number),
            'cons': TArr.func(a, listof(a), listof(a)),
            'car': TArr.func(listof(a), a),
            'cdr': TArr.func(listof(a), listof(a)),
            'Cons': TArr.func(a, listof(a), listof(a)),
            'Nil': listof(a),
            'null': listof(a),
            'print': TArr.func(a, TYPE_UNIT),
            'println': TArr.func(a, TYPE_UNIT),
            "read-line": TArr.func(TYPE_UNIT, TYPE_STRING),
        }

        ops = TypeEnv.ops_to_env(ops)

        return TypeEnv(ops)

    def apply(self, subst):
        new_mapping = {k: v.apply(subst) for k, v in self.internal}
        return TypeEnv(new_mapping)

    def ftv(self) -> Set[str]:
        ret = set()
        for _, v in self.internal.items():
            ret = ret.union(v.ftv())
        return ret


class InferSys(object):

    def __init__(self, verbose=False):
        super(InferSys, self).__init__()
        self.count = 0
        self.equations = []
        self.env = TypeEnv.empty()
        self.verbose = verbose

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

    def new_type_vars(self, num):
        return [self.new_type_var() for _ in range(num)]

    def generalize(self, t: Type):
        subst = dict()
        ftv = list(t.ftv())
        ftv.sort()
        ps = set()
        for f_var in ftv:
            p = self.new_type_var()
            subst[f_var] = p
            ps.add(p.v)
        t = t.apply(subst)
        return t.gen(ps)

    def add_equation(self, left: Type, right: Type):
        if self.verbose:
            print('add equation {} = {}'.format(left, right))
        self.equations.append((left, right))

    def add_equations(self, types: [Type]):
        if len(types) == 0:
            return
        ref = types[0]
        for t in types[1:]:
            self.add_equation(ref, t)

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
            if len(ir_expr.args) == 0:
                out_type = TArr(TYPE_UNIT, out_type)
            self.add_equation(out_type, f_type)
            return ret_type

        if isinstance(ir_expr, IRLet):
            new_vars = []
            for (v, d) in ir_expr.envs:
                d_type = self.infer_ir_expr(env, d)
                subst = unifies(self.equations)
                d_type = d_type.apply(subst)
                # new_env = env.add(v, d_type.gen(env.ftv()))
                new_vars.append((v, d_type.gen(env.ftv())))
            new_env = env.extend(new_vars)
            body = ir_expr.body
            return self.infer_ir_expr(new_env, body)

        if isinstance(ir_expr, IRLambda):
            args = []
            for arg in ir_expr.args:
                args.append((arg, Schema.none(self.new_type_var())))
            new_env = env.extend(args)
            if len(ir_expr.args) == 0:
                args.append((None, Schema.none(TYPE_UNIT)))
            body_type = self.infer_ir_expr(new_env, ir_expr.body)
            ret = body_type
            for _, schema in reversed(args):
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

        if isinstance(ir_expr, IRBegin):
            for arg in ir_expr.args:
                arg_type = self.infer_ir_expr(env, arg)

            return arg_type

        if isinstance(ir_expr, IRSet):
            sym_type = self.infer_ir_expr(env, ir_expr.sym)
            var_type = self.infer_ir_expr(env, ir_expr.var)
            self.add_equation(sym_type, var_type)
            return TYPE_UNIT

        if isinstance(ir_expr, IRMatch):
            v_type = self.infer_ir_expr(env, ir_expr.v)
            arm_types = []
            for (pat, arm) in ir_expr.arms:
                pat_type, binds = self.infer_ir_pat(env, pat)
                self.add_equation(v_type, pat_type)
                if len(binds) > 0:
                    pass
                    # print('get bindings from pat:', pat)
                # for t_var, t in binds:
                    # print(t_var, '=>', t)
                binds = [(var, Schema.none(t)) for var, t in binds]
                new_env = env.extend(binds)
                arm_types.append(self.infer_ir_expr(new_env, arm))

            self.add_equations(arm_types)
            return arm_types[0]

        if isinstance(ir_expr, IRListCtor):
            elem_type = None
            elem_types = []
            for elem in ir_expr.args:
                elem_type = self.infer_ir_expr(env, elem)
                elem_types.append(elem_type)

            self.add_equations(elem_types)
            if elem_type is None:
                elem_type = self.new_type_var()

            return Defined("List", [elem_type])

        if isinstance(ir_expr, IRTupleCtor):
            if len(ir_expr.args) == 0:
                return TYPE_UNIT
            else:
                arg_types = [self.infer_ir_expr(env, arg) for arg in ir_expr.args]
                return Tuple(arg_types)

        raise ValueError("unknown ir_expr", ir_expr)

    def infer_ir_pat(self, env: TypeEnv, pat: IRPat) -> (Type, [(TVar, Type)]):

        if isinstance(pat, IRVarPat):
            if pat.var.v == '_':
                return self.new_type_var(), []

            # t = self.infer_ir_expr(env, pat.var)
            t = self.new_type_var()
            return t, [(pat.var, t)]

        if isinstance(pat, IRListPat):
            elem_type = None
            binds = []
            v_types = []
            for v in pat.vs:
                t, v_binds = self.infer_ir_pat(env, v)
                binds.extend(v_binds)
                v_types.append(t)
                elem_type = t
            self.add_equations(v_types)
            if elem_type is None:
                elem_type = self.new_type_var()
            return Defined("List", [elem_type]), binds

        if isinstance(pat, IRTuplePat):
            binds = []
            v_types = []
            for v in pat.vs:
                t, v_binds = self.infer_ir_pat(env, v)
                binds.extend(v_binds)
                v_types.append(t)
            ret_type = Tuple(v_types) if len(v_types) > 0 else TYPE_UNIT
            return ret_type, binds

        if isinstance(pat, IRCtorPat):
            ctor_t = self.infer_ir_expr(env, pat.ctor)
            binds = []
            ret_t = self.new_type_var()
            actual_t = ret_t
            for v in reversed(pat.vs):
                v_t, v_binds = self.infer_ir_pat(env, v)
                actual_t = TArr(v_t, actual_t)
                binds.extend(v_binds)
            self.add_equation(actual_t, ctor_t)
            return ret_t, binds

    def infer_var_define(self, env: TypeEnv, define: IRVarDefine) -> Type:
        sym = define.sym
        body = define.body
        sym_type = self.new_type_var()
        new_env = env.add(sym, Schema.none(sym_type))
        body_type = self.infer_ir_expr(new_env, body)
        # print('var define body type:', body_type)
        self.add_equation(sym_type, body_type)
        return sym_type

    def infer_ir_define(self, env: TypeEnv, define: IRDefine) -> Type:
        sym = define.sym
        args = define.args
        body = define.body
        args_type = [self.new_type_var() for _ in args]
        if len(args_type) == 0:
            args_type.append(TYPE_UNIT)
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

    def solve_ir_expr(self, env: TypeEnv, expr: IRExpr):
        t = self.infer_ir_expr(env, expr)
        subst = self.solve_curr_equation()
        return t.apply(subst)

    def solve_ir_define(self, env: TypeEnv, define: IRDefine):
        t = self.infer_ir_define(env, define)
        subst = self.solve_curr_equation()
        return t.apply(subst)

    def solve_var_define(self, env: TypeEnv, define: IRVarDefine):
        t = self.infer_var_define(env, define)
        subst = self.solve_curr_equation()
        return t.apply(subst)

    def solve_curr_equation(self) -> Subst:
        return unifies(self.equations)


def confirm(infered: Type, anno: Type, subst=None) -> (bool, Mapping[str, TVar]):

    if subst is None:
        subst = dict()

    if anno is None:
        return True, subst

    if isinstance(infered, TVar) and isinstance(anno, TVar):
        if infered.v in subst.keys():
            trans = infered.apply(subst)
            if trans.v != anno.v:
                return False, subst
            else:
                return True, subst
        else:
            subst[infered.v] = anno
            return True, subst

    if isinstance(infered, TConst) and isinstance(anno, TConst):
        if infered.name != anno.name:
            return False, dict()
        else:
            return True, dict()

    if isinstance(infered, TArr) and isinstance(anno, TArr):
        if infered.arity() != anno.arity():
            return False, subst
        else:
            infers = infered.flatten()
            annoes = anno.flatten()

            for infer_t, anno_t in zip(infers, annoes):
                match, subst = confirm(infer_t, anno_t, subst)
                if not match:
                    return False, subst
            return True, subst

    if isinstance(infered, Defined) and isinstance(anno, Defined):
        if infered.arity() != anno.arity() or infered.name != anno.name:
            return False, subst
        else:
            for i, t in enumerate(infered.types):
                match, subst = confirm(t, anno.types[i], subst)
                if not match:
                    return False, subst
            return True, subst

    if isinstance(infered, Tuple) and isinstance(anno, Tuple):
        if infered.arity() != anno.arity():
            return False, subst
        else:
            for i, t in enumerate(infered.types):
                match, subst = confirm(t, anno.types[i], subst)
                if not match:
                    return False, subst

    return False, subst
