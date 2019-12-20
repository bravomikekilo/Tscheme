from ir import *
from ir_lit import *
from ir_pat import *
from type_sys import *
from typing import Mapping, Optional
from collections import OrderedDict
from code_gen import RecordCtor, RecordExtractor, SumCtor

class ParseError(object):

    def __init__(self, span: Span, msg: str):
        super(ParseError, self).__init__()
        self.span = span
        self.msg = msg

    def __str__(self):
        return 'in {}: {}'.format(self.span, self.msg)

    def __repr__(self):
        return 'ParseError({}: {})'.format(self.span, self.msg)


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
    elif isinstance(expr, RChar):
        return IRChar(expr.v)
    elif isinstance(expr, RList):
        ret = [parse_lit(v) for v in expr.v]
        return IRList(ret)
    else:
        raise ValueError('expr {} is not a literal'.format(expr))


def parse_lambda(r_expr: RList) -> (IRExpr, [ParseError]):
    errors = []
    lam = None
    if len(r_expr.v) != 3:
        errors.append(ParseError(r_expr.span, "wrong arity of lambda form"))
        return None, errors
    args = r_expr.v[1]
    body = r_expr.v[2]

    if not isinstance(args, RList):
        errors.append(ParseError(args.span, "wrong form of lambda parameters"))
        return None, errors
    else:
        vars = []
        for arg in args.v:
            if isinstance(arg, RSymbol):
                vars.append(IRVar(arg.v))
            else:
                errors.append(ParseError(arg.span, "error in lambda parameters, form is not a symbol"))
        ret, ret_errors = parse_ir_expr(body)
        errors.extend(ret_errors)
        lam = IRLambda(vars, ret)

    return lam, errors


def parse_let(r_expr: RList) -> (IRExpr, [ParseError]):
    errors = []
    let = None
    if len(r_expr.v) != 3:
        errors.append(ParseError(r_expr.span, "wrong arity of let form"))
        return let, errors
    r_envs = r_expr.v[1]
    r_body = r_expr.v[2]

    envs = []
    if not isinstance(r_envs, RList):
        errors.append(ParseError(r_envs.span, "error in let env, form is not a list"))
    else:
        for r_env in r_envs.v:
            if not isinstance(r_env, RList):
                errors.append(ParseError(r_env.span, 'env pair must be a list'))
                return let, errors
            if len(r_env.v) != 2:
                errors.append(ParseError(r_env.span, 'env pair must be pair'))
                continue
            r_v = r_env.v[0]
            r_d = r_env.v[1]
            if not isinstance(r_v, RSymbol):
                errors.append(ParseError(r_v.span, "binding must on a symbol"))
                v = None
            else:
                v = IRVar(r_v.v)

            d, d_error = parse_ir_expr(r_d)
            errors.extend(d_error)
            envs.append((v, d))
        body, body_errors = parse_ir_expr(r_body)
        errors.extend(body_errors)
        let = IRLet(envs, body)

    return let, errors


def parse_if(r_expr: RList) -> (IRExpr, [ParseError]):
    errors = []
    iff = None
    if len(r_expr.v) != 4:
        errors.append(ParseError(r_expr.span, "wrong arity in if form"))
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


def parse_cond_arm(r_expr: RList) -> ((IRExpr, IRExpr), [ParseError]):
    errors = []
    cond = None
    arm = None
    if len(r_expr.v) != 2:
        errors.append(ParseError(r_expr.span, "wrong arity in cond arm"))
        return (cond, arm), errors
    cond, cond_errors = parse_ir_expr(r_expr.v[0])
    errors.extend(cond_errors)

    arm, arm_errors = parse_ir_expr(r_expr.v[1])
    errors.extend(arm_errors)

    return (cond, arm), errors


def parse_cond(r_expr: RList) -> (IRExpr, [ParseError]):
    errors = []
    cond = None
    if len(r_expr.v) < 2:
        errors.append(ParseError(r_expr.span, "wrong arity in cond form"))
        return cond, errors
    r_conds = r_expr.v[1:]

    conds = []
    for r_cond in r_conds:
        if isinstance(r_cond, RList):
            (cond, arm), cond_errors = parse_cond_arm(r_cond)
            errors.extend(cond_errors)
            conds.append((cond, arm))
        else:
            errors.append(ParseError(r_cond.span, "cond arm must be a list"))
    cond = IRCond(conds)

    return cond, errors


def parse_apply(r_expr: RList) -> (IRExpr, [ParseError]):
    errors = []
    expr = None

    if len(r_expr.v) == 0:
        errors.append(ParseError(r_expr.span, "empty application on top level, error"))
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


def parse_pat(r_expr: RExpr) -> (IRPat, [ParseError]):
    errors = []
    pat = None

    if isinstance(r_expr, RList):
        if len(r_expr.v) == 0:
            errors.append(ParseError(r_expr.span, "pattern can't be empty"))
            return pat, errors

        head = r_expr.v[0]
        if isinstance(head, RSymbol):
            sym = head.v
            if sym == 'quote':
                if len(r_expr.v) != 2:
                    errors.append(ParseError(r_expr.span, "wrong arity in quote"))
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
            errors.append(ParseError(head.span, "pattern head should be a symbol"))
            return pat, errors
    else:
        lit = parse_lit(r_expr)
        # errors.extend(lit_errors)
        if isinstance(lit, IRSymbol):
            pat = IRVarPat(IRVar(lit.v))
        else:
            pat = IRLitPat(lit)

    return pat, errors


def parse_match(r_expr: RList) -> (IRExpr, [ParseError]):
    errors = []
    match = None

    if len(r_expr.v) < 3:
        errors.append(ParseError(r_expr.span, "match form must have matched expression and at least one match arm"))
        return match, errors
    v, v_errors = parse_ir_expr(r_expr.v[1])
    errors.extend(v_errors)
    arms = []
    for r_branch in r_expr.v[2:]:
        if isinstance(r_branch, RList):
            if len(r_branch.v) != 2:
                errors.append(ParseError(r_branch.span, "wrong arity in match arm"))
                continue
            r_pat = r_branch.v[0]
            r_arm = r_branch.v[1]
            pat, pat_errors = parse_pat(r_pat)
            arm, atm_errors = parse_ir_expr(r_arm)
            arms.append((pat, arm))
        else:
            errors.append(ParseError(r_branch.span, "match arm must be a list"))
            continue
    pat = IRMatch(v, arms)
    return pat, errors


def parse_list_form(r_expr: RList) -> (IRExpr, [ParseError]):
    errors = []

    r_args = r_expr.v[1:]
    args = []
    for r_arg in r_args:
        arg, arg_errors = parse_ir_expr(r_arg)
        args.append(arg)
        errors.extend(arg_errors)

    return IRListCtor(args), errors


def parse_tuple_form(r_expr: RList) -> (IRExpr, [ParseError]):
    errors = []

    r_args = r_expr.v[1:]
    args = []
    for r_arg in r_args:
        arg, arg_errors = parse_ir_expr(r_arg)
        args.append(arg)
        errors.extend(arg_errors)

    return IRTupleCtor(args), errors


def parse_set(r_expr: RList) -> (IRExpr, [ParseError]):
    errors = []
    form = None
    if len(r_expr.v) != 3:
        errors.append(ParseError(r_expr.span, "wrong arity in set! form"))
        return form, errors
    r_sym = r_expr.v[1]
    r_v = r_expr.v[2]

    if not isinstance(r_sym, RSymbol):
        errors.append(ParseError(r_sym.span, "must set! on a symbol"))
        return form, errors
    sym = IRVar(r_sym.v)
    v, v_errors = parse_ir_expr(r_v)
    errors.extend(v_errors)
    form = IRSet(sym, v)
    return form, errors


def parse_begin(r_expr: RList) -> (IRExpr, [ParseError]):
    errors = []

    if len(r_expr.v) == 1:
        errors.append(ParseError(r_expr.span, 'there must be at least one form in begin'))
        return None, errors

    r_args = r_expr.v[1:]
    args = []
    for r_arg in r_args:
        arg, arg_errors = parse_ir_expr(r_arg)
        args.append(arg)
        errors.extend(arg_errors)

    return IRBegin(args), errors


def parse_ir_expr(r_expr) -> (IRExpr, [ParseError]):
    errors = []
    expr = None
    if isinstance(r_expr, RList):
        if len(r_expr.v) == 0:
            errors.append(ParseError(r_expr.span, "empty application on top level, error"))
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
                    errors.append(ParseError(r_expr.span, "wrong arity in quote form"))
                    return expr, errors
                else:
                    expr = parse_lit(r_expr.v[1])
                    # errors.extend(quote_errors)
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
                expr, cond_errors = parse_list_form(r_expr)
                errors.extend(cond_errors)
                return expr, errors

            if sym == 'tuple':
                expr, cond_errors = parse_tuple_form(r_expr)
                errors.extend(cond_errors)
                return expr, errors

            if sym == 'set!':
                expr, set_errors = parse_set(r_expr)
                errors.extend(set_errors)
                return expr, errors

            if sym == 'begin':
                expr, begin_errors = parse_begin(r_expr)
                errors.extend(begin_errors)
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


def parse_define(r_expr: RList) -> (IRDefine, [ParseError]):
    define = None
    errors = []
    if len(r_expr.v) > 4 or len(r_expr.v) < 3:
        errors.append(ParseError(r_expr.span, "wrong arity of define form"))
        return None, errors

    args = r_expr.v[1]
    if len(r_expr.v) == 4:
        r_ret_type = r_expr.v[2]
        ret_type, ret_type_errors = parse_type_decl(None, r_ret_type)
        errors.extend(ret_type_errors)
        r_body = r_expr.v[3]
    else:
        ret_type = None
        r_body = r_expr.v[2]

    if not isinstance(args, RList):
        if isinstance(args, RSymbol):
            sym = IRVar(args.v)
            body, body_errors = parse_ir_expr(r_body)
            errors.extend(body_errors)
            return IRVarDefine(sym, body, ret_type), errors
        else:
            errors.append(ParseError(args.span, "wrong form of define parameters"))
            return None, errors
    else:
        vars = []
        var_names = set()
        arg_types = []
        for i, arg in enumerate(args.v):
            if isinstance(arg, RSymbol):
                if arg.v in var_names:
                    errors.append(ParseError(arg.span, "duplicate argument name {}".format(arg.v)))
                vars.append(IRVar(arg.v))
                var_names.add(arg.v)
                if i != 0:
                    arg_types.append(None)
            elif i != 0 and isinstance(arg, RList) and len(arg.v) == 2 and isinstance(arg.v[0], RSymbol):
                # parse argument with type annotation
                sym = arg.v[0].v
                r_anno = arg.v[1]
                anno, anno_errors = parse_type_decl(None, r_anno)
                errors.extend(anno_errors)
                arg_types.append(anno)
                if sym in var_names:
                    errors.append(ParseError(arg.v[0].span, "duplicate argument name {}".format(sym)))
                vars.append(IRVar(sym))
            else:
                errors.append(ParseError(arg.span,
                                         "error in lambda parameters, form is not a symbol or symbol with annotation"))
        arg_types.append(ret_type)
        if all((anno_type is None for anno_type in arg_types)):
            anno_type = None
        else:
            anno_type = TArr.func(*arg_types)
        ret, ret_errors = parse_ir_expr(r_body)
        errors.extend(ret_errors)
        define = IRDefine(vars[0], vars[1:], ret, anno_type)

    return define, errors


def parse_type_decl(env: (Set[str], Mapping[str, int]), r_expr: RExpr) -> (Type, [ParseError]):
    if env is None:
        bounded_tvar = None
        defined = None
    else:
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
        elif sym == 'Char':
            ret_type = TYPE_CHAR
        elif sym == 'Unit':
            ret_type = TYPE_UNIT
        elif str.isupper(sym[0]):
            ret_type = Defined(sym, [])
        else:
            if bounded_tvar is not None and sym not in bounded_tvar:
                errors.append(ParseError(r_expr.span, "unbounded type variable {}".format(sym)))
            ret_type = TVar(sym)
        return ret_type, errors
    elif isinstance(r_expr, RList):
        if len(r_expr.v) == 0 or not isinstance(r_expr.v[0], RSymbol):
            errors.append(ParseError(r_expr.span, 'type must have name'))
        type_name = r_expr.v[0].v
        subs = []
        for sub in r_expr.v[1:]:
            sub_t, sub_errors = parse_type_decl(env, sub)
            errors.extend(sub_errors)
            subs.append(sub_t)
        if type_name == '*':
            # parse a tuple type
            if len(subs) == 0:
                return TYPE_UNIT, errors
            else:
                return Tuple(subs), errors

        elif type_name == '->':
            # parse a function type
            if len(subs) == 0:
                errors.append(ParseError(r_expr.span, "empty function type"))
                return ret_type, errors
            else:
                ret_type = subs[-1]
                for t in reversed(subs[:-1]):
                    ret_type = TArr(t, ret_type)
                if len(subs) == 1:
                    ret_type = TArr(TYPE_UNIT, ret_type)
                return ret_type, errors

        elif defined is None or type_name in defined:
            if defined is None:
                return Defined(type_name, subs), errors
            if len(subs) != defined[type_name]:
                errors.append(ParseError(r_expr.span, "wrong arity in type apply"))
            return Defined(type_name, subs), errors

        else:
            print("unknown defined type {}".format(type_name))
            errors.append(ParseError(r_expr.span, "unknown defined type {}".format(type_name)))

    else:
        errors.append(ParseError(r_expr.span, "type must be a symbol or a list"))
    return ret_type, errors


def parse_define_sum_ctors(defined: Type,
                           type_arity: Mapping[str, int],
                           r_expr: RList) -> ([(str, Type)], [ParseError]):
    errors = []
    ctors = []

    ftv = defined.ftv()
    env = (ftv, type_arity)
    for r_ctor in r_expr.v[2:]:
        if not isinstance(r_ctor, RList) and len(r_ctor.v) > 0:
            errors.append(ParseError(r_ctor.span, "wrong form of data constructor"))
            continue
        if not isinstance(r_ctor.v[0], RSymbol):
            errors.append(ParseError(r_ctor.v[0].span, "data constructor name must be symbol"))
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


def parse_define_record_ctor(defined: Defined, type_arity, r_expr: RList) -> (RecordCtor, [RecordExtractor], [ParseError]):
    ctor = None
    exts = []
    errors = []

    ftv = defined.ftv()
    env = (ftv, type_arity)

    if len(r_expr.v) < 3:
        errors.append(ParseError(r_expr.span, 'wrong arity in define-record'))
        return ctor, exts, errors

    field_types = []
    for i, r_ext in enumerate(r_expr.v[2:]):

        if not isinstance(r_ext, RList) and len(r_ext.v) == 2:
            errors.append(ParseError(r_ext.span, "field in record define must be a pair"))
            continue
        if not isinstance(r_ext.v[0], RSymbol):
            errors.append(ParseError(r_ext.v[0].span, "field name must be a symbol"))

        ext_name = r_ext.v[0].v
        r_field_type = r_ext.v[1]
        field_type, field_type_errors = parse_type_decl(env, r_field_type)
        field_types.append(field_type)

        if len(field_type_errors) > 0:
            errors.append(ParseError(r_field_type.span, 'parse type error'))
        errors.extend(field_type_errors)
        ext_full_name = '{}.{}'.format(defined.name, ext_name)
        ext_type = TArr(defined, field_type)
        exts.append(RecordExtractor(ext_full_name, t=ext_type, order=i))

    field_types.append(defined)
    ctor_type = TArr.func(*field_types)
    ctor = RecordCtor(name=defined.name, t=ctor_type)

    return ctor, exts, errors


def parse_define_type(r_expr: RList) -> (Defined, [ParseError]):
    errors = []
    ret_type = None
    if len(r_expr.v) < 3:
        errors.append(ParseError(r_expr.span, "wrong arity in define-sum"))
        return ret_type, errors

    # parse The Type
    r_ret_type = r_expr.v[1]

    if isinstance(r_ret_type, RSymbol):
        if not str.isupper(r_ret_type.v[0]):
            errors.append(ParseError(r_ret_type.span, "Type name must start with Capital letter"))
        ret_type = Defined(r_ret_type.v, [])
    elif isinstance(r_ret_type, RList):
        if len(r_ret_type.v) == 0:
            errors.append(ParseError(r_ret_type.span, "type can't be a empty list"))
        all_is_sym = all((isinstance(t, RSymbol) for t in r_ret_type.v))
        if not all_is_sym:
            errors.append(ParseError(r_ret_type.span, "type must be list of symbol"))
        else:
            type_name = r_ret_type.v[0].v
            if not str.isupper(type_name[0]):
                errors.append(ParseError(r_ret_type.v[0].span, "Type name must start with Capital letter"))
            t_vars = []
            bound_vars = set()
            for sym in r_ret_type.v[1:]:
                if not str.islower(sym.v[0]):
                    errors.append(ParseError(sym.span, 'TVar must start with lower letter'))
                    continue
                else:
                    if sym.v in bound_vars:
                        errors.append(ParseError(sym.span, 'duplicate type variable {}'.format(sym.v)))
                        continue
                    t_vars.append(TVar(sym.v))
            ret_type = Defined(type_name, t_vars)

    else:
        errors.append(ParseError(r_ret_type.span, "type must be a symbol or a list"))

    return ret_type, errors


def is_type_def(r_expr: RExpr) -> bool:
    if isinstance(r_expr, RList) \
            and len(r_expr.v) > 0 \
            and isinstance(r_expr.v[0], RSymbol):
        sym = r_expr.v[0].v
        return sym == 'define-sum' or sym == 'define-record'
    else:
        return False


def extract_and_check_type(r_exprs: [RList]):
    types = OrderedDict()
    ctors = []
    errors = []

    for r_expr in r_exprs:
        defined, defined_errors = parse_define_type(r_expr)
        errors.extend(defined_errors)
        if defined.name not in types:
            types[defined.name] = defined
        else:
            msg = "type {} has been defined".format(defined.name)
            errors.append(ParseError(r_expr.span, msg))
    if len(errors) > 0:
        return types, ctors, errors

    arity = {k: len(v.types) for k, v in types.items()}
    for r_expr, (name, t) in zip(r_exprs, types.items()):
        parsed_ctors, ctor_errors = parse_define_sum_ctors(t, arity, r_expr)
        ctors.extend(parsed_ctors)

    return types, ctors, errors


def parse_r(r_exprs: [RExpr]) -> ([IRDefine], [IRExpr], [str]):
    defines = []
    exprs = []
    errors = []

    for expr in r_exprs:
        if isinstance(expr, RList):
            if len(expr.v) == 0:
                errors.append(ParseError(expr.span, "empty application on top level, error"))
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
