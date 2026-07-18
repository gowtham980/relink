"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import type { UserState } from "@/domain/types";
import { averageUrge, daysPracticed, slipRate } from "@/domain/metrics";
import { emptyState, loadState, saveState } from "@/lib/store";
import { invokeCoach } from "@/lib/coach-client";

export default function InsightsPage() {
  const router = useRouter();
  const [state, setState] = useState<UserState>(emptyState());
  const [loading, setLoading] = useState(false);
  const [nudge, setNudge] = useState("");

  useEffect(() => {
    const s = loadState();
    if (!s.onboarded) router.replace("/onboarding");
    else setState(s);
  }, [router]);

  async function generate() {
    setLoading(true);
    try {
      const res = await invokeCoach("insight", {
        checkIns: state.checkIns,
        slips: state.slips,
      });
      const insight = {
        summary: String(res.summary || ""),
        patterns: (res.patterns as string[]) || [],
        suggestedPlanEdits: (res.suggestedPlanEdits as string[]) || [],
        at: new Date().toISOString(),
      };
      const next = { ...state, insight };
      saveState(next);
      setState(next);
      const n = await invokeCoach("nudge", { values: state.values });
      setNudge(String(n.nudge || ""));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl font-semibold">Insights</h1>
          <p className="text-dusk">Patterns from your logs — not judgment.</p>
        </div>
        <button type="button" className="btn-primary" disabled={loading} onClick={generate}>
          {loading ? "Analyzing…" : "Generate AI insight"}
        </button>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <div className="card p-4">
          <p className="text-xs text-dusk">Practice days</p>
          <p className="text-2xl font-semibold">{daysPracticed(state.checkIns)}</p>
        </div>
        <div className="card p-4">
          <p className="text-xs text-dusk">Avg urge</p>
          <p className="text-2xl font-semibold">{averageUrge(state.checkIns) || "—"}</p>
        </div>
        <div className="card p-4">
          <p className="text-xs text-dusk">Slip rate</p>
          <p className="text-2xl font-semibold">{slipRate(state.checkIns)}%</p>
        </div>
      </div>

      {nudge && (
        <div className="card border-pine/20 bg-emerald-50/50 p-4 text-sm">
          <strong>Nudge:</strong> {nudge}
        </div>
      )}

      {state.insight ? (
        <div className="card space-y-3 p-5">
          <p className="font-display text-xl font-semibold">{state.insight.summary}</p>
          {state.insight.patterns.length > 0 && (
            <ul className="list-disc pl-5 text-sm text-dusk">
              {state.insight.patterns.map((p) => (
                <li key={p}>{p}</li>
              ))}
            </ul>
          )}
          {state.insight.suggestedPlanEdits.length > 0 && (
            <div>
              <p className="text-sm font-semibold">Suggested plan edits</p>
              <ul className="mt-1 list-disc pl-5 text-sm text-dusk">
                {state.insight.suggestedPlanEdits.map((p) => (
                  <li key={p}>{p}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ) : (
        <div className="card p-6 text-dusk">
          {state.checkIns.length < 2
            ? "Log a couple of check-ins, then generate an insight."
            : "Ready when you are — generate your first insight card."}
        </div>
      )}

      <section aria-label="Recent check-ins">
        <h2 className="mb-2 font-semibold">Recent check-ins</h2>
        {state.checkIns.length === 0 ? (
          <p className="text-sm text-dusk">None yet.</p>
        ) : (
          <ul className="space-y-2">
            {state.checkIns.slice(0, 7).map((c) => (
              <li key={c.id} className="card flex flex-wrap justify-between gap-2 px-3 py-2 text-sm">
                <span>{new Date(c.date).toLocaleString()}</span>
                <span>
                  mood {c.mood} · urge {c.urgeLevel}
                  {c.slipped ? " · slipped" : ""}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
