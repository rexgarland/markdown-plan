from pathlib import Path

from . import utils
from . import parse
from .task import Task, parse_line

def get_text_forgiving(obj):
    if type(obj) is str:
        return obj
    elif utils.is_path(obj):
        assert obj.exists() and obj.is_file(), f'Could not find object "{obj}"'
        return obj.read_text()
    else:
        raise Exception(f"Object of type {type(obj)} is not valid plan data: {obj}")

def has_cycle(task, visited, on_stack):
    visited[task] = True
    on_stack[task] = True
    for dep in task.dependencies:
        if not visited[dep]:
            res = has_cycle(dep, visited, on_stack)
            if res:
                return res
        elif on_stack[dep]:
            return dep
    on_stack[task] = False
    return None

def get_cycle(path):
    first = path[0]
    last = path[-1]
    if len(path)>1 and first==last:
        return path
    for dep in last.dependencies:
        cyc = get_cycle(path+[dep])
        if cyc:
            return cyc
    return None

def split_dependency(dep):
    if ':' in dep:
        splits = dep.split(':')
        assert len(splits)==2
        filepart = splits[0].strip()
        taskpart = splits[1].strip()
    elif '/' in dep:
        filepart = dep.strip()
        taskpart = ''
    else:
        filepart = None
        taskpart = dep.strip()
    if not filepart:
        filepart = None
    if not taskpart:
        taskpart = None
    return filepart, taskpart

def link_parents_with_children(trees):
    '''Create parent-child relationships in task objects based on tree-structured nodes.'''
    def recurse(trees, parent=None):
        if not trees:
            return
        for (task, subtrees) in trees:
            task.parent = parent
            if parent:
                parent.children.add(task)
            recurse(subtrees, parent=task)
    recurse(trees)

def link_ordered_siblings(trees):
    '''Create list-ordering dependencies.'''
    def recurse(trees):
        if not trees:
            return
        last_ordered = None
        for (task, subtrees) in trees:
            if task.is_ordered:
                if last_ordered:
                    task.dependencies.add(last_ordered)
                last_ordered = task
            recurse(subtrees)
    recurse(trees)

def append_plan_extension(path):
    path = Path(path)
    if path.name[-8:]!='.plan.md':
        path = path.parent / (path.stem + '.plan.md')
    return path

def recurse_dep_tree(task, func):
    for dep in task.dependencies:
        func(dep)
        recurse_dep_tree(dep, func)

class Plan:
    def __init__(self, text=None, file=None, files=[]):
        self.tasks = []
        self.dependencies = {}
        if text:
            self.add_tasks(text)
        if file:
            files = [file] + files
        for f in files:
            f = append_plan_extension(f)
            f = f.expanduser().resolve()
            self.add_tasks(f)
        self.recurse_completion()
        self.resolve_dependencies()
        self.validate_deadlines()

    @property
    def root_tasks(self):
        parentless = [t for t in self.tasks if not t.parent]
        return parentless

    @property
    def todo_tasks(self):
        return [t for t in self.tasks if t.is_todo]

    @property
    def completed_tasks(self):
        return [t for t in self.tasks if t.is_completed]

    @property
    def waiting_tasks(self):
        return [t for t in self.tasks if t.has_start]

    @property
    def upcoming_deadline_tasks(self):
        return [t for t in self.tasks if t.is_todo and t.has_deadline]

    @property
    def deadlines_for_task(self):
        if not hasattr(self, '_deadlines_for_task'):
            self._deadlines_for_task = {task: set() for task in self.tasks}
            for task in self.upcoming_deadline_tasks:
                def recurse(t):
                    self._deadlines_for_task[t].add(task)
                    for dep in t.dependencies:
                        recurse(dep)
                recurse(task)
        return self._deadlines_for_task
    
    
    def add_tasks(self, obj):
        text = get_text_forgiving(obj)
        task_kwargs = {}
        if type(obj) is str:
            task_kwargs['file_id'] = str(hash(obj))
        else:
            path = Path(obj).resolve()
            assert path.exists()
            task_kwargs['file'] = path
        indent = parse.infer_indent(text)
        # build nodes
        nodes = []
        in_code_block = False
        for line in text.split('\n'):
            if parse.is_code_block_delimiter(line):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue
            if parse.is_task(line):
                level = parse.get_level(line, indent=indent)
                task, dependencies = parse_line(line, level=level, **task_kwargs)
                self.tasks.append(task)
                self.dependencies[task] = dependencies
                nodes += [{'level': level, 'value': task}]
        trees = utils.build_trees(nodes)
        link_parents_with_children(trees)
        link_ordered_siblings(trees)

    def recurse_completion(self):
        roots = self.root_tasks
        def recurse(task, parent_completed=False):
            if parent_completed:
                task.is_completed = True
            for child in task.children:
                recurse(child, parent_completed=task.is_completed)
        for root in roots:
            recurse(root)

    def resolve_dependencies(self):
        self.link_dependencies()
        self.lift_dependencies()
        self.trickle_dependencies()
        self.trim_dependencies()

    def link_dependencies(self):
        '''Creates links to task objects based on string references'''
        for task in self.tasks:
            for string in self.dependencies[task]:
                filepart, taskpart = split_dependency(string)
                if not filepart:
                    fref = task.file
                else:
                    assert utils.is_path(task.file)
                    refpath = task.file.parent / append_plan_extension(filepart)
                    refpath = refpath.resolve()
                    assert refpath.exists(), f"Cannot resolve file '{refpath}' for dependency '{string}'"
                    fref = refpath
                possible = [newtask for newtask in self.tasks if newtask!=task and newtask.file==fref and (taskpart in newtask.description)]
                assert possible, f"Cannot resolve dependency '{string}' in file '{task.file}'"
                assert len(possible)==1, f"Mutliple tasks found matching dependency '{string}'"
                task.dependencies.add(possible[0])

    def lift_dependencies(self):
        """Lifts unrelated dependencies to the nearest timed ancestor, if one exists"""
        self.validate_no_multiple_timed_lineages()
        for task in self.tasks:
            for dep in task.dependencies:
                if (dep in task.parent.children) or (task in dep.ancestors):
                    continue
                if not dep.is_timed:
                    timed_ancestors = [a for a in dep.ancestors if a.is_timed]
                    if timed_ancestors:
                        assert len(timed_ancestors)==1
                        task.dependencies.remove(dep)
                        task.dependencies.add(timed_ancestors[0])

    def trickle_dependencies(self):
        """
        1) Give parent dependencies to its children, recursively
        2) Then, parents should depend on children to finish.
        """
        parents = set(self.root_tasks)
        while parents:
            parent = parents.pop()
            # (1)
            for child in parent.children:
                for dep in parent.dependencies:
                    child.dependencies.add(dep)
            # (2)
            for child in parent.children:
                parent.dependencies.add(child)
            # recurse
            for child in parent.children:
                parents.add(child)

    def trim_dependencies(self):
        """Remove chronologically-redundant dependencies"""
        self.validate_no_circular_dependencies()
        for task in self.tasks:
            to_visit = set(task.dependencies)
            while to_visit:
                dep = to_visit.pop()
                def trim(t):
                    if t in task.dependencies:
                        task.dependencies.remove(t)
                        if t in to_visit:
                            to_visit.remove(t)
                recurse_dep_tree(dep, trim)

    def validate_no_circular_dependencies(self):
        visited = {task: False for task in self.tasks}
        for task in self.tasks:
            recStack = {task: False for task in self.tasks}
            if not visited[task]:
                c = has_cycle(task, visited, recStack)
                if c:
                    cyc = get_cycle([c])
                    descriptions = [task.description for task in cyc]
                    path = ' => '.join([f'"{d}"' for d in descriptions])
                    raise Exception(f'Found cyclic dependencies: ({path})')

    def validate_no_multiple_timed_lineages(self):
        '''Verify that for every timed task, no ancestors are also timed'''
        for task in self.tasks:
            if task.is_timed:
                assert not any([t.is_timed for t in task.ancestors]), f"Timed task '{task.description}' in file '{task.file}' has a timed ancestor."

    def validate_deadlines(self):
        def recurse(task, subsequent=None):
            if task.deadline:
                if subsequent:
                    assert task.deadline<=subsequent.deadline, f"Achronological deadlines for subsequent tasks ('{task}' .. '{subsequent}')"
                subsequent = task
            for dep in task.dependencies:
                recurse(dep, subsequent=subsequent)
        for task in self.tasks:
            if task.deadline:
                recurse(task)

