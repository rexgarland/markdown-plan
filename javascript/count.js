function isTask(line) {
  return line.startsWith("# ") || line.startsWith("- ");
}

export function countTasks(plan) {
  const lines = plan.split("\n");
  const taskLines = lines.filter(isTask);

  const total = taskLines.length;
  const completed = 0;

  return { total, completed };
}
