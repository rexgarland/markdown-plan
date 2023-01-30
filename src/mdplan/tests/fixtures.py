from pytest import fixture
from tempfile import TemporaryDirectory
from os.path import dirname
from pathlib import Path
import tarfile

this_folder = dirname(__file__)

config_flat = {
    "repo_folder": "example_repo",
    "repo_archive": "data/example_repo.tar.gz",
    "plan_file": "test.plan.md",
}

config_nested = {
    "repo_folder": "nested_repo",
    "repo_archive": "data/nested_repo.tar.gz",
    "plan_file": "plans/test.plan.md",
}


def clone_repo(config, folder):
    archive_path = Path(this_folder) / config["repo_archive"]
    tar = tarfile.open(archive_path)
    tar.extractall(folder)
    return Path(folder) / config["repo_folder"]


@fixture
def repo():
    with TemporaryDirectory() as tmpdir:
        repodir = clone_repo(config_flat, tmpdir)
        yield str(repodir)


@fixture
def plan(repo):
    return str(Path(repo) / config_flat["plan_file"])


@fixture
def repo_nested():
    with TemporaryDirectory() as tmpdir:
        repodir = clone_repo(config_nested, tmpdir)
        yield str(repodir)


@fixture
def plan_nested(repo_nested):
    return str(Path(repo_nested) / config_nested["plan_file"])
