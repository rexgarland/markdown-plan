from ..tree import TreeBuilder


class TestTreeBuilder:
    def test_connects_two_levels(self):
        builder = TreeBuilder()
        a = builder.add("a", indent=0)
        b = builder.add("b", indent=1)
        assert b.parent == a

    def test_connects_three_levels(self):
        builder = TreeBuilder()
        builder.add("a", indent=0)
        b = builder.add("b", indent=1)
        c = builder.add("c", indent=2)
        assert c.parent == b

    def test_multiple_siblings_to_parent(self):
        builder = TreeBuilder()
        a = builder.add("a", indent=0)
        b = builder.add("b", indent=1)
        c = builder.add("c", indent=1)
        assert b.parent == a
        assert c.parent == a

    def test_parse_correctly_when_root_is_none(self):
        builder = TreeBuilder()
        builder.add("a", indent=0)
        builder.add("b", indent=1)
        c = builder.add("c", indent=0)
        d = builder.add("d", indent=1)
        assert c.parent == None
        assert d.parent == c
