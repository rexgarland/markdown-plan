import { countTasks } from "../count";

describe("counting tasks", () => {
  it("should count a header", () => {
    const plan = "# hello";
    const { total } = countTasks(plan);
    expect(total).toBe(1);
  });

  it("should count multi headers", () => {
    const plan = "### subheader";
    const { total } = countTasks(plan);
    expect(total).toBe(1);
  });

  it("should count a list item", () => {
    const plan = "- hello";
    const { total } = countTasks(plan);
    expect(total).toBe(1);
  });

  it("should only count leaves", () => {
    const plan = `- parent
  - child`;
    const { total } = countTasks(plan);
    expect(total).toBe(1);
  });

  it("should consider not count headers with children", () => {
    const plan = `# title
- task`;
    const { total } = countTasks(plan);
    expect(total).toBe(1);
  });

  it("should handle multiple sublevels", () => {
    const plan = `- parent1
  - child1
  - parent2
    - child2`;
    const { total } = countTasks(plan);
    expect(total).toBe(2);
  });

  it("should count done tasks", () => {
    const plan = "- [x] hello";
    const { completed } = countTasks(plan);
    expect(completed).toBe(1);
  });
});
