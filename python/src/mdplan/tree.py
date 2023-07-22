from typing import Generic, Optional, Set, Tuple, TypeVar

V = TypeVar("V")


class Node(Generic[V]):
    value: V
    parent: Optional["Node[V]"]
    children: Set["Node"]

    def __init__(self, value):
        self.value = value
        self.parent = None
        self.children = set()

    @classmethod
    def adopt(cls, parent: "Node", child: "Node"):
        parent.children.add(child)
        child.parent = parent


class Tree(Generic[V]):
    nodes: Set[Node[V]]

    def __init__(self, nodes: list[Node[V]]):
        self.nodes = set(nodes)

    @property
    def leaves(self) -> Set[Node[V]]:
        s = set([node for node in self.nodes if len(node.children) == 0])
        return s

    @property
    def roots(self) -> Set[Node[V]]:
        return set([node for node in self.nodes if node.parent == None])


Ancestor = Tuple[Node[V], int]  # node and its indentation level


class TreeBuilder(Generic[V]):
    """
    Builds a tree from a list of indented values
    """

    curr_lineage: list[Ancestor[V]]

    def __init__(self):
        self.curr_lineage = []

    def find_placement_in_lineage(self, indent: int) -> int:
        i = 0
        while i < len(self.curr_lineage) and self.curr_lineage[i][1] < indent:
            i += 1
        return i

    def place_in_lineage(self, node: Node[V], indent: int) -> Optional[Ancestor[V]]:
        i = self.find_placement_in_lineage(indent)
        self.curr_lineage[i:] = [(node, indent)]

    def add(self, value: V, indent: int) -> Node[V]:
        node = Node(value)
        self.place_in_lineage(node, indent)

        node_has_parent = len(self.curr_lineage) > 1
        if node_has_parent:
            parent, _ = self.curr_lineage[-2]
            Node.adopt(parent, node)  # connect the two nodes

        return node


def build_tree_from_indents(values, indents) -> Tree:
    builder = TreeBuilder()
    nodes = []
    for (value, indent) in zip(values, indents):
        node = builder.add(value, indent=indent)
        nodes.append(node)

    return Tree(nodes)
