from type_sys import *
from syntax import *
from typing import Optional


def count_func_arity(ctor_type: Type) -> int:
    if not isinstance(ctor_type, TArr):
        return 1
    ret = 1
    while isinstance(ctor_type, TArr):
        ret += 1
        ctor_type = ctor_type.out_type
    return ret


def gen_ctor_define(ctor_name: str, ctor_type: Type) -> Optional[RList]:
    if ctor_name == 'Cons':
        return None
    if ctor_name == 'Null':
        return None

    arity = count_func_arity(ctor_type)
    args = [RSymbol(chr(ord('a') + i)) for i in range(arity)]

    arg_list = [RSymbol(ctor_name)]
    arg_list.extend(args)

    body_list = [RSymbol('list'), quote(RSymbol(ctor_name))]
    body_list.extend(args)

    ret = [RSymbol('define'), RList(arg_list), RList(body_list)]

    return RList(ret)
