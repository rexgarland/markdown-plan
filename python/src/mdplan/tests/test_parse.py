from ..parse import is_task, parse_task, parse_tree


class TestIsTask:
    def test_recognizes_list_item(self):
        line = "- hello"
        assert is_task(line)
        line = "1. hello"
        assert is_task(line), "Could not recognize numbered task"
        line = "  1. hello"
        assert is_task(line), "Could not recognize task with indentation"

    def test_recognizes_header(self):
        line = "# hello"
        assert is_task(line)
        line = "## hello"
        assert is_task(line), "Could not recognize h2 as task"

    def test_ignores_block_quote(self):
        line = "> * hello"
        assert not is_task(line)

    def test_ignores_horizontal_line(self):
        line = "***"
        assert not is_task(line)


class TestParseTask:
    def test_captures_description(self):
        line = "  - hello @(world)"
        task = parse_task(line)
        assert task.description == "hello"

    def test_description_excludes_done(self):
        line = "- [x] hello"
        task = parse_task(line)
        assert task.description == "hello"

    def test_description_excludes_empty_checkbox(self):
        line = "- [ ] hello"
        task = parse_task(line)
        assert task.description == "hello"

    def test_captures_is_done(self):
        line = "- [x] hello"
        task = parse_task(line)
        assert task.done

    def test_captures_empty_done(self):
        line = "- [ ] hello"
        task = parse_task(line)
        assert not task.done

    def test_captures_dependencies(self):
        line = "- [x] hello @(world, universe)"
        task = parse_task(line)
        assert "world" in task.dependencies
        assert "universe" in task.dependencies


class TestParseTree:
    def test_contains_appropriate_leaves(self):
        plan = """
- one
  - two
"""
        tree = parse_tree(plan)
        assert len(tree.leaves) == 1
        assert tree.leaves.pop().value.description == "two"

    def test_correctly_finds_children(self):
        plan = """
- parent
  - child1
  - child2
"""
        tree = parse_tree(plan)
        parent = [node for node in tree.nodes if node.value.description == "parent"][0]
        assert len(parent.children) == 2

    def test_ignores_code_blocks(self):
        plan = """
- task1
```
- task2
```
"""
        tree = parse_tree(plan)
        assert len(tree.nodes) == 1

    def test_allows_for_indentation_jumps(self):
        # some markdown formatters do this by default
        plan = """
1. first
   - second
     - third
   - fourth
"""
        tree = parse_tree(plan)
        assert len(tree.roots) == 1
        assert len(tree.leaves) == 2
        first = tree.roots.pop()
        assert len(first.children) == 2
        third = (tree.leaves - first.children).pop()
        assert third
