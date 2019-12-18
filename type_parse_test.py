#%%
from ir_parse import *
from parsing import raw_atom
import parsy

#%%

with open('test_src/tree.rkt') as f:
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



