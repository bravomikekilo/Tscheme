from type_sys import *
from syntax import *
from typing import Optional


class CodeGen(object):

    def __init__(self):
        super(CodeGen, self).__init__()

    def code_gen(self) -> RList:
        raise NotImplementedError()


class Ctor(CodeGen):

    def __init__(self, name: str, t: Type):
        super(Ctor, self).__init__()
        self.name = name
        self.type = t

    def code_gen(self) -> RList:
        raise NotImplementedError()


class SumCtor(Ctor):

    def __init__(self, name: str, t: Type):
        super(SumCtor, self).__init__(name, t)

    def code_gen(self) -> RList:

        ctor_type = self.type
        ctor_name = self.name

        arity = ctor_type.arity() - 1
        args = [RSymbol(chr(ord('a') + i)) for i in range(arity)]

        arg_list = [RSymbol(ctor_name)]
        arg_list.extend(args)

        body_list = [RSymbol('list'), quote(RSymbol(ctor_name))]
        body_list.extend(args)

        ret = [RSymbol('define'), RList(arg_list), RList(body_list)]

        return RList(ret)


class RecordCtor(Ctor):

    def __init__(self, name: str, t: Type):
        super(RecordCtor, self).__init__(name, t)
        pass

    def code_gen(self) -> RList:
        t = self.type
        arity = t.arity() - 1
        args = [RSymbol(chr(ord('a') + i)) for i in range(arity)]
        arg_list = [RSymbol(self.name)]
        arg_list.extend(args)

        body_list = [RSymbol('vector')]
        body_list.extend(args)
        ret = [RSymbol('define'), RList(arg_list), RList(body_list)]
        return RList(ret)


class RecordExtractor(CodeGen):

    def __init__(self, name: str, t: Type, order: int):
        super(RecordExtractor, self).__init__()
        self.name = name
        self.type = t
        self.order = order

    def code_gen(self) -> RList:
        arg_list = [RSymbol(self.name), RSymbol('t')]
        body_list = [RSymbol('vector-ref'), RSymbol('t'), RInt(self.order)]
        ret = [RSymbol('define'), RList(arg_list), RList(body_list)]
        return RList(ret)


def gen_ctor_define(ctor_name: str, ctor_type: Type) -> Optional[RList]:
    if ctor_name == 'Cons':
        return None
    if ctor_name == 'Nil':
        return None

    arity = ctor_type.arity() - 1
    args = [RSymbol(chr(ord('a') + i)) for i in range(arity)]

    arg_list = [RSymbol(ctor_name)]
    arg_list.extend(args)

    body_list = [RSymbol('list'), quote(RSymbol(ctor_name))]
    body_list.extend(args)

    ret = [RSymbol('define'), RList(arg_list), RList(body_list)]

    return RList(ret)
