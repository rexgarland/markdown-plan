from datetime import date, datetime
from pathlib import Path

from .gantt import GanttDuration, GanttEvent
from . import parse
from . import utils

NOW = datetime.now()
TODAY = date.today()

class Task:
    """
    This class handles the data structure of a single task.

    Check out parse.py to see how a task is created from a string.
    """
    def __init__(self,
                description,
                string=None,
                level=None,
                estimate=None,
                measurements=[],
                start=None,
                finish=None,
                deadline=None,
                is_completed=False,
                is_ordered=False,
                dependencies=None,
                parent=None,
                children=None,
                file=None):
        self.description = description
        self.string = string
        self.level = int(level)
        self.measurement = sum([Measurement(m) for m in measurements]) if measurements else None
        self.estimate = Estimate(estimate) if estimate else None
        self.deadline = deadline
        self.start = start
        self.finish = finish
        self.parent = parent
        self.is_ordered = is_ordered
        if not children:
            children = set()
        self.children = set(children)
        if not dependencies:
            dependencies = set()
        self.dependencies = set(dependencies)
        self.file = file
        self._is_completed = is_completed

    @property
    def type(self):
        if self.estimate:
            return self.estimate.type
        return None

    @property
    def total_duration(self):
        possible = [self.estimate.nominal.hours if self.estimate else 0]
        possible += [self.completed_duration.hours]
        return GanttDuration(value=max(possible), scale='hours')

    @property
    def completed_duration(self):
        if self.has_start:
            return GanttEvent(datetime=NOW)-self.start
        hours = self.measurement.hours if self.measurement else 0
        return GanttDuration(value=hours, scale='hours')

    @property
    def remaining_duration(self):
        return self.total_duration-self.completed_duration

    @property
    def is_timed(self):
        return bool(self.estimate or self.measurement or self.start or self.finish)

    @property
    def is_wait(self):
        return self.type == 'wait'

    def __repr__(self):
        return f"Task '{self.description}' in file '{self.file}'"

    @property
    def ancestors(self):
        t = self
        a = []
        while t.parent:
            a.append(t.parent)
            t = t.parent
        return a

    @property
    def has_start(self):
        return not (self.start is None)

    @property
    def has_finish(self):
        return not (self.finish is None)

    @property
    def has_deadline(self):
        return not (self.deadline is None)

    @property
    def deadline(self):
        return self._deadline
    
    @deadline.setter
    def deadline(self, value):
        self._deadline = Deadline(value) if value else None

    @property
    def start(self):
        return self._start
    
    @start.setter
    def start(self, value):
        self._start = Start(value) if value else None

    @property
    def finish(self):
        return self._finish
    
    @finish.setter
    def finish(self, value):
        self._finish = Finish(value) if value else None

    @property
    def is_completed(self):
        return self._is_completed or self.has_finish

    @is_completed.setter
    def is_completed(self, value):
        assert value==bool(value), "Cannot assign non-boolean to 'is_completed'"
        self._is_completed = value

    @property
    def type(self):
        if not self.estimate:
            return None
        return self.estimate.type
    
    @property
    def is_todo(self):
        # has not been started or completed
        return not (self.has_start or self.is_completed)

class Estimate:
    def __init__(self, string):
        self.string = string
        if parse.is_wait(string):
            self.type = 'wait'
            string = string.strip()[4:]
        else:
            self.type = 'work'
        value, self.scale = parse.parse_estimate(string)
        self._value = self.Value(value, self.scale)

    class Value:
        def __init__(self, value, scale):
            self.nominal = GanttDuration(value=value, scale=scale)
            self.min = self.nominal
            self.max = self.nominal

    @property
    def min(self):
        return self._value.min

    @property
    def max(self):
        return self._value.max

    @property
    def nominal(self):
        return self._value.nominal

class Measurement(GanttDuration):
    def __init__(self, string):
        assert parse.is_measurement(string)
        if parse.is_interval(string):
            value = parse.parse_time_interval(string)
            scale = 'hours'
        else:
            string, scale = parse.parse_string_and_scale(string)
            value = float(string)
        super().__init__(value=value, scale=scale)

def match_parse_or_default(matcher, parser, default):
    def func(obj):
        if matcher(obj):
            return parser(obj)
        return default(obj)
    return func

def try_parse(parser):
    def func(string):
        try:
            return parser(string)
        except:
            raise ValueError(f'Could not parse string "{string}"')
    return func

class Deadline(GanttEvent):
    def __init__(self, obj=None, **kwargs):
        super().__init__(obj, **kwargs)

class Start(GanttEvent):
    def __init__(self, obj=None, **kwargs):
        self.is_match = parse.is_start
        self.parse = parse.parse_start
        super().__init__(obj=obj, **kwargs)
        assert self<=GanttEvent(datetime=NOW) or self<=GanttEvent(date=TODAY), "Start must be specified in the past"

class Finish(GanttEvent):
    def __init__(self, obj=None, **kwargs):
        self.is_match = parse.is_finish
        self.parse = parse.parse_finish
        super().__init__(obj=obj, **kwargs)
        assert self<=GanttEvent(datetime=NOW) or self<=GanttEvent(date=TODAY), "Finish must be specified in the past"

def parse_line(line, **kwargs):
    description = parse.get_description(line)
    estimate = parse.get_estimate(line)
    measurements = parse.get_measurements(line)
    deadline = parse.get_deadline(line)
    start = parse.get_start(line)
    finish = parse.get_finish(line)
    is_ordered = parse.is_ordered(line)
    dependencies = parse.get_dependencies(line)
    is_completed = parse.is_completed(line)
    t = Task(description, string=line, estimate=estimate, measurements=measurements, deadline=deadline, start=start, finish=finish, is_ordered=is_ordered, is_completed=is_completed, **kwargs)
    return t, dependencies


    
    