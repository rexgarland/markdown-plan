function isHeader(line) {
  return line.startsWith("# ");
}

function isListItem(line) {
  const stripped = line.trim();
  return stripped.startsWith("- ") || stripped.startsWith("* ");
}

function isTask(line) {
  return isHeader(line) || isListItem(line);
}

export function countTasks(plan) {
  const lines = plan.split("\n");
  const taskLines = lines.filter(isTask);

  const total = taskLines.length;
  const completed = 0;

  return { total, completed };
}
