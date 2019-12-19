from infer import *


def confirm_type(infered, anno):
    match, subst = confirm(infered, anno)
    for k, v in subst.items():
        print(k, '=>', v)

    print('matched' if match else 'mismatch')
    print(infered.apply(subst), ('==' if match else '!='), anno)

#%%

anno = TArr.func(TVar('a'), TArr.func(TVar('c'), TVar('c')), TVar('a'), None, TVar('b'))
print(anno)

#%%

infered = TArr.func(TVar('a1'), TArr.func(TVar('c1'), TVar('c1')), TVar('a1'), TVar('x'), TVar('b1'))
print(infered)


#%%
confirm_type(infered, anno)

#%%
infered = TArr.func(TVar('c'), TVar('c'))
anno = TArr.func(TVar('a'), TVar('b'))

confirm_type(infered, anno)

#%%
infered = TArr.func(TVar('b'), TVar('b'))
anno = TArr.func(TVar('a'), TVar('b'))

confirm_type(infered, anno)

