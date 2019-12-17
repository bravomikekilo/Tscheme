from ir import *
from ir_lit import *


def parse_lit(expr: RExpr) -> IRExpr:
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