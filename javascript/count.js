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

function parseHeaderLevel(headerLine) {
  const match = headerLine.match(/^(#{1,6})\s/);
  const hashes = match[1];
  return hashes.length;
}

function taskLevel(taskLine) {
  if (isHeader(taskLine)) {
    const headerLevel = parseHeaderLevel(taskLine);
    // h6 corresponds to -1
    return headerLevel - 7;
  }
  return countPrecedingWhiteSpace(taskLine);
}

function parseDescription(taskLine) {
  let match;
  if (isHeader(taskLine)) {
    match = taskLine.match(/^#{1,6}\s(.*)/);
    return match[1];
  }
  match = taskLine.match(/^\s*(-|\*)\s(.*)/);
  return match[2];
}

function isCompleted(taskLine) {
  const description = parseDescription(taskLine);
  return description.match(/^\s*\[x\]\s/);
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
  const completed = leaveTaskLines.filter(isCompleted).length;

  return { total, completed };
}
