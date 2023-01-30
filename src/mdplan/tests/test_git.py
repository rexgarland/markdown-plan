from os import listdir

from .fixtures import *

from ..git.history import GitHistory


def test_finds_multiple_versions(plan):
    history = GitHistory(plan)
    assert len(history) > 1


def test_finds_source(plan):
    history = GitHistory(plan)
    v1 = history[0]
    assert (
        v1.source
        == """# Test plan

1. write a test
2. watch it fail
3. make it pass
"""
    )


def test_finds_source_from_subdirectory(plan_nested):
    history = GitHistory(plan_nested)
    v1 = history[0]
    assert v1.source


def test_finds_correct_dates(plan):
    history = GitHistory(plan)
    date_strings = [version.datetime.isoformat() for version in history[:5]]
    assert date_strings == [
        "2023-01-16T00:00:00+00:00",
        "2023-01-17T00:00:00+00:00",
        "2023-01-18T00:00:00+00:00",
        "2023-01-19T00:00:00+00:00",
        "2023-01-21T00:00:00+00:00",
    ]


def test_finds_correct_statistics(plan):
    history = GitHistory(plan)

    total = [v.task_statistics.total for v in history[:5]]
    assert total == [3, 4, 4, 5, 5]

    completed = [v.task_statistics.completed for v in history[:5]]
    assert completed == [0, 0, 1, 2, 5]
