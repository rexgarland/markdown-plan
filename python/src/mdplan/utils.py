from functools import reduce
import math


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
        i1 = string.index(starter) + len(starter)
        i2 = string.index(finisher)
        groups.append(string[i1:i2])
        string = string[i2 + 1 :]
    return groups


def pipe(functions):
    return lambda x: reduce(lambda a, v: v(a), functions, x)
