from ..count import count_all_tasks, count_remaining_tasks


def test_counts_a_flat_list():
    plan = """1. first task
2. second"""
    num = count_remaining_tasks(plan)

    assert num == 2


def test_only_counts_leaves_as_remaining_tasks():
    plan = """
1. create plan
    - this is one step
    - here is another
2. edit plan
    - something
"""
    num = count_remaining_tasks(plan)

    assert num == 3, "should not count the parent tasks"


def test_does_not_count_completed_tasks():
    plan = """
1. [x] this is done
2. remaining work
"""
    num = count_remaining_tasks(plan)

    assert num == 1


def test_does_not_count_subtasks_of_finished_parent():
    plan = """
1. [x] parent
  - sub1
  - sub2"""
    num = count_remaining_tasks(plan)

    assert num == 0


def test_counts_all_tasks():
    plan = """
1. [x] first thing
    - do this
    - then that
2. finall, do this"""
    num = count_all_tasks(plan)

    assert num == 3
