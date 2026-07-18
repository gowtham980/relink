"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import type { UserState } from "@/domain/types";
import { emptyState, loadState, saveState } from "@/lib/store";
import { invokeCoach } from "@/lib/coach-client";

export default function CoachPage() {
  const router = useRouter();
  const [state, setState] = useState<UserState>(emptyState());
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [safety, setSafety] = useState<string | null>(null);

  useEffect(() => {
    const s = loadState();
    if (!s.onboarded) router.replace("/onboarding");
    else setState(s);
  }, [router]);

  async function send(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || loading) return;
    const message = input.trim();
    setInput("");
    const history = [...state.coachHistory, { role: "user" as const, content: message }];
    setState((s) => ({ ...s, coachHistory: history }));
    setLoading(true);
    setSafety(null);
    try {
      const res = await invokeCoach("coach", {
        message,
        mode: "mi",
        history: state.coachHistory,
        profile: {
          habit: state.habitLabel,
          values: state.values,
          identity: state.identity,
          triggers: state.triggers,
          riskWindows: state.riskWindows,
          stageOfChange: state.stageOfChange,
        },
        recentCheckIns: state.checkIns.slice(0, 5).map((c) => ({
          date: c.date,
          mood: c.mood,
          urgeLevel: c.urgeLevel,
          slipped: c.slipped,
          note: c.note,
        })),
        activePlans: state.plans
          .filter((p) => p.active)
          .slice(0, 4)
          .map((p) => ({ ifCue: p.ifCue, thenAction: p.thenAction })),
        lastSlip: state.slips[0]
          ? { at: state.slips[0].at, context: state.slips[0].context, next24h: state.slips[0].next24h }
          : null,
      });
      if (res.blocked) {
        setSafety(String(res.reply));
        const next = { ...state, coachHistory: history };
        saveState(next);
        setState(next);
      } else {
        const nextHist = [
          ...history,
          { role: "assistant" as const, content: String(res.reply) },
        ];
        const next = { ...state, coachHistory: nextHist };
        saveState(next);
        setState(next);
      }
    } catch (err) {
      const nextHist = [
        ...history,
        {
          role: "assistant" as const,
          content: err instanceof Error ? err.message : "Error",
        },
      ];
      const next = { ...state, coachHistory: nextHist };
      saveState(next);
      setState(next);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <div>
        <h1 className="font-display text-3xl font-semibold">Adaptive coach</h1>
        <p className="text-sm text-dusk">
          Mode: <span className="rounded-full bg-pine/10 px-2 py-0.5 font-medium text-pine">MI</span>{" "}
          — uses your check-ins, plans, and repairs — not lectures.
        </p>
      </div>

      {safety && (
        <div className="card border-coral/30 p-4 text-sm" role="alert">
          <p className="font-semibold text-coral">Safety pause</p>
          <p>{safety}</p>
          <a href="/ethics" className="underline">
            Crisis resources
          </a>
        </div>
      )}

      <div className="card min-h-[280px] space-y-3 p-4" aria-live="polite">
        {state.coachHistory.length === 0 && (
          <p className="text-sm text-dusk">
            Ask about motivation, barriers, or what success looks like this week. The coach can see
            your recent logs and active if-then plans.
          </p>
        )}
        {state.coachHistory.map((m, i) => (
          <div
            key={i}
            className={`rounded-xl px-3 py-2 text-sm ${
              m.role === "user" ? "ml-8 bg-pine/10" : "mr-8 bg-sand"
            }`}
          >
            <span className="sr-only">{m.role}: </span>
            {m.content}
          </div>
        ))}
        {loading && <p className="text-sm text-dusk">Thinking…</p>}
      </div>

      <form onSubmit={send} className="flex gap-2">
        <label className="sr-only" htmlFor="coach-in">
          Message to coach
        </label>
        <input
          id="coach-in"
          className="input flex-1"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="What's on your mind?"
          maxLength={2000}
        />
        <button type="submit" className="btn-primary" disabled={loading}>
          Send
        </button>
      </form>
    </div>
  );
}
