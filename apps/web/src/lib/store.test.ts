import { beforeEach, describe, expect, it, vi } from "vitest";

describe("store", () => {
  beforeEach(() => {
    vi.resetModules();
    const map = new Map<string, string>();
    const ls = {
      getItem: (k: string) => map.get(k) ?? null,
      setItem: (k: string, v: string) => {
        map.set(k, v);
      },
      removeItem: (k: string) => {
        map.delete(k);
      },
      clear: () => map.clear(),
    };
    vi.stubGlobal("window", { localStorage: ls });
    vi.stubGlobal("localStorage", ls);
  });

  it("emptyState defaults", async () => {
    const { emptyState } = await import("./store");
    const s = emptyState();
    expect(s.onboarded).toBe(false);
    expect(s.checkIns).toEqual([]);
    expect(s.plans).toEqual([]);
  });

  it("save and load roundtrip", async () => {
    const { emptyState, loadState, saveState } = await import("./store");
    const s = emptyState();
    s.onboarded = true;
    s.habitLabel = "scroll";
    s.values = ["focus"];
    saveState(s);
    const loaded = loadState();
    expect(loaded.onboarded).toBe(true);
    expect(loaded.habitLabel).toBe("scroll");
    expect(loaded.values).toEqual(["focus"]);
  });

  it("loadState recovers from corrupt JSON", async () => {
    const { loadState } = await import("./store");
    localStorage.setItem("relink.user.v1", "{not-json");
    expect(loadState().onboarded).toBe(false);
  });

  it("uid is unique-ish", async () => {
    const { uid } = await import("./store");
    expect(uid()).not.toBe(uid());
  });
});
