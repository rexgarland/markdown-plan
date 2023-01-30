from dataclasses import dataclass
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
import pygit2
import json

from ..tree import Tree
from ..task import Task
from ..parse import parse_tree
from ..count import count_all_tasks, count_remaining_tasks


@dataclass
class TaskStatistics:
    total: int
    completed: int

    def as_data(self):
        data = {"total": self.total, "completed": self.completed}
        return data


class GitVersion:
    commit: pygit2.Commit
    source: str

    def __init__(self, commit, source):
        self.commit = commit
        self.source = source

    def __iter__(self):
        yield self

    @property
    def tree(self) -> Tree[Task]:
        return parse_tree(self.source)

    @property
    def datetime(self) -> datetime:
        timestamp = self.commit.commit_time
        offset = self.commit.commit_time_offset
        tz = timezone(timedelta(minutes=offset))
        return datetime.fromtimestamp(timestamp, tz)

    @property
    def task_statistics(self) -> TaskStatistics:
        total = count_all_tasks(self.source)
        completed = total - count_remaining_tasks(self.source)
        return TaskStatistics(total=total, completed=completed)

    def as_data(self):
        data = {
            "date": self.datetime.isoformat(),
            "tasks": self.task_statistics.as_data(),
        }
        return data


def is_repo(folder: Path):
    gitdir = folder / ".git"
    return gitdir.exists()


def find_closest_repo(path: Path):
    for folder in path.parents:
        if is_repo(folder):
            return folder
    raise Exception("Could not find a git repo containing '{path}'")


class GitHistory(Sequence):
    plan: Path
    repo: Path
    versions: list[GitVersion]

    def __init__(self, planfile):
        self.plan = Path(planfile).absolute()
        self.repo = find_closest_repo(self.plan)
        self.find_versions()

        super().__init__()

    def __getitem__(self, index):
        return self.versions[index]

    def __len__(self):
        return len(self.versions)

    def read_source_from_commit(self, commit: pygit2.Commit) -> Optional[str]:
        tree = commit.tree
        relpath = self.plan.relative_to(self.repo)
        try:
            blob = tree[str(relpath)]
            if blob:
                return blob.data.decode("utf-8")
        except:
            pass

    def find_versions(self):
        self.versions = []
        repo = pygit2.Repository(self.repo)
        for commit in repo.walk(repo.head.target):
            source = self.read_source_from_commit(commit)
            if source:
                version = GitVersion(commit, source)
                self.versions.append(version)
        self.versions.sort(key=lambda v: v.datetime)

    def to_json(self) -> str:
        data = {"versions": [version.as_data() for version in self.versions]}
        return json.dumps(data)
