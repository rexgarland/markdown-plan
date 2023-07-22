from dataclasses import dataclass


@dataclass
class Task:
    """
    A description of work
    """

    description: str
    done: bool
    dependencies: list[str]
