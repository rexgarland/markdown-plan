import argparse
from pathlib import Path

from .dag import convert_to_dag

def is_plan(f):
    return f.endswith('.plan.md') and Path(f).is_file()

def main():
    parser = argparse.ArgumentParser('Convert a markdown plan to a JSON DAG.')
    parser.add_argument('file', type=str)
    parser.add_argument('--output', default=None)
    args = parser.parse_args()

    outfile = convert_to_dag(args.file, jsonfile=args.output)
    print(outfile)

if __name__=='__main__':
    main()