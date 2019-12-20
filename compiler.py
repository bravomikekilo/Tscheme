from typing import Set
from type_check import TypeChecker
from argparse import ArgumentParser
from parsing import whole_program
from code_gen import gen_ctor_define


class CompileContext(object):

    def __init__(self, record_names: Set[str]):
        super(CompileContext, self).__init__()
        self.record_names = record_names


def main():
    parser = ArgumentParser(description='script used to compile typed scheme to racket')
    parser.add_argument('script', help='path to script')
    parser.add_argument('--output', help='path to output file', default='out.rkt')
    parser.add_argument('--silent', action='store_true', help='slient success output')

    ARGS = parser.parse_args()
    SCRIPT_PATH = ARGS.script
    SILENT = ARGS.silent
    OUTPUT_PATH = ARGS.output

    with open(SCRIPT_PATH, 'r') as f:
        SRC = f.read()

    r_exprs = whole_program.parse(SRC)

    checker = TypeChecker()
    code_gens, record_names, ir_terms, errors = checker.check_content(r_exprs, verbose=not SILENT)

    if len(errors) > 0:
        for error in errors:
            print(error)

    compiled_forms = []
    for code_gen in code_gens:
        # ctor_gen = gen_ctor_define(ctor_name, ctor_type)
        compiled_forms.append(code_gen.code_gen())

    context = CompileContext(record_names)

    for ir_term in ir_terms:
        compiled_forms.append(ir_term.to_racket(env=context))

    with open(OUTPUT_PATH, 'w') as out_f:
        out_f.write('#lang racket\n\n')
        for form in compiled_forms:
            print('form:', form)
            out_f.write(form.pretty_print())
            out_f.write('\n')


if __name__ == '__main__':
    main()



