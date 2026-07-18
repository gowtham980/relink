"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { loadState, saveState, uid } from "@/lib/store";
import { invokeCoach } from "@/lib/coach-client";
import { repairCount } from "@/domain/metrics";

export default function SlipPage() {
  const router = useRouter();
  const [context, setContext] = useState("");
  const [next24h, setNext24h] = useState("");
  const [reply, setReply] = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!loadState().onboarded) router.replace("/onboarding");
  }, [router]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await invokeCoach("slip", {
        message: `Context: ${context}. Next 24h idea: ${next24h}`,
      });
      setReply(String(res.reply || ""));
      const state = loadState();
      state.slips = [
        {
          id: uid(),
          at: new Date().toISOString(),
          context,
          next24h,
        },
        ...state.slips,
      ];
      state.repairs = repairCount(state.slips);
      if (next24h.trim()) {
        state.plans = [
          {
            id: uid(),
            ifCue: "In the next 24 hours after a slip",
            thenAction: next24h.trim(),
            active: true,
          },
          ...state.plans,
        ];
      }
      saveState(state);
      setDone(true);
    } catch (err) {
      setReply(err instanceof Error ? err.message : "Error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-lg space-y-4">
      <h1 className="font-display text-3xl font-semibold">Slip recovery</h1>
      <p className="text-dusk">
        A lapse is not a relapse. We repair the plan — we don&apos;t erase your identity.
      </p>
      <form onSubmit={submit} className="card space-y-3 p-5">
        <div>
          <label className="label" htmlFor="ctx">
            What happened right before?
          </label>
          <textarea
            id="ctx"
            className="input min-h-[80px]"
            value={context}
            onChange={(e) => setContext(e.target.value)}
            required
            maxLength={1000}
          />
        </div>
        <div>
          <label className="label" htmlFor="n24">
            One concrete next-24h action
          </label>
          <input
            id="n24"
            className="input"
            value={next24h}
            onChange={(e) => setNext24h(e.target.value)}
            placeholder="e.g. evening walk + phone in kitchen after 9pm"
            required
            maxLength={300}
          />
        </div>
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? "Recovering…" : "Process slip"}
        </button>
      </form>
      {reply && (
        <div className="card space-y-2 p-5" role="status">
          <p className="text-sm">{reply}</p>
          {done && (
            <a href="/plans" className="text-sm font-semibold text-pine underline">
              View updated plans →
            </a>
          )}
        </div>
      )}
    </div>
  );
}
