import json

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


expected_data = {
    "versions": [
        {"date": "2023-01-16T00:00:00+00:00", "tasks": {"total": 3, "completed": 0}},
        {"date": "2023-01-17T00:00:00+00:00", "tasks": {"total": 4, "completed": 0}},
        {"date": "2023-01-18T00:00:00+00:00", "tasks": {"total": 4, "completed": 1}},
        {"date": "2023-01-19T00:00:00+00:00", "tasks": {"total": 5, "completed": 2}},
        {"date": "2023-01-21T00:00:00+00:00", "tasks": {"total": 5, "completed": 5}},
    ]
}
expected_json = json.dumps(expected_data)


def test_renders_correct_json_history(plan):
    history = GitHistory(plan)
    json = history.to_json()
    assert json == expected_json

def test_does_not_crash_if_encountering_unparseable_commit(plan_with_bad_commit):
    history = GitHistory(plan_with_bad_commit)
    json = history.to_json() # This could fail because one of the commit has a bad indent. See git log in test repo folder.