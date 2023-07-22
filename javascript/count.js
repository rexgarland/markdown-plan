function isHeader(line) {
  return line.match(/^#{1,6}\s/);
}

function isListItem(line) {
  return line.match(/^\s*(-|\*)\s/);
}

function isTask(line) {
  return isHeader(line) || isListItem(line);
}

function countPrecedingWhiteSpace(line) {
  let num = 0;
  for (const char of line) {
    if (char === " ") {
      num++;
    } else {
      break;
    }
  }
  return num;
}

function taskLevel(taskLine) {
  if (isHeader(taskLine)) {
    return -1;
  }
  return countPrecedingWhiteSpace(taskLine);
}

export function countTasks(plan) {
  const lines = plan.split("\n");

  const taskLines = lines.filter(isTask);
  const levels = taskLines.map(taskLevel);

  const leaveTaskLines = taskLines.filter((_, i) => {
    const isLastTask = i === taskLines.length - 1;

    if (isLastTask) {
      return true;
    }

    const thisLevel = levels[i];
    const nextLevel = levels[i + 1];
    const isParent = nextLevel > thisLevel;

    return !isParent;
  });

  const total = leaveTaskLines.length;
  const completed = 0;

  return { total, completed };
}
