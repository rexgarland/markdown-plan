# markdown-plan
`markdown-plan` is a project planning syntax based on markdown. This extended syntax includes time estimates and time measurements, helping you improve your planning accuracy. It was designed for software freelancers who want to organize technical work, but I imagine it could be useful elsewhere.

## Installation

```
pip install mdplan
```

## Getting started

Trye the following example to make sure everything works. 

Copy the following markdown into a text file named `website.plan.md`.

```
# Bring up website [by 12-10]
- purchase domain {30 mins} [20 mins]
- prepare server
    1. rent server {1 hr}
    2. setup server {2-3 hours} [12-1:30pm, 2-3pm]
    3. push and run code {20 mins}
- connect domain to server @(domain, prepare server) {1 hr}
    - update dns records
    - secure website with https
```

Then run `mdplan webside.plan.md` from within the same directory to view the plan as a gantt chart.

![example gantt chart in the terminal](images/example.png)

## Tutorial

In `markdown-plan`, each "plan" is a text file, and each "task" is a markdown list item.

The format for a task is fairly simple. For example:

```
* setup server {2-3 hrs}
```

This means "I estimate the task `setup server` will take 2-3 hours." Once you start working on the task, you can add time measurements in brackets:

```
* setup server {2-3 hrs} [12-1:30pm, 2-3pm]
```

`markdown-plan` recognizes time intervals as well as durations (e.g. `[2.5 hrs]`). You can also add a deadline in (partial) ISO format...

```
* setup server {2-3 hrs} [2.5 hrs] [by 12-10]
```

... as well as dependencies on other tasks ...

```
* choose server provider
...
* setup server {2-3 hrs} [2.5 hrs] [by 12-10] @(server provider)
```

For dependencies, you can write any unique substring of the referenced task.

Some useful tools:
* viewing a gantt chart in the terminal
coming soon:
* automatically scheduling tasks when order is ambiguous
* checking feasibility of deadlines
* `--csv`: exporting everything as a csv

## Basic syntax
A valid "markdown plan" must have two things:
1. a title line (starting with a single `#`)
2. a list of tasks

```
# example plan
* task 1
* task 2
```

Internally, everything is a task. The title is a task whose subtasks are everything after it. Nested lists are tasks whose dependencies are its children, etc.

Any line formatted as a list item is parsed as a task according to the following syntax.
```
* <description> {<estimate>} [<measurements>] [by <deadline>] [done|cancelled] @(<dependencies>)
```
The only required elements are an initial list marker and a description. Everything else can be added or ignored depending on your needs.

Examples:
```
* research title transfer {4 hours}

- start online app {1-2 hrs} [12-1:30pm, 2-3pm] [done]

1. complete paperwork [30 min] [done]

2. mail paperwork {wait 1-2 weeks} [started 12-10] [by 1-1]
```

Ordered lists will cue markdown-plan to automatically add dependencies between tasks. Lists can be nested ...
```
- new title
    1. finish paperwork
    2. mail paperwork
```
... and you can mix ordered and unordered lists together.
```
1. first this
2. then this
- this can happen any time
```

## Tools

Run `mdplan help` to see a list of tools and `mdplan <tool> help` to see a description and options.

### Viewing
You can view plan(s) as a gantt chart in the terminal.
```
$ mdplan <file(s) or glob>
```

```
$ mdplan example.plan.md

Deadline Summary

⚠️ sell car [by 12-10]:             3.94 work days late
✅ create web portfolio [by 1-5]:   2.05 weeks early

View schedule? (y/n) 
```

#### Under the hood

When a plan includes "wait" tasks, optimal scheduling quickly becomes untractable. The scheduler uses a stochastic optimizer to find a valid task permutation with an approximately optimal score (i.e. maximizing the minimum earliness across deadlines).

### Reporting

The `correlation` tool shows estimated versus measured task times.
```
$ mdplan correlation example.plan.md
```
[img]

A csv table can be generated for further analysis...
```
$ mdplan csv example.plan.md
```
[img]

## Syntax Details

In markdown-plan, there are two types of tasks:
* work tasks and
* wait tasks

### Work tasks

Work tasks are tasks that require your time to complete. They allow for the following syntax.

An `{estimate}` can be the following:
* duration (e.g. `{4 hours}`)
* duration range (e.g. `{3-4 days}`)

A `[measurement]` can be the following:
* duration (e.g. `[1 hr]`)
* time interval (e.g. `[11-12pm]`)
* start or finish time (see wait tasks below)

Multiple measurements can be separated by commas within brackets (e.g. `[12-1, 3-4pm]`) or as separate brackets (e.g. `[12-1] [3-4pm]`)

A deadline is denoted with the word `by` in brackets and can be the following:
* date (e.g. `[by 12-10]`)
* time (for items that should finish today) (e.g. `[by 1:30pm]` or `[by 13:30]`)
* datetime (for greater precision) (e.g. `[by 12-10 at 1:30pm]`)

A `[status]` can be
* "done" for task completion
* "cancelled" for ignoring a tasks

### Waiting tasks

Waiting tasks are tasks for which you only wait (i.e. you do not have to do any work). All of the above syntax is valid for waiting tasks, with some additions. 

The task's estimate can be prefixed with the word `wait` to signify a waiting task (e.g. work that can happen concurrently with your own work):
```{wait 3-4 days}```

A waiting task requires no work from you, but other tasks depending on it must wait until it is finished (e.g. waiting for something to arrive in the mail). The following measurements are used for waiting tasks:
* a start time (e.g. `[started 12-10]`)
* a finish time (e.g. `[finished 12-15]`)

You can also write a time duration like normal if you prefer.

### Task dependencies

A plan file is parsed as a tree of tasks, where the title line is the "root" task. Each task is assigned "dependencies" based on list nesting (parent/children relationships) and list ordering. Manual dependencies can be added by referencing a unique substring of another task:

`- start online app @(research)`

In this case, the task "start online app" will require the task "research" to be completed before it starts. Tasks from another file can be referenced using a file prefix and a colon. For example:

`- start online app @(other: research)`

In this case, the file `./other.plan.md` is searched for a task containing the substring "research". Any relative path can be used in place of `other`, keeping or omitting the `.plan.md` suffix.

### Other rules

These are some caveats when running the scheduler. The following rules should be considered.

1. No timed task can have a parent or child who is also timed. A "timed task" is any task with an estimate or a measurement.
2. Never list an ancestor task as a dependency of a given task. Parent tasks must finish after their children are finished, not the other way around.

## More examples

`cd` into the `example` directory and try running `mdplan gantt` on any of the examples. 

## Acknowledgements

This project was inspired by Thomas Figg's ["Programming is Terrible"](https://www.youtube.com/watch?v=csyL9EC0S0c) talk and Andrew Steel's [gantt](https://github.com/andrew-ls/gantt) repo.