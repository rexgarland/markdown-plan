from datetime import datetime, timedelta
import time
import random
from functools import cached_property

from .gantt import GanttEvent, GanttDuration
from . import parse

NOW = datetime.now()

def common_ancestor_depth(t1, t2):
    a1 = t1.ancestors
    a2 = t2.ancestors
    common = None
    for a in a1:
        if a in a2:
            common = a
            break
    if not common:
        return None
    d1 = a1.index(common)
    d2 = a2.index(common)
    return min(d1, d2)

class Schedule:
    def __init__(self, plan, order):
        self.plan = plan
        self.order = order
        self.ordered_tasks = order
        assert set(self.ordered_tasks)==set(self.plan.todo_tasks), "Schedule order must contain task indices for remaining tasks only"

    def task_order(plan, indices):
        return [plan.tasks[i] for i in indices]

    @property
    def is_chronological(self):
        previous = self.plan.completed_tasks + self.plan.waiting_tasks
        for task in self.ordered_tasks:
            for dep in task.dependencies:
                if not (dep in previous):
                    return False
            previous += [task]
        return True

    @property
    def end_times(self):
        _end_times = {}
        for task in self.plan.waiting_tasks:
            _end_times[task] = max(GanttEvent(datetime=NOW), task.start+task.total_duration)
        time = GanttEvent(datetime=NOW)
        for task in self.ordered_tasks:
            task_start = time
            for dep in task.dependencies:
                if dep.is_completed:
                    continue
                assert (dep in _end_times), f"Could not find task '{dep}' in previous order or completed tasks."
                if _end_times[dep]>task_start:
                    task_start = _end_times[dep]
            _end_times[task] = task_start + task.remaining_duration
            if not task.is_wait:
                time = _end_times[task]
        return _end_times

    @property
    def earliness(self):
        return {task: GanttDuration((task.deadline-self.end_times[task]).hours) for task in self.plan.upcoming_deadline_tasks}

    @cached_property
    def context_switching(self):
        jumps = 0
        slides = 0
        for i in range(1, len(self.ordered_tasks)):
            first = self.ordered_tasks[i-1]
            second = self.ordered_tasks[i]
            depth = common_ancestor_depth(first, second)
            if depth is None:
                jumps += 1
            else:
                slides += depth
        return (jumps, slides)

    @cached_property
    def fitness(self):
        if not self.is_chronological:
            return (-float('inf'),)
        # return min(self.earliness.items(), key=lambda i: i[1])[1].hours
        hours = tuple(sorted([g.hours for g in self.earliness.values()]))
        switches = [-a for a in self.context_switching]
        return tuple([*hours, *switches])

class GeneticAlg:
    def __init__(self, realtime_reports=False):
        '''
        Must implement:
            - initial (population)
            - fitness (function ind => float)
            - crossover (function ind1, ind2 => ind3)
            - mutate (function ind1 => subpopulation)
            - stop (function population => bool)
        '''
        self.stats = {
            'n': 0,
            'bests': [],
        }
        self.realtime_reports = realtime_reports
        self.last_report = time.time()
        self.solution = None

    def print_report(self):
        print(f"Best fitness so far: {self.stats['bests'][-1]}")

    def run(self):
        population = self.initial
        best_fitness = None
        best_individual = None

        while not self.stop(population):
            population.sort(key = self.fitness, reverse=True)
            max_fitness = self.fitness(population[0])
            winner = population[0]

            if best_fitness is None:
                best_fitness = max_fitness
            if max_fitness>=best_fitness:
                best_fitness = max_fitness
                best_individual = winner

            if best_individual==winner:
                winner = population[1]

            child = self.crossover(best_individual, winner)
            children = self.mutate(child)
            # population = children + population[:len(population)-len(children)]
            population[-len(children):] = children
            self.stats['n'] += 1
            self.stats['bests'] += [best_fitness]

            if self.realtime_reports:
                if time.time()-self.last_report>2:
                    self.print_report()
                    self.last_report = time.time()

        self.solution = best_individual

class Scheduler(GeneticAlg):
    def __init__(self, plan, population_size=200, generation_size=100, mutation_rate=0.05, **kwargs):
        self.population_size = population_size
        self.generation_size = generation_size
        self.mutation_rate = mutation_rate
        self.plan = plan
        self.bests = []
        super().__init__(**kwargs)

    @property
    def initial(self):
        # random permutations of remaining tasks
        return self.mutate(self.best_guess(), num=self.population_size)

    def fitness(self, schedule):
        # minimum earliness across deadlines
        return schedule.fitness

    def crossover(self, schedule1, schedule2):
        neworder = self.crossover_half(schedule1.order, schedule2.order)
        return self.to_schedule(neworder)

    def mutate(self, schedule, method='shift', num=None):
        if not num:
            num = self.generation_size

        if method=='all':
            methods = ['reinsert', 'adjacent', 'shift']
            pop = []
            for m in methods:
                pop += self.mutate(schedule, method=m, num=num//len(methods))
            return pop

        if method=='reinsert':
            subpopulation = [self.to_schedule(self.reinsert_mutation(schedule.order)) for _ in range(num)]
        elif method=='adjacent':
            subpopulation = [self.to_schedule(self.adjacent_mutation(schedule.order)) for _ in range(num)]
        elif method=='shift':
            subpopulation = [self.to_schedule(self.shift_mutation(schedule.order)) for _ in range(num)]
        else:
            raise ValueError(f'Unexpected mutation method: "{method}"')
        return subpopulation

    def stop(self, population):
        # stop when the best fitness is stable
        stable_len = 10
        if hasattr(self, 'stats') and 'bests' in self.stats:
            self.bests = self.stats['bests']
        else:
            self.bests += [max([self.fitness(schedule) for schedule in population])]
        if len(self.bests)>=stable_len:
            identical = [self.bests[i]==self.bests[i+1] for i in range(max(len(self.bests)-stable_len,0), len(self.bests)-1)]
            stable = all(identical)
            if stable:
                return True
        return False

    def to_schedule(self, order):
        return Schedule(self.plan, order)

    def best_guess(self):
        order = []
        remaining = set(self.plan.todo_tasks)
        added = set([t for t in self.plan.tasks if t.is_completed or (t in self.plan.waiting_tasks)])
        while remaining:
            available = [t for t in remaining if all([dep in added for dep in t.dependencies])]
            assert available, "No task order will satisfy dependency graph."
            available.sort(key = lambda task: min([t.deadline for t in self.plan.deadlines_for_task[task]]) if self.plan.deadlines_for_task[task] else GanttEvent(datetime.now()+timedelta(days=10000)))
            available.sort(key = lambda task: not task.is_wait)
            new = available[0]
            order += [new]
            remaining.remove(new)
            added.add(new)
        return Schedule(self.plan, order)

    def crossover_half(self, order1, order2):
        # keep a contiguous substring of len//2 (at a random offset) from order1
        # fill in the rest with order2
        order1, order2 = random.sample([order1, order2], 2)
        hl = len(order1)//2
        i = random.randint(0,len(order1)-hl)
        from1 = order1[i:i+hl]
        from2 = [a for a in order2 if a not in from1]
        new = from2[:i] + from1 + from2[i:]
        assert len(new)==len(order1)
        return new

    def crossover_random(self, order1, order2):
        indices = sorted(random.sample(range(len(order1)), len(order1)//2))
        chosen = [order1[i] for i in indices]
        remaining = [t for t in order2 if t not in chosen]
        result = []
        j = 0
        for i in range(len(order1)):
            if i in indices:
                result.append(order1[i])
            else:
                result.append(remaining[j])
                j += 1
        return result

    def adjacent_mutation(self, order):
        # switch two adjacent indices for every mutation
        remaining = order.copy()
        new = []
        while remaining:
            if len(remaining)>1 and random.random()<self.mutation_rate:
                new += [remaining[1]]
                remaining = [remaining[0]] + remaining[2:]
            else:
                new += [remaining[0]]
                remaining = remaining[1:]
        return new

    def reinsert_mutation(self, order):
        # pull an element from the array and place it somewhere else
        new = order.copy()
        to_reinsert = [task for task in order if random.random()<self.mutation_rate]
        for task in to_reinsert:
            new.remove(task)
            i = random.randint(0,len(new))
            new = new[:i] + [task] + new[i:]
        return new

    def shift_mutation(self, order):
        i1 = random.randint(0, len(order)-1)
        i2 = random.randint(0, len(order)-1)
        i = min(i1,i2)
        j = max(i1,i2)
        remaining = order[:i] + order[j+1:]
        slice = order[i:j+1]
        insert = random.randint(0, len(remaining))
        return remaining[:insert] + slice + remaining[insert:]

    @property
    def min_deadline(self):
        if not self.solution:
            return None
        return self.solution.calculate_earliness()[1]

    def summarize(self):
        if not s.solution:
            print("Could not find a schedule satisfying dependencies.")
            return

        if s.plan.upcoming_deadline_tasks:
            print('\nDeadline Summary\n')
            earliness = s.solution.earliness
            printuples = []
            for item in sorted(list(earliness.items()), key = lambda i: i[0].deadline):
                task = item[0]
                early_by = item[1]
                deadline_string = parse.get_deadline(task.string)
                if early_by.hours>=0:
                    printuples += [(f'✅ {task.description} [by {deadline_string}]:', f'{early_by} early')]
                else:
                    if task.deadline<GanttEvent(datetime=NOW):
                        printuples += [(f'❌ {task.description} [by {deadline_string}]:', f'missed')]
                    else:
                        printuples += [(f'⚠️  {task.description} [by {deadline_string}]:', f'{-early_by} late')]
            real_len = lambda a: len(a) - 2*a.count('⚠️')
            buffered_width = max([real_len(first) for (first, second) in printuples]) + 2
            spaces = {first: buffered_width-real_len(first) for (first, second) in printuples}
            for (first, second) in printuples:
                print(first+' '*spaces[first]+second)

        # print('\nSchedule\n')
        # for task in s.solution.ordered_tasks:
        #     print(f"{task.file.name}:\t{task.description}")

if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser('schedule tasks')
    parser.add_argument('files', type=str, nargs='+')
    args = parser.parse_args()
    from mdplan.plan import Plan
    plan = Plan(files=args.files)
    s = Scheduler(plan, realtime_reports=True)
    s.run()
    s.summarize()