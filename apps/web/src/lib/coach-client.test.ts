import { afterEach, describe, expect, it, vi } from "vitest";
import { invokeCoach } from "./coach-client";

describe("invokeCoach", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("posts action and returns json", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({
        ok: true,
        json: async () => ({ reply: "hi", disclaimer: "x" }),
      }))
    );
    const data = await invokeCoach("urge", { message: "test" });
    expect(data.reply).toBe("hi");
    expect(fetch).toHaveBeenCalledWith(
      "/api/coach",
      expect.objectContaining({ method: "POST" })
    );
  });

  it("throws on http error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({
        ok: false,
        status: 500,
        text: async () => "boom",
      }))
    );
    await expect(invokeCoach("coach", { message: "x" })).rejects.toThrow(/boom|500/);
  });
});
