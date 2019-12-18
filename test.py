from parsing import raw_atom
from ir_parse import parse_ir_expr, parse_define
from ir import *
from syntax import *
from infer import *

#%%
number = TYPE_NUMBER
bool = TYPE_BOOL

t1 = TVar('t1')
t2 = TVar('t2')
t3 = TVar('t3')
t4 = TVar('t4')


def listof(t_var: TVar):
    return Defined("List", [t_var])


ops = {
    '+': Schema.none(TArr.func(number, number, number)),
    '-': Schema.none(TArr.func(number, number, number)),
    '*': Schema.none(TArr.func(number, number, number)),
    '/': Schema.none(TArr.func(number, number, number)),
    '=': Schema.none(TArr.func(number, number, bool)),
    '>': Schema.none(TArr.func(number, number, bool)),
    '<': Schema.none(TArr.func(number, number, bool)),
    'rand': Schema.none(TArr.func(TYPE_UNIT, number)),
    'cons': Schema.none(TArr.func(t3, listof(t3), listof(t3))),
    'Cons': Schema(TArr.func(t1, listof(t1), listof(t1)), [t1]),
    'Null': Schema(listof(t2), [t2]),
    'null': Schema(listof(t4), [t4]),
}


def load_ir_expr_and_infer(path, ops):
    with open(path, 'r') as f:
        src = f.read()
    r, _ = raw_atom.parse_partial(src)
    ir, errors = parse_ir_expr(r)
    if len(errors) > 0:
        for error in errors:
            print('error in parsing ir:', error)
    ir_lit = '\n'.join(ir.print())
    print(ir_lit)
    env = TypeEnv(ops)
    infer_sys = InferSys()
    ir_tvar = infer_sys.infer_ir_expr(env, ir)
    print('result t_var:', ir_tvar)
    try:
        subst = infer_sys.solve_curr_equation()
    except UniException as e:
        print(e.why)
        raise e
    ir_result = ir_tvar.apply(subst)
    print('result:', ir_result)
    return ir_tvar, subst, ir_result


def load_ir_define_and_infer(path, ops):

    with open(path, 'r') as f:
        src = f.read()
    r, _ = raw_atom.parse_partial(src)
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
    try:
        subst = infer_sys.solve_curr_equation()
    except UniException as e:
        print(e.why)
        raise e
    ir_result = ir_tvar.apply(subst)
    print('result:', ir_result)
    return ir_tvar, subst, ir_result


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
load_ir_expr_and_infer('test_src/no_arg_func.rkt', ops)
load_ir_expr_and_infer('test_src/rand_add.rkt', ops)

#%% list form test
load_ir_expr_and_infer('test_src/list_repeat.rkt', ops)

#%%
load_ir_expr_and_infer('test_src/match.rkt', ops)
load_ir_define_and_infer('test_src/define_map.rkt', ops)
load_ir_define_and_infer('test_src/define_zip.rkt', ops)
load_ir_define_and_infer('test_src/define_zip_with.rkt', ops)
load_ir_define_and_infer('test_src/define_take.rkt', ops)
load_ir_define_and_infer('test_src/define_take_while.rkt', ops)
load_ir_define_and_infer('test_src/define_drop.rkt', ops)
load_ir_define_and_infer('test_src/define_drop_while.rkt', ops)
load_ir_define_and_infer('test_src/define_foldl.rkt', ops)
load_ir_define_and_infer('test_src/define_foldr.rkt', ops)
load_ir_expr_and_infer('test_src/list_head.rkt', ops)
load_ir_define_and_infer('test_src/define_concat.rkt', ops)

#%%
load_ir_expr_and_infer('test_src/plus1.rkt', ops)
load_ir_expr_and_infer('test_src/add.rkt', ops)
load_ir_expr_and_infer('test_src/id.rkt', ops)
load_ir_expr_and_infer('test_src/compose.rkt', ops)
load_ir_expr_and_infer('test_src/apply.rkt', ops)

#%%
load_ir_define_and_infer('test_src/factorial.rkt', ops)
load_ir_define_and_infer('test_src/factorial_cond.rkt', ops)

