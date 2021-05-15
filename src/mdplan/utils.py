from functools import reduce
import math

def build_tree(nodes):
    """
    Builds a tree from a list of nodes, each a dict with 'level' and 'value'.
    A tree is a tuple of shape (value, subtrees).
    Also returns remaining nodes.
    """
    if not nodes:
        return []
    value = nodes[0]['value']
    base_level = nodes[0]['level']
    nodes = nodes[1:]
    subtrees = []
    while nodes and nodes[0]['level']>base_level:
        subtree, nodes = build_tree(nodes)
        subtrees.append(subtree)
    tree = (value, subtrees)
    return tree, nodes

def build_trees(nodes):
    # builds a list of trees
    trees = []
    while nodes:
        tree, nodes = build_tree(nodes)
        trees.append(tree)
    return trees

def gcd(*numbers):
    return reduce(math.gcd, numbers)

def find_groups(string, grouper):
    """
    Returns a list of texts enclosed in grouper.

    E.g.
        find_groups('hello {there}', '{}') -> ['there']
    """
    starter = grouper[0]
    finisher = grouper[1]
    groups = []
    while starter in string:
        i1 = string.index(starter)+len(starter)
        i2 = string.index(finisher)
        groups.append(string[i1:i2])
        string = string[i2+1:]
    return groups

def is_readable(obj):
    return hasattr(obj, 'readable') and callable(obj.readable) and obj.readable()

def is_path(obj):
    try:
        obj.exists()
        obj.is_file()
        return hasattr(obj, 'read_text') and callable(obj.read_text)
    except AttributeError:
        return False

def is_datetime(obj):
    return hasattr(obj, 'day') and hasattr(obj, 'hour')

def is_date(obj):
    return hasattr(obj, 'day') and not (hasattr(obj, 'hour'))

def is_time(obj):
    return hasattr(obj, 'hour') and not (hasattr(obj, 'day'))