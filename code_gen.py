from type_sys import *
from syntax import *
from typing import Optional


def gen_ctor_define(ctor_name: str, ctor_type: Type) -> Optional[RList]:
    if ctor_name == 'Cons':
        return None
    if ctor_name == 'Null':
        return None

    arity = ctor_type.arity() - 1
    args = [RSymbol(chr(ord('a') + i)) for i in range(arity)]

    arg_list = [RSymbol(ctor_name)]
    arg_list.extend(args)

    body_list = [RSymbol('list'), quote(RSymbol(ctor_name))]
    body_list.extend(args)

    ret = [RSymbol('define'), RList(arg_list), RList(body_list)]

    return RList(ret)
