Some useful tools:
* viewing a gantt chart in the terminal
coming soon:
* automatically scheduling tasks when order is ambiguous
* checking feasibility of deadlines
* `--csv`: exporting everything as a csv


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

### Other rules

These are some caveats when running the scheduler. The following rules should be considered.

1. No timed task can have a parent or child who is also timed. A "timed task" is any task with an estimate or a measurement.
2. Never list an ancestor task as a dependency of a given task. Parent tasks must finish after their children are finished, not the other way around.