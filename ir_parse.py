from ir import *
from ir_lit import *
from ir_pat import *
from type_sys import *
from typing import Mapping
from collections import OrderedDict


def parse_lit(expr: RExpr) -> IRLit:
    if isinstance(expr, RSymbol):
        return IRSymbol(expr.v)
    elif isinstance(expr, RFloat):
        return IRFloat(expr.v)
    elif isinstance(expr, RInt):
        return IRInt(expr.v)
    elif isinstance(expr, RBool):
        return IRBool(expr.v)
    elif isinstance(expr, RString):
        return IRString(expr.v)
    else:
        raise ValueError('expr {} is not a literal'.format(expr))


def parse_lambda(r_expr: RList) -> (IRExpr, [str]):
    errors = []
    lam = None
    if len(r_expr.v) != 3:
        errors.append("wrong arity of lambda form")
        return None, errors
    args = r_expr.v[1]
    body = r_expr.v[2]

    if not isinstance(args, RList):
        errors.append("wrong form of lambda parameters")
        return None, errors
    else:
        vars = []
        for arg in args.v:
            if isinstance(arg, RSymbol):
                vars.append(IRVar(arg.v))
            else:
                errors.append("error in lambda parameters, form is not a symbol")
        ret, ret_errors = parse_ir_expr(body)
        errors.extend(ret_errors)
        lam = IRLambda(vars, ret)

    return lam, errors


def parse_let(r_expr: RList) -> (IRExpr, [str]):
    errors = []
    let = None
    if len(r_expr.v) != 3:
        errors.append("wrong arity of let form")
        return let, errors
    r_env = r_expr.v[1]
    r_body = r_expr.v[2]

    if not isinstance(r_env, RList):
        errors.append("error in let env, form is not a list")
    else:
        if len(r_env.v) != 2:
            errors.append("wrong arity in let env")
            v = None
            d = None
        else:
            r_v = r_env.v[0]
            r_d = r_env.v[1]
            if not isinstance(r_v, RSymbol):
                errors.append("binding must on a symbol")
                v = None
            else:
                v = IRVar(r_v.v)

            d, d_error = parse_ir_expr(r_d)
            errors.extend(d_error)
        body, body_error = parse_ir_expr(r_body)
        errors.extend(body_error)
        let = IRLet(v, d, body)

    return let, errors


def parse_if(r_expr: RList) -> (IRExpr, [str]):
    errors = []
    iff = None
    if len(r_expr.v) != 4:
        errors.append("wrong arity in if form")
        return iff, errors
    r_cond = r_expr.v[1]
    r_then = r_expr.v[2]
    r_else = r_expr.v[3]

    cond, cond_errors = parse_ir_expr(r_cond)
    errors.extend(cond_errors)

    then, then_errors = parse_ir_expr(r_then)
    errors.extend(then_errors)

    el, else_errors = parse_ir_expr(r_else)
    errors.extend(else_errors)

    iff = IRIf(cond, then, el)

    return iff, errors


def parse_cond_arm(r_expr: RList) -> ((IRExpr, IRExpr), [str]):
    errors = []
    cond = None
    arm = None
    if len(r_expr.v) != 2:
        errors.append("wrong arity in cond arm")
        return (cond, arm), errors
    cond, cond_errors = parse_ir_expr(r_expr.v[0])
    errors.extend(cond_errors)

    arm, arm_errors = parse_ir_expr(r_expr.v[1])
    errors.extend(arm_errors)

    return (cond, arm), errors


def parse_cond(r_expr: RList) -> (IRExpr, [str]):
    errors = []
    cond = None
    if len(r_expr.v) < 2:
        errors.append("wrong arity in cond form")
        return cond, errors
    r_conds = r_expr.v[1:]

    conds = []
    for r_cond in r_conds:
        if isinstance(r_cond, RList):
            (cond, arm), cond_errors = parse_cond_arm(r_cond)
            errors.extend(cond_errors)
            conds.append((cond, arm))
        else:
            errors.append("cond arm must be a list")
    cond = IRCond(conds)

    return cond, errors


def parse_apply(r_expr: RList) -> (IRExpr, [str]):
    errors = []
    expr = None

    if len(r_expr.v) == 0:
        errors.append("empty application on top level, error")
        return None, errors
    r_head = r_expr.v[0]

    expr_head, head_errors = parse_ir_expr(r_head)
    if isinstance(expr_head, IRSymbol):
        expr_head = IRVar(expr_head.v)
    errors.extend(head_errors)
    expr_args = []
    for arg in r_expr.v[1:]:
        expr_arg, arg_errors = parse_ir_expr(arg)
        expr_args.append(expr_arg)
        errors.extend(arg_errors)
    expr = IRApply(expr_head, expr_args)
    return expr, errors


def parse_pat(r_expr: RExpr) -> (IRPat, [str]):
    errors = []
    pat = None

    if isinstance(r_expr, RList):
        if len(r_expr.v) == 0:
            errors.append("pattern can't be empty")
            return pat, errors

        head = r_expr.v[0]
        if isinstance(head, RSymbol):
            sym = head.v
            if sym == 'quote':
                if len(r_expr.v) != 2:
                    errors.append("wrong arity in quote")
                    return pat, errors
                lit, errors = parse_lit(r_expr.v[1])
                pat = IRLitPat(lit)
                return pat, errors

            if sym == 'list':
                # list pattern
                subs = []
                for r_sub in r_expr.v[1:]:
                    sub, sub_errors = parse_pat(r_sub)
                    subs.append(sub)
                    errors.extend(sub_errors)
                pat = IRListPat(subs)
                return pat, errors

            if sym == 'tuple':
                # tuple pattern
                subs = []
                for r_sub in r_expr.v[1:]:
                    sub, sub_errors = parse_pat(r_sub)
                    subs.append(sub)
                    errors.extend(sub_errors)
                pat = IRTuplePat(subs)
                return pat, errors

            # ctor pattern
            ctor = IRVar(sym)
            subs = []
            for r_sub in r_expr.v[1:]:
                sub, sub_errors = parse_pat(r_sub)
                subs.append(sub)
                errors.extend(sub_errors)
            pat = IRCtorPat(ctor, subs)
            return pat, errors

        else:
            errors.append("pattern head should be a symbol")
            return pat, errors
    else:
        lit = parse_lit(r_expr)
        # errors.extend(lit_errors)
        if isinstance(lit, IRSymbol):
            pat = IRVarPat(IRVar(lit.v))
        else:
            pat = IRLitPat(lit)

    return pat, errors


def parse_match(r_expr: RList) -> (IRExpr, [str]):
    errors = []
    match = None

    if len(r_expr.v) < 3:
        errors.append("match form must have matched expression and at least one match arm")
        return match, errors
    v, v_errors = parse_ir_expr(r_expr.v[1])
    errors.extend(v_errors)
    arms = []
    for r_branch in r_expr.v[2:]:
        if isinstance(r_branch, RList):
            if len(r_branch.v) != 2:
                errors.append("wrong arity in match arm")
                continue
            r_pat = r_branch.v[0]
            r_arm = r_branch.v[1]
            pat, pat_errors = parse_pat(r_pat)
            arm, atm_errors = parse_ir_expr(r_arm)
            arms.append((pat, arm))
        else:
            errors.append("match arm must be a list")
            continue
    pat = IRMatch(v, arms)
    return pat, errors


def parse_list_form(r_expr: RList) -> (IRExpr, [str]):
    errors = []

    r_args = r_expr.v[1:]
    args = []
    for r_arg in r_args:
        arg, arg_errors = parse_ir_expr(r_arg)
        args.append(arg)
        errors.extend(arg_errors)

    return IRListCtor(args), errors


def parse_tuple_form(r_expr: RList) -> (IRExpr, [str]):
    errors = []

    r_args = r_expr.v[1:]
    args = []
    for r_arg in r_args:
        arg, arg_errors = parse_ir_expr(r_arg)
        args.append(arg)
        errors.extend(arg_errors)

    return IRTupleCtor(args), errors


def parse_set(r_expr: RList) -> (IRExpr, [str]):
    errors = []
    form = None
    if len(r_expr.v) != 3:
        errors.append("wrong arity in set! form")
        return form, errors
    r_sym = r_expr.v[1]
    r_v = r_expr.v[2]

    if not isinstance(r_sym, RSymbol):
        errors.append("must set! on a symbol")
        return form, errors
    sym = IRVar(r_sym.v)
    v, v_errors = parse_ir_expr(r_v)
    errors.extend(v_errors)
    form = IRSet(sym, v)
    return form, errors


def parse_begin(r_expr: RList) -> (IRExpr, [str]):
    errors = []

    if len(r_expr.v) == 1:
        errors.append('there must be at least one form in begin')
        return None, errors

    r_args = r_expr.v[1:]
    args = []
    for r_arg in r_args:
        arg, arg_errors = parse_ir_expr(r_arg)
        args.append(arg)
        errors.extend(arg_errors)

    return IRBegin(args), errors


def parse_ir_expr(r_expr) -> (IRExpr, [str]):
    errors = []
    expr = None
    if isinstance(r_expr, RList):
        if len(r_expr.v) == 0:
            errors.append("empty application on top level, error")
            return expr, errors
        r_head = r_expr.v[0]
        if isinstance(r_head, RSymbol):
            sym = r_head.v
            if sym == 'lambda':
                # parse a lambda
                expr, lam_errors = parse_lambda(r_expr)
                errors.extend(lam_errors)
                return expr, errors
            if sym == 'quote':
                # parse a quote
                if len(r_expr.v) != 2:
                    errors.append("wrong arity in quote form")
                    return expr, errors
                else:
                    expr, quote_errors = parse_lit(r_expr.v[1])
                    errors.extend(quote_errors)
                    return expr, errors
            if sym == 'let':
                expr, let_errors = parse_let(r_expr)
                errors.extend(let_errors)
                return expr, errors

            if sym == 'if':
                expr, if_errors = parse_if(r_expr)
                errors.extend(if_errors)
                return expr, errors

            if sym == 'cond':
                expr, cond_errors = parse_cond(r_expr)
                errors.extend(cond_errors)
                return expr, errors

            if sym == 'match':
                expr, cond_errors = parse_match(r_expr)
                errors.extend(cond_errors)
                return expr, errors

            if sym == 'list':
                expr, cond_errors = parse_cond(r_expr)
                errors.extend(cond_errors)
                return expr, errors

            if sym == 'tuple':
                expr, cond_errors = parse_cond(r_expr)
                errors.extend(cond_errors)
                return expr, errors

            else:
                # parse a apply
                expr, apply_errors = parse_apply(r_expr)
                errors.extend(apply_errors)
                return expr, errors
        else:
            expr, apply_errors = parse_apply(r_expr)
            errors.extend(apply_errors)
    else:
        expr = parse_lit(r_expr)
        if isinstance(expr, IRSymbol):
            expr = IRVar(expr.v)

    return expr, errors


def parse_define(r_expr: RList) -> (IRDefine, [str]):
    define = None
    errors = []
    if len(r_expr.v) != 3:
        errors.append("wrong arity of define form")
        return None, errors
    args = r_expr.v[1]
    body = r_expr.v[2]

    if not isinstance(args, RList):
        errors.append("wrong form of define parameters")
        return None, errors
    else:
        vars = []
        for arg in args.v:
            if isinstance(arg, RSymbol):
                vars.append(IRVar(arg.v))
            else:
                errors.append("error in lambda parameters, form is not a symbol")
        ret, ret_errors = parse_ir_expr(body)
        errors.extend(ret_errors)
        define = IRDefine(vars[0], vars[1:], ret)

    return define, errors


def parse_type_decl(env: (Set[str], Mapping[str, int]), r_expr: RExpr) -> (Type, [str]):
    bounded_tvar, defined = env
    ret_type = None
    errors = []
    if isinstance(r_expr, RSymbol):
        sym = r_expr.v
        if sym == 'Number':
            ret_type = TYPE_NUMBER
        elif sym == 'Bool':
            ret_type = TYPE_BOOL
        elif sym == 'Symbol':
            ret_type = TYPE_SYMBOL
        elif sym == 'String':
            ret_type = TYPE_STRING
        elif sym == 'Unit':
            ret_type = TYPE_UNIT
        elif str.isupper(sym[0]):
            ret_type = Defined(sym, [])
        else:
            ret_type = TVar(sym)
        return ret_type, errors
    elif isinstance(r_expr, RList):
        if len(r_expr.v) == 0 or not isinstance(r_expr.v[0], RSymbol):
            errors.append('type must have name')
        type_name = r_expr.v[0].v
        subs = []
        for sub in r_expr.v[1:]:
            sub_t, sub_errors = parse_type_decl(env, sub)
            errors.extend(sub_errors)
            subs.append(sub_t)
        if type_name in defined:
            if len(subs) != defined[type_name]:
                errors.append("wrong arity in type apply")
            return Defined(type_name, subs), errors
        elif type_name == '*':
            # parse a tuple type
            if len(subs) == 0:
                return TYPE_UNIT, errors
            else:
                return Tuple(subs), errors
        elif type_name == '->':
            # parse a function type
            if len(subs) == 0:
                errors.append("empty function type")
                return ret_type, errors
            else:
                ret_type = subs[-1]
                for t in reversed(subs[:-1]):
                    ret_type = TArr(t, ret_type)
                return ret_type, errors
        else:
            print("unknown defined type {}".format(type_name))
            errors.append("unknown defined type {}".format(type_name))

    else:
        errors.append("type must be a symbol or a list")
    return ret_type, errors


def parse_define_ctors(defined: Type,
                       type_arity: Mapping[str, int],
                       r_expr: RList) -> ([(str, Type)], [str]):
    errors = []
    ctors = []

    ftv = defined.ftv()
    env = (ftv, type_arity)
    for r_ctor in r_expr.v[2:]:
        if not isinstance(r_ctor, RList) and len(r_ctor.v) > 0:
            errors.append("wrong form of data constructor")
            continue
        if not isinstance(r_ctor.v[0], RSymbol):
            errors.append("data constructor name must be symbol")
            continue
        ctor_name = r_ctor.v[0].v
        r_args = r_ctor.v[1:]
        arg_types = []
        for r_arg in r_args:
            arg_type, arg_errors = parse_type_decl(env, r_arg)
            errors.extend(arg_errors)
            arg_types.append(arg_type)

        ctor_type = defined
        for arg_type in reversed(arg_types):
            ctor_type = TArr(arg_type, ctor_type)

        ctors.append((ctor_name, ctor_type))
    return ctors, errors


def parse_define_sum(r_expr: RList) -> (Defined, [str]):
    errors = []
    ret_type = None
    if len(r_expr.v) < 3:
        errors.append("wrong arity in define-sum")
        return ret_type, errors

    # parse The Type
    r_ret_type = r_expr.v[1]

    if isinstance(r_ret_type, RSymbol):
        if not str.isupper(r_ret_type.v[0]):
            errors.append("Type name must start with Capital letter")
        ret_type = Defined(r_ret_type.v, [])
    elif isinstance(r_ret_type, RList):
        if len(r_ret_type.v) == 0:
            errors.append("type can't be a empty list")
        all_is_sym = all((isinstance(t, RSymbol) for t in r_ret_type.v))
        if not all_is_sym:
            errors.append("type must be list of symbol")
        else:
            type_name = r_ret_type.v[0].v
            if not str.isupper(type_name[0]):
                errors.append("Type name must start with Capital letter")
            t_vars = []
            bound_vars = set()
            for sym in r_ret_type.v[1:]:
                if not str.islower(sym.v[0]):
                    errors.append('TVar must start with lower letter')
                    continue
                else:
                    if sym.v in bound_vars:
                        errors.append('duplicate type variable {}'.format(sym.v))
                        continue
                    t_vars.append(TVar(sym.v))
            ret_type = Defined(type_name, t_vars)

    else:
        errors.append("type must be a symbol or a list")

    return ret_type, errors


def is_type_def(r_expr: RExpr) -> bool:
    if isinstance(r_expr, RList) \
            and len(r_expr.v) > 0 \
            and isinstance(r_expr.v[0], RSymbol):
        return r_expr.v[0] == 'define-sum'
    else:
        return False


def extract_and_check_type(r_exprs: [RList]):
    types = OrderedDict()
    ctors = []
    errors = []

    for r_expr in r_exprs:
        defined, defined_errors = parse_define_sum(r_expr)
        errors.extend(defined_errors)
        if defined.name not in types:
            types[defined.name] = defined
        else:
            errors.append("type {} has been defined".format(defined.name))
    if len(errors) > 0:
        return types, ctors, errors

    arity = {k: len(v.types) for k, v in types.items()}
    for r_expr, (name, t) in zip(r_exprs, types.items()):
        parsed_ctors, ctor_errors = parse_define_ctors(t, arity, r_expr)
        ctors.extend(parsed_ctors)

    return types, ctors, errors


def parse_r(r_exprs: [RExpr]) -> ([IRDefine], [IRExpr], [str]):
    defines = []
    exprs = []
    errors = []

    for expr in r_exprs:
        if isinstance(expr, RList):
            if len(expr.v) == 0:
                errors.append("empty application on top level, error")
                continue
            head = expr.v[0]
            if isinstance(head, RSymbol):
                sym = head.v
                if sym == 'define':
                    define, errs = parse_define(expr)
                    errors.extend(errs)
                    defines.append(define)
                else:
                    # parse IRExpr
                    ir_expr, errs = parse_ir_expr(expr)
                    errors.extend(errs)
                    exprs.append(ir_expr)
            else:
                if isinstance(head, RList):
                    ir_expr, errs = parse_ir_expr(expr)
                    errors.extend(errs)
                    exprs.append(ir_expr)
        # parse a literal
        else:
            exprs.append(parse_lit(expr))

    return defines, exprs
