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
});
