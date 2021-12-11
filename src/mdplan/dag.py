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

