#!/usr/bin/env python3
from infer import *
from ir_parse import is_type_def, parse_define_sum, parse_define_ctors
from ir_parse import parse_define, parse_ir_expr, parse_lit
from collections import OrderedDict
from parsing import whole_program

from argparse import ArgumentParser


class TypeChecker(object):

    def __init__(self, type_env=None):
        super(TypeChecker, self).__init__()
        if type_env is None:
            self.type_env = TypeEnv.empty()
        else:
            self.type_env = type_env
        self.defined_types = OrderedDict()
        self.ctors = OrderedDict()
        self.infer_sys = InferSys()

    def check_types(self, type_forms: [RList]) -> (Mapping[str, Type], Mapping[str, Type], [str]):
        errors = []
        types = OrderedDict()
        ctors = OrderedDict()

        for r_expr in type_forms:
            defined, defined_errors = parse_define_sum(r_expr)
            errors.extend(defined_errors)
            if defined.name not in types:
                types[defined.name] = defined
            else:
                errors.append("type {} has been defined".format(defined.name))
        if len(errors) > 0:
            return types, ctors, errors

        arity = {k: len(v.types) for k, v in types.items()}

        for r_expr, (name, t) in zip(type_forms, types.items()):
            parsed_ctors, ctor_errors = parse_define_ctors(t, arity, r_expr)
            errors.extend(ctor_errors)
            if len(ctor_errors) == 0:
                for ctor_name, ctor in parsed_ctors:
                    ctors['{}.{}'.format(t.name, ctor_name)] = ctor

        return types, ctors, errors

    def check_content(self, r_exprs: [RExpr], verbose=False) ->\
            (Mapping[str, Type], Mapping[str, Type], [IRTerm], [str]):
        errors = []
        ir_terms = []
        type_forms = [form for form in r_exprs if is_type_def(form)]
        other_forms = [form for form in r_exprs if not is_type_def(form)]
        types, ctors, type_errors = self.check_types(type_forms)
        if len(type_errors) > 0:
            errors.extend(type_errors)
            return types, ctors, ir_terms, errors

        infer_sys = InferSys()
        type_env = TypeEnv.default()

        if verbose:
            for type_name, t in types.items():
                print("get type:", t)

        ctor_schemas = []
        for ctor_name, ctor_type in ctors.items():
            if verbose:
                print("get data ctor {} :: {}".format(ctor_name, ctor_type))
            s = infer_sys.generalize(ctor_type)
            ctor_schemas.append((IRVar(ctor_name), s))
        type_env = type_env.extend(ctor_schemas)

        for expr in other_forms:
            if isinstance(expr, RList):
                if len(expr.v) == 0:
                    errors.append("empty application on top level, error")
                    continue
                head = expr.v[0]
                if isinstance(head, RSymbol):
                    sym = head.v
                    if sym == 'define':
                        define, errs = parse_define(expr)
                        ir_terms.append(define)
                        errors.extend(errs)
                        if len(errs) > 0:
                            continue
                        t = infer_sys.solve_ir_define(type_env, define)
                        s = infer_sys.generalize(t)
                        type_env = type_env.add(define.sym, s)
                        if verbose:
                            if s.is_dummy():
                                print('define: {} :: {}'.format(define.sym.v, t))
                            else:
                                print('define: {} :: {}'.format(define.sym.v, s))
                    else:
                        # parse IRExpr
                        ir_expr, errs = parse_ir_expr(expr)
                        ir_terms.append(ir_expr)
                        errors.extend(errs)
                        if len(errs) > 0:
                            continue
                        t = infer_sys.solve_ir_expr(type_env, ir_expr)
                        if verbose:
                            print('expr: {} :: {}'.format(ir_expr.to_raw(), t))
                else:
                    if isinstance(head, RList):
                        ir_expr, errs = parse_ir_expr(expr)
                        ir_terms.append(ir_expr)
                        errors.extend(errs)
                        if len(errors) > 0:
                            continue
                        t = infer_sys.solve_ir_expr(type_env, ir_expr)
                        if verbose:
                            print('expr: {} :: {}'.format(ir_expr.to_raw(), t))
                    else:
                        errors.append("expr head must be a lambda or a symbol")
                        continue
            else:
                lit = parse_lit(expr)
                ir_terms.append(expr)
                t = infer_sys.solve_ir_expr(type_env, lit)
                if verbose:
                    print('literal: {} :: {}'.format(lit.to_raw(), t))
        return types, ctors, ir_terms, errors


def main():
    parser = ArgumentParser(description='script used to check typed-scheme type')
    parser.add_argument('script', help='path to script')
    parser.add_argument('--silent', action='store_true', help='slient success output')

    ARGS = parser.parse_args()
    SCRIPT_PATH = ARGS.script
    SILENT = ARGS.silent

    with open(SCRIPT_PATH, 'r') as f:
        SRC = f.read()

    r_exprs = whole_program.parse(SRC)

    checker = TypeChecker()
    _, _, _, errors = checker.check_content(r_exprs, verbose=not SILENT)
    if len(errors) > 0:
        for error in errors:
            print(error)


if __name__ == '__main__':
    main()




