import { describe, expect, it } from "vitest";
import { averageUrge, daysPracticed, repairCount, slipRate } from "./metrics";

describe("metrics", () => {
  it("counts unique practice days", () => {
    expect(
      daysPracticed([
        { id: "1", date: "2026-07-01", mood: 3, urgeLevel: 5, slipped: false, note: "" },
        { id: "2", date: "2026-07-01", mood: 2, urgeLevel: 4, slipped: false, note: "" },
        { id: "3", date: "2026-07-02", mood: 4, urgeLevel: 2, slipped: true, note: "" },
      ])
    ).toBe(2);
  });

  it("averages urge", () => {
    expect(
      averageUrge([
        { id: "1", date: "a", mood: 1, urgeLevel: 4, slipped: false, note: "" },
        { id: "2", date: "b", mood: 1, urgeLevel: 6, slipped: false, note: "" },
      ])
    ).toBe(5);
  });

  it("empty average is 0", () => {
    expect(averageUrge([])).toBe(0);
  });

  it("slip rate and repairs", () => {
    expect(
      slipRate([
        { id: "1", date: "a", mood: 1, urgeLevel: 1, slipped: true, note: "" },
        { id: "2", date: "b", mood: 1, urgeLevel: 1, slipped: false, note: "" },
      ])
    ).toBe(50);
    expect(repairCount([{ id: "1", at: "x", context: "", next24h: "" }])).toBe(1);
  });

  it("slip rate empty is 0", () => {
    expect(slipRate([])).toBe(0);
  });
});
