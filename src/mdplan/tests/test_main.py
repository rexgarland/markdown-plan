import json

from .fixtures import *

from ..git.history import GitHistory

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
