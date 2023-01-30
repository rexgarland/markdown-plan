import argparse
from pathlib import Path

from .git.history import GitHistory
from .git.plot import GitPlot

description = """
A tool for analyzing markdown plans
"""

epilog = """
Analysis details:
* history: parses the git history of a plan file, outputting version statistics as JSON
* plot: opens a browser to display a plan's history (as a burn-up chart)
 
"""


def main():
    parser = argparse.ArgumentParser(
        description=description,
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "command", choices=["history", "plot"], help="the type of analysis to run"
    )
    parser.add_argument(
        "planfile",
        type=Path,
        help="the path to a markdown plan",
    )
    args = parser.parse_args()

    if args.command == "history":
        history = GitHistory(args.planfile)
        print(history.to_json())
    if args.command == "plot":
        history = GitHistory(args.planfile)
        plot = GitPlot(history)
        plot.open()


if __name__ == "__main__":
    main()
