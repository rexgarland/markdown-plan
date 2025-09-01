How this folder works:
1. You create a <name>_repo folder to create a new test repo (automatically ignored, see .gitignore)
2. Init git repo within that folder, then commit as you would normally.
3. Run `utils/package.sh <name>_repo` to create a git-trackable package of the repo to be used in testing.