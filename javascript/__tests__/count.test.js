import { countTasks } from "../count";

describe("counting tasks", () => {
  it("should count a header", () => {
    const plan = "# hello";
    const { total } = countTasks(plan);

    expect(total).toBe(1);
  });
});
