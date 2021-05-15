import argparse
from pathlib import Path

from .render import render

def is_plan(f):
    return f.endswith('.plan.md') and Path(f).is_file()

def main():
    parser = argparse.ArgumentParser('View files in markdown-plan.')
    parser.add_argument('files', type=str, nargs='+')
    args = parser.parse_args()

    renderable_files = filter(is_plan, args.files)
    assert renderable_files, "No markdown plans found in files specified."

    render(files=renderable_files)

if __name__=='__main__':
    main()