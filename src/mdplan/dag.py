"""
This module is for exporting the DAG to JSON.

The graph is exported in a neighbor list representation.

E.g.
[
	{
		"id": 1,
		"description": "a task",
		"dependencies": [2]
	},
	{
		"id": 2,
		"description": "do me first",
		"dependencies": []
	}
]
"""
import json

from . import utils
from .plan import Plan

def convert_to_dag(planfile, jsonfile=None):

	if jsonfile is None:
		jsonfile = utils.json_version_of(planfile)

	# parse the file
	plan = Plan(planfile)

	# assign an id to each task
	for i in range(len(plan.tasks)):
		plan.tasks[i].id = i

	# create a neighbor list
	json_tasks = []
	for task in plan.tasks:
		new = {
			'id': task.id,
			'description': task.description,
			
		}
		if task.total_duration.hours > 0:
			new['type'] = task.type
			new['duration']= task.total_duration.days
			new['remaining']= task.remaining_duration.days
		new['dependencies'] = [t.id for t in task.dependencies]
		json_tasks.append(new)

	# write out
	with open(jsonfile, 'w') as f:
		json.dump(json_tasks, f, indent='\t')

	return jsonfile