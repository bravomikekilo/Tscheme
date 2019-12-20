#!/usr/bin/env python3
from infer import *
from typing import Set
from ir_parse import ParseError
from ir_parse import is_type_def, parse_define_type, parse_define_sum_ctors, parse_define_record_ctor
from ir_parse import parse_define, parse_ir_expr, parse_lit
from collections import OrderedDict
from parsing import whole_program
from code_gen import CodeGen, SumCtor
from more_itertools import tail


from argparse import ArgumentParser


def extract_type(forms: [RExpr]) -> (
        ([RExpr], Set[str], Mapping[str, Type], Mapping[str, Type], [CodeGen]), [ParseError]):
    errors = []
    record_names = set()
    types = OrderedDict()
    funcs = OrderedDict()
    code_gens = []

    type_forms = [form for form in forms if is_type_def(form)]
    other_forms = [form for form in forms if not is_type_def(form)]

    types['List'] = Defined("List", [TVar('a')])

    # first parse out all types declarations
    for r_expr in type_forms:
        defined, defined_errors = parse_define_type(r_expr)
        errors.extend(defined_errors)
        if defined.name not in types:
            types[defined.name] = defined
        else:
            errors.append(ParseError(r_expr.span, "type {} has been defined".format(defined.name)))

    if len(errors) > 0:
        return (other_forms, record_names, types, funcs, code_gens), errors

    arity = {k: len(v.types) for k, v in types.items()}

    type_items = iter(types.items())
    next(type_items)
    for r_expr, (name, t) in zip(type_forms, type_items):
        if r_expr.v[0].v == 'define-record':
            # parse record type ctor and extractor
            record_names.add(name)
            ctor, exts, record_errors = parse_define_record_ctor(t, arity, r_expr)
            if len(record_errors) > 0:
                errors.extend(record_errors)
            funcs[ctor.name] = ctor.type
            for ext in exts:
                funcs[ext.name] = ext.type
            code_gens.append(ctor)
            code_gens.extend(exts)
        else:
            parsed_ctors, ctor_errors = parse_define_sum_ctors(t, arity, r_expr)

            if len(ctor_errors) == 0:
                errors.extend(ctor_errors)
            for ctor_name, ctor_type in parsed_ctors:
                full_name = '{}.{}'.format(t.name, ctor_name)
                sum_type_ctor = SumCtor(name=full_name, t=ctor_type)
                funcs[sum_type_ctor.name] = sum_type_ctor.type
                code_gens.append(sum_type_ctor)

    return (other_forms, record_names, types, funcs, code_gens), errors


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
            defined, defined_errors = parse_define_type(r_expr)
            errors.extend(defined_errors)
            if defined.name not in types:
                types[defined.name] = defined
            else:
                errors.append("type {} has been defined".format(defined.name))
        if len(errors) > 0:
            return types, ctors, errors

        arity = {k: len(v.types) for k, v in types.items()}

        for r_expr, (name, t) in zip(type_forms, types.items()):
            parsed_ctors, ctor_errors = parse_define_sum_ctors(t, arity, r_expr)
            errors.extend(ctor_errors)
            if len(ctor_errors) == 0:
                for ctor_name, ctor in parsed_ctors:
                    ctors['{}.{}'.format(t.name, ctor_name)] = ctor

        return types, ctors, errors

    def check_content(self, r_exprs: [RExpr], verbose=False) -> \
            ([CodeGen], Set[str], [IRTerm], [ParseError]):
        errors = []
        ir_terms = []
        (other_forms, record_names, types, funcs, code_gens), type_errors = extract_type(r_exprs)
        # types, ctors, type_errors = self.check_types(type_forms)

        if len(type_errors) > 0:
            errors.extend(type_errors)
            return code_gens, record_names, ir_terms, errors

        infer_sys = InferSys()
        type_env = TypeEnv.default()

        if verbose:
            for type_name, t in types.items():
                print("defined type {} :: {}".format(type_name, t))

            for name, t in funcs.items():
                print("get func {} :: {}".format(name, t))

        schemas = []
        schemas.extend(((TVar(name), infer_sys.generalize(t)) for name, t in types.items()))
        schemas.extend(((TVar(name), infer_sys.generalize(t)) for name, t in funcs.items()))

        type_env = type_env.extend(schemas)

        for expr in other_forms:
            if isinstance(expr, RList):
                if len(expr.v) == 0:
                    errors.append(ParseError(expr.span, "empty application on top level, error"))
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
                        if isinstance(define, IRDefine):
                            t, msg = infer_sys.solve_ir_define(type_env, define)
                        else:
                            t, msg = infer_sys.solve_var_define(type_env, define)

                        if msg is not None:
                            errors.append(
                                ParseError(
                                    expr.span,
                                    'type error, unification error: {}'.format(msg)
                                )
                            )
                            continue

                        if define.anno is not None:
                            anno = define.anno
                            matched, subst = confirm(t, anno)
                            # print('origin solved type', t)
                            if not matched:
                                msg = 'define {} type mismatch, infered {}, but annotation is {}' \
                                    .format(define.sym.v, t.apply(subst), anno)
                                print('type of anno', type(anno))
                                errors.append(ParseError(expr.span, msg))
                                continue
                            else:
                                # print('type matched')
                                # print('flattened anno', anno.flatten())
                                if isinstance(anno, TArr) and (any(t is None for t in anno.flatten())):

                                    msg = 'define {} type fullfilled, infered {}, annotation is {}' \
                                        .format(define.sym.v, t.apply(subst), anno)
                                    print(ParseError(expr.span, msg))

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
                        t, msg = infer_sys.solve_ir_expr(type_env, ir_expr)
                        if msg is not None:
                            msg = "type error, unification error {}".format(msg)
                            errors.append(ParseError(expr.span, msg))
                            continue

                        if verbose:
                            print('expr: {} :: {}'.format(ir_expr.to_raw(), t))
                else:
                    if isinstance(head, RList):
                        ir_expr, errs = parse_ir_expr(expr)
                        ir_terms.append(ir_expr)
                        errors.extend(errs)
                        if len(errors) > 0:
                            continue
                        t, msg = infer_sys.solve_ir_expr(type_env, ir_expr)
                        if msg is not None:
                            msg = "type error, unification error {}".format(msg)
                            errors.append(ParseError(expr.span, msg))
                            continue
                        if verbose:
                            print('expr: {} :: {}'.format(ir_expr.to_raw(), t))
                    else:
                        errors.append(ParseError(expr.span, "expr head must be a lambda or a symbol"))
                        continue
            else:
                lit = parse_lit(expr)
                ir_terms.append(expr)
                t, msg = infer_sys.solve_ir_expr(type_env, lit)
                if msg is not None:
                    msg = "type error, unification error {}".format(msg)
                    errors.append(ParseError(expr.span, msg))
                    continue
                if verbose:
                    print('literal: {} :: {}'.format(lit.to_raw(), t))

        return code_gens, record_names, ir_terms, errors


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
