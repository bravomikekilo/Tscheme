from syntax import *
from parsy import regex, generate
import parsy


def map_number(s):
    sign = 1
    if '+' in s or '-' in s:
        sign = 1 if s[0] == '+' else -1
        s = s[1:]
    body = float(s)
    if '.' not in s:
        body = int(body)
        return RInt(sign * body)
    return RFloat(sign * body)


number = regex(r'[+-]?\d+(\.\d+)?').map(map_number)

raw_symbol = regex(r"""[^()[\]{}",'`|\s]+""")


@generate
def slist():
    forward = yield parsy.regex(r'[([]')
    atoms = yield atom.sep_by(parsy.whitespace)

    if forward == '(':
        yield regex(r'\s*') >> parsy.string(')')
    else:
        yield regex(r'\s*') >> parsy.string(']')
    return RList(atoms, sq=forward == '[')


@generate
def symbol():
    """
    parse a symbol or a bool
    """
    raw = yield raw_symbol
    if raw == '#t':
        return RBool(True)
    elif raw == '#f':
        return RBool(False)
    else:
        return RSymbol(raw)


string = regex(r'''"[^"]*"''').map(lambda x: RString(x[1:-1]))



@generate
def atom():
    quote = yield parsy.string("'").optional()
    ret = yield raw_atom

    if quote is not None:
        return RList([RSymbol('quote'), ret])
    else:
        return ret

raw_atom = number | symbol | string | slist

@generate
def whole_program():
    """
    parse whole program
    """
    yield regex(r'\s*')
    atoms = yield atom.sep_by(regex(r'\s*'))
    yield regex(r'\s*')
    return atoms



