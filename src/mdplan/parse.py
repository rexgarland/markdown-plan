from datetime import date, datetime
import re

from . import utils
from .task import Task
from .tree import Tree, build_tree_from_indents

TODAY = date.today()
NOW = datetime.now()


WHITESPACE = [" ", "\t"]


def get_initial_white(string):
    text = ""
    for char in string:
        if char in WHITESPACE:
            text += char
        else:
            return text
    return ""


LIST_MARKERS = ["*", "-"]


def is_header(word):
    return all([c == "#" for c in word])


def is_task(line):
    # task lines must start with a marker (after any initial indent whitespace)
    stripped = line.strip()
    if not stripped:
        return False
    first_word = stripped.split(" ")[0]
    if first_word in LIST_MARKERS:
        return True
    if is_header(first_word):
        return True
    if first_word[0].isnumeric() and first_word[-1] == ".":
        return all([c.isnumeric() for c in first_word[:-1]])
    return False


def get_dependencies(string):
    groups = utils.find_groups(string, ["@(", ")"])
    if not groups:
        return []
    assert len(groups) == 1
    string = groups[0]
    splits = string.split(",")
    return [split.strip() for split in splits]


def is_done(line):
    for text in utils.find_groups(line, "[]")[:1]:
        if text == "x":
            return True
    return False


def indent_level(line, single_indent="\t"):
    stripped_line = line.strip()
    first_printable = stripped_line[0]
    first_index = line.index(first_printable)
    level = line[:first_index].count(single_indent)
    return level


def calculate_nesting_level(line, single_indent="\t"):
    """
    Returns the nesting level.

    For headers, it is negative, with -6 being h1 and -1 being h6.
    For list items, it is non-negative, starting at 0 for no indentation.
    """
    stripped_line = line.strip()
    first_printable = stripped_line[0]
    if first_printable == "#":
        num_hashes = stripped_line.split(" ")[0].count("#")
        return -7 + num_hashes
    else:
        return indent_level(line, single_indent)


def get_description(content):
    start, end = 0, len(content)
    if is_done(content):
        start = 3
    elif content.startswith("[ ]"):
        start = 3
    if re.search(r"""@\(.*\)""", content):
        end = content.find("@(")
    return content[start:end].strip()


def infer_indent(text) -> str:
    lines = text.split("\n")
    indents = [get_initial_white(line) for line in lines if is_task(line)]
    indents = [indent for indent in indents if indent]
    if not indents:
        return "\t"  # default
    chartype = indents[0][0]
    together = "".join(indents)
    assert together.count(chartype) == len(together), "Indentation must be consistent"
    counts = {len(indent) for indent in indents}
    return utils.gcd(*counts) * chartype


def lstrip(chars):
    def strip_fn(text):
        index = 0
        while index < len(text) and text[index] in chars:
            index += 1
        return text[index:]

    return strip_fn


def strip_headers(line):
    return lstrip(["#"])(line)


def strip_list_markers(line):
    if line:
        if line[0] == "-":
            return line[1:]
        if line[0].isnumeric():
            no_left_numbers = lstrip("1234567890")(line)
            if no_left_numbers and no_left_numbers[0] == ".":
                return no_left_numbers[1:]
    return line


def strip_left_whitespace(line):
    return lstrip([" ", "\t"])(line)


def strip_markdown(line):
    return utils.pipe(
        [
            strip_left_whitespace,
            strip_headers,
            strip_list_markers,
            strip_left_whitespace,
        ]
    )(line)


def parse_task(line):
    content = strip_markdown(line)
    done = is_done(content)
    description = get_description(content)
    dependencies = get_dependencies(content)
    return Task(description=description, done=done, dependencies=dependencies)


def sliding_pairs(arr: list):
    return [(arr[i], arr[i + 1]) for i in range(len(arr) - 1)]


def is_code_block_delimiter(line):
    return line.startswith("```")


def remove_code_blocks(lines: list[str]) -> list[str]:
    out = []
    in_code_block = False
    for line in lines:
        if in_code_block:
            if is_code_block_delimiter(line):
                in_code_block = False
        else:
            if is_code_block_delimiter(line):
                in_code_block = True
            else:
                out.append(line)
    return out


def parse_tree(plan: str) -> Tree[Task]:
    indent = infer_indent(plan)
    lines = plan.splitlines()
    lines = remove_code_blocks(lines)
    filtered_lines = [line for line in lines if is_task(line)]
    indents = [calculate_nesting_level(line, indent) for line in filtered_lines]
    tasks = [parse_task(line) for line in filtered_lines]
    tree = build_tree_from_indents(tasks, indents)
    return tree
