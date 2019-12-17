from parsing import raw_atom
from ir_parse import parse_ir_expr, parse_define
from ir import *
from syntax import *
from type_sys import *

#%%
with open('test_src/plus1.rkt') as f:
    plus1_src = f.read()
print(plus1_src)

#%%
plus1_r = raw_atom.parse(plus1_src)


#%%
plus1_ir, ir_errors = parse_ir_expr(plus1_r)
print('ir_errors:', ir_errors)
plus1_ir_lit = '\n'.join(plus1_ir.print())
print(plus1_ir_lit)

#%%
number = TYPE_NUMBER
bool = TYPE_BOOL
ops = {
    '+': Schema.none(TArr(number, TArr(number, number))),
    '-': Schema.none(TArr(number, TArr(number, number))),
    '*': Schema.none(TArr(number, TArr(number, number))),
    '/': Schema.none(TArr(number, TArr(number, number))),
    '=': Schema.none(TArr(number, TArr(number, bool))),
    '>': Schema.none(TArr(number, TArr(number, bool))),
    '<': Schema.none(TArr(number, TArr(number, bool))),
}


def load_ir_expr_and_infer(path, ops):
    with open(path, 'r') as f:
        src = f.read()
    r = raw_atom.parse(src)
    ir, errors = parse_ir_expr(r)
    if len(errors) > 0:
        for error in errors:
            print('error in parsing ir:', error)
    ir_lit = '\n'.join(ir.print())
    print(ir_lit)
    env = TypeEnv(ops)
    infer_sys = InferSys()
    ir_tvar = infer_sys.infer_ir_expr(env, ir)
    subst = infer_sys.solve_curr_equation()
    ir_result = ir_tvar.apply(subst)
    print('result:', ir_result)
    return ir_tvar, subst, ir_result


def load_ir_define_and_infer(path, ops):

    with open(path, 'r') as f:
        src = f.read()
    r = raw_atom.parse(src)
    ir_define, errors = parse_define(r)
    if len(errors) > 0:
        for error in errors:
            print('error in parsing ir:', error)
    ir_lit = '\n'.join(ir_define.print())
    print(ir_lit)
    env = TypeEnv(ops)
    infer_sys = InferSys()
    ir_tvar = infer_sys.infer_ir_define(env, ir_define)
    print('result t_var:', ir_tvar)
    subst = infer_sys.solve_curr_equation()
    ir_result = ir_tvar.apply(subst)
    print('result:', ir_result)
    return ir_tvar, subst, ir_result

#%%


infer_sys = InferSys()

env = TypeEnv(ops)

try:
    plus1_tvar = infer_sys.infer_ir_expr(env, plus1_ir)
    subst = infer_sys.solve_curr_equation()
    plus1_result = plus1_tvar.apply(subst)
except UniException as e:
    print('exception in unification why:', e.why)
    raise e


print('plus1_result:', plus1_result)


#%%
load_ir_expr_and_infer('test_src/plus1.rkt', ops)
load_ir_expr_and_infer('test_src/add.rkt', ops)
load_ir_expr_and_infer('test_src/id.rkt', ops)

#%%
load_ir_define_and_infer('test_src/factorial.rkt', ops)
load_ir_define_and_infer('test_src/factorial_cond.rkt', ops)

