#!/usr/bin/env python3
from infer import *
from typing import Set
from ir_parse import ParseError
from ir_parse import is_type_def, parse_define_type, parse_define_sum_ctors, parse_define_record_ctor
from ir_parse import parse_define, parse_ir_expr, parse_lit
from collections import OrderedDict
from parsing import whole_program
from code_gen import CodeGen, SumCtor
from networkx import DiGraph
from networkx.algorithms.components import strongly_connected_components as scc
from networkx.algorithms.components import condensation
from networkx.algorithms.dag import topological_sort
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

    def __init__(self, type_env=None, verbose=False):
        super(TypeChecker, self).__init__()
        if type_env is None:
            self.type_env = TypeEnv.empty()
        else:
            self.type_env = type_env
        self.defined_types = OrderedDict()
        self.ctors = OrderedDict()
        self.infer_sys = InferSys()
        self.verbose = verbose

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

    @staticmethod
    def is_define_form(form: RExpr):
        if isinstance(form, RList) and len(form.v) > 0 and isinstance(form.v[0], RSymbol):
            return form.v[0].v == 'define'
        return False

    def report_define_infer(self, t: Type, define: IRDef, expr: RExpr) -> (Schema, [ParseError]):
        errors = []


        if define.anno is not None:
            anno = define.anno
            matched, subst = confirm(t, anno)
            # print('origin solved type', t)
            if not matched:
                msg = 'define {} type mismatch, infered {}, but annotation is {}' \
                    .format(define.sym.v, t.apply(subst), anno)
                # print('type of anno', type(anno))
                errors.append(ParseError(expr.span, msg))
                return None, errors
            else:
                # print('type matched')
                # print('flattened anno', anno.flatten())
                if isinstance(anno, TArr) and (any(t is None for t in anno.flatten())):
                    msg = 'define {} type fullfilled, infered {}, annotation is {}' \
                        .format(define.sym.v, t.apply(subst), anno)
                    print(ParseError(expr.span, msg))

        s = self.infer_sys.generalize(t)
        # type_env = type_env.add(define.sym, s)
        if self.verbose:
            if s.is_dummy():
                print('define: {} :: {}'.format(define.sym.v, t))
            else:
                print('define: {} :: {}'.format(define.sym.v, s))
        return s, errors

    def check_content(self, r_exprs: [RExpr], verbose=False) -> \
            ([CodeGen], Set[str], [IRTerm], [ParseError]):
        errors = []
        ir_terms = []
        (other_forms, record_names, types, funcs, code_gens), type_errors = extract_type(r_exprs)
        # types, ctors, type_errors = self.check_types(type_forms)

        if len(type_errors) > 0:
            errors.extend(type_errors)
            return code_gens, record_names, ir_terms, errors

        # infer_sys = InferSys()
        infer_sys = self.infer_sys
        type_env = TypeEnv.default()

        if self.verbose:
            for type_name, t in types.items():
                print("defined type {} :: {}".format(type_name, t))

            for name, t in funcs.items():
                print("get func {} :: {}".format(name, t))

        schemas = []
        schemas.extend(((TVar(name), infer_sys.generalize(t)) for name, t in types.items()))
        schemas.extend(((TVar(name), infer_sys.generalize(t)) for name, t in funcs.items()))

        type_env = type_env.extend(schemas)

        define_forms = [f for f in other_forms if TypeChecker.is_define_form(f)]
        expr_forms = [f for f in other_forms if not TypeChecker.is_define_form(f)]

        all_def = dict()
        all_def_form = dict()

        for define_form in define_forms:
            define, errs = parse_define(define_form)
            ir_terms.append(define)
            errors.extend(errs)

            all_def[define.get_name()] = define
            all_def_form[define.get_name()] = define_form

        dep_graph = DiGraph()

        for k in all_def.keys():
            # print('all_def key', k)
            dep_graph.add_node(k)

        def_names = set(all_def.keys())
        # for def_name in def_names:
            # print('def_name:', def_name)

        for k, v in all_def.items():
            # print('check ref in', v.get_name())
            refs = v.has_ref(def_names)

            # for ref in refs:
                # print(k, 'refs => ', ref)

            for ref in refs:
                dep_graph.add_edge(ref, k)


        comps = list(scc(dep_graph))
        if self.verbose:
            print('comps:', comps)
        shrink = condensation(dep_graph, comps)
        part_indexs = list(topological_sort(shrink))

        for part_index in part_indexs:
            def_group = comps[part_index]
            if len(def_group) == 1:
                def_name = def_group.pop()
                # print('processing def:', def_name)
                define = all_def[def_name]
                expr = all_def_form[def_name]

                if isinstance(define, IRDefine):
                    t, msg = infer_sys.solve_ir_define(type_env, define)
                else:
                    t, msg = infer_sys.solve_var_define(type_env, define)
                # print('t:', t)
                if msg is not None:
                    # print('msg:', msg)
                    errors.append(
                        ParseError(
                                expr.span,
                                'type error, unification error: {}'.format(msg)
                            )
                        )
                    continue

                s, match_errors = self.report_define_infer(t, define, expr)
                errors.extend(match_errors)
                type_env = type_env.add(define.sym, s)
            else:
                def_names = list(def_group)
                defs = [all_def[name] for name in def_names]
                exprs = [all_def_form[name] for name in def_names]
                types, msg = infer_sys.solve_ir_many_def(type_env, defs)
                if msg is not None:
                    errors.append(
                        ParseError(
                                exprs[0].span,
                                'type error, unification error: {}'.format(msg)
                            )
                        )
                    continue
                for (t, _def, expr) in zip(types, defs, exprs):
                    s, match_errors = self.report_define_infer(t, _def, expr)
                    errors.extend(match_errors)
                    type_env = type_env.add(_def.sym, s)

        # finish at here

        for expr_form in expr_forms:
            ir_expr, errs = parse_ir_expr(expr_form)
            ir_terms.append(ir_expr)
            errors.extend(errs)
            if len(errors) > 0:
                continue
            t, msg = infer_sys.solve_ir_expr(type_env, ir_expr)
            if msg is not None:
                msg = "type error, unification error {}".format(msg)
                errors.append(ParseError(expr_form.span, msg))
                continue
            if self.verbose:
                print('expr: {} :: {}'.format(ir_expr.to_raw(), t))

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

    checker = TypeChecker(verbose=not SILENT)
    _, _, _, errors = checker.check_content(r_exprs, verbose=not SILENT)
    if len(errors) > 0:
        for error in errors:
            print(error)


if __name__ == '__main__':
    main()
