#%%
from infer import *

#%%
def show_su(su):
    for k, v in su.items():
        print('{} => {}'.format(TVar(k), v))

#%%


#%%
a = TVar('a')
b = TVar('b')
c = TVar('c')

t1 = TVar('t1')
t2 = TVar('t2')
t3 = TVar('t3')
t4 = TVar('t4')

Int = TConst('Int')
Bool = TConst('Bool')
Int2Bool = TArr(Int, Bool)

Tree = Defined("Tree", [a, Defined("Tree", [Int])])
print("Tree:", Tree)
#%%
su = unifies([(a, b), (b, Int)])
show_su(su)

#%%

su = unifies([(a, Int2Bool)])
show_su(su)

#%%

su = unifies([(TArr(t1, t2), TArr(t3, t4))])
show_su(su)


#%%

su = unifies([(TArr(t1, t2), TArr(t2, t1))])
show_su(su)

#%%

su = unifies([
    (TArr(t2, t3),  t1),
    (t2, t3)
])
show_su(su)


#%%
a1 = TVar('a1')
a2 = TVar('a2')
a1_2_a2 = TArr(a1, a2)

infer_sys = InferSys()
schema = Schema(a1_2_a2, [a1])
inst_ret = infer_sys.inst(schema)

#%%

