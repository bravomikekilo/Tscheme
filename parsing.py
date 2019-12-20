from syntax import *
from parsy import regex, generate
import parsy


def to_pos(pos: (int, int)):
    ln, col = pos
    return Pos(ln + 1, col + 1)


def to_range(start: (int, int), end: (int, int)):
    start_pos = to_pos(start)
    end_pos = to_pos(end)
    return Span(start_pos, end_pos)


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

@generate
def number():
    start_pos = yield parsy.line_info
    ret = yield regex(r'[+-]?\d+(\.\d+)?').map(map_number)
    end_pos = yield parsy.line_info
    ran = to_range(start_pos, end_pos)
    ret.range = ran
    return ret

# number = regex(r'[+-]?\d+(\.\d+)?').map(map_number)

raw_symbol = regex(r"""[^()[\]{}",'`|\s]+""")


@generate
def slist():
    start_pos = yield parsy.line_info
    forward = yield parsy.regex(r'[([]')
    atoms = yield atom.sep_by(parsy.whitespace)

    if forward == '(':
        yield regex(r'\s*') >> parsy.string(')')
    else:
        yield regex(r'\s*') >> parsy.string(']')
    end_pos = yield parsy.line_info
    return RList(atoms, sq=forward == '[', span=to_range(start_pos, end_pos))


@generate
def symbol():
    """
    parse a symbol or a bool
    """
    start_pos = yield parsy.line_info
    raw = yield raw_symbol
    end_pos = yield parsy.line_info

    ran = to_range(start_pos, end_pos)
    if raw == '#t':
        return RBool(True, span=ran)
    elif raw == '#f':
        return RBool(False, span=ran)
    elif raw.startswith('#\\'):
        return RChar(raw)
    else:
        return RSymbol(raw, span=ran)


@generate
def string():
    start_pos = yield parsy.line_info
    ret = yield regex(r'''"[^"]*"''').map(lambda x: RString(x[1:-1]))
    end_pos = yield parsy.line_info
    return RString(ret, span=to_range(start_pos, end_pos))


@generate
def atom():
    start_pos = yield parsy.line_info
    quote = yield parsy.string("'").optional()
    ret = yield raw_atom
    end_pos = yield parsy.line_info

    ran = to_range(start_pos, end_pos)
    if quote is not None:
        return RList([RSymbol('quote'), ret], span=ran)
    else:
        ret.range = ran
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



