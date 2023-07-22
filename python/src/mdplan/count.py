from typing import Optional

from .tree import Node, Tree
from .task import Task
from .parse import parse_tree


def trickle_completion(tree: Tree[Task]):
    """
    Trickle-down completion from parent to children.
    If a node is done, all its progeny are also marked done.
    """

    def recurse(node: Node[Task], done: Optional[bool] = None):
        if done:
            node.value.done = True
        for child in node.children:
            recurse(child, done=node.value.done)

    for root in tree.roots:
        recurse(root)


def count_all_tasks(plan):
    tree = parse_tree(plan)
    return len(tree.leaves)


def count_remaining_tasks(plan):
    tree = parse_tree(plan)
    trickle_completion(tree)
    remaining_tasks = [leaf.value for leaf in tree.leaves if not leaf.value.done]
    return len(remaining_tasks)
