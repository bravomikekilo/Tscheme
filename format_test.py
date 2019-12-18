from argparse import ArgumentParser
from parsing import raw_atom, whole_program


parser = ArgumentParser(description='test script for formatter')
parser.add_argument('src', type=str)

ARGS = parser.parse_args()
SRC_PATH = ARGS.src
with open(SRC_PATH, 'r') as f:
    SRC = f.read()

atoms = whole_program.parse(SRC)
print()
for atom in atoms:
    print(atom.pretty_print())


