#%%
from ir_parse import *
from parsing import raw_atom, whole_program
import parsy
from type_check import extract_type

#%%

with open('test_src/types.rkt') as f:
    src = f.read()
r_exprs, reminder = raw_atom.sep_by(parsy.regex(r'\s*')).parse_partial(src)

types, ctors, errors = extract_and_check_type(r_exprs)

if len(errors) > 0:
    for error in errors:
        print('error in extract type:', error)
for k, v in types.items():
    print('type {} => {}'.format(k, v))

for ctor in ctors:
    print('ctor:', ctor)




#%%
with open('test_src/types/full_types.rkt') as f:
    src = f.read()

forms = whole_program.parse(src)

(other_forms, record_names, types, funcs, code_gens), errors = extract_type(forms)
print('extract_finish')
for error in errors:
    print(error)

for name, t in types.items():
    print('defined type {} :: {}'.format(name, t))


for name, t in funcs.items():
    print('defined func {} :: {}'.format(name, t))

for code_gen in code_gens:
    print('code_gen:')
    print(code_gen.code_gen().pretty_print(indent_width=2))
    print('---------------------\n')

for record_name in record_names:
    print('record_name:', record_name)
