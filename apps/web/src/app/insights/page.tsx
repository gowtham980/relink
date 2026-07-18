"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import type { UserState } from "@/domain/types";
import { averageUrge, daysPracticed, parsePlanEdit, slipRate } from "@/domain/metrics";
import { emptyState, loadState, saveState, uid } from "@/lib/store";
import { invokeCoach } from "@/lib/coach-client";

export default function InsightsPage() {
  const router = useRouter();
  const [state, setState] = useState<UserState>(emptyState());
  const [loading, setLoading] = useState(false);
  const [nudge, setNudge] = useState("");
  const [applied, setApplied] = useState<string | null>(null);

  useEffect(() => {
    const s = loadState();
    if (!s.onboarded) router.replace("/onboarding");
    else setState(s);
  }, [router]);

  async function generate() {
    setLoading(true);
    setApplied(null);
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

  function applyEdit(text: string) {
    const { ifCue, thenAction } = parsePlanEdit(text);
    const next = {
      ...state,
      plans: [
        { id: uid(), ifCue, thenAction, active: true, origin: "ai" as const },
        ...state.plans,
      ],
    };
    saveState(next);
    setState(next);
    setApplied(text);
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
              <ul className="mt-2 space-y-2">
                {state.insight.suggestedPlanEdits.map((p) => (
                  <li
                    key={p}
                    className="flex flex-wrap items-start justify-between gap-2 rounded-xl bg-sand/80 px-3 py-2 text-sm"
                  >
                    <span className="text-dusk">{p}</span>
                    <button
                      type="button"
                      className="btn-primary shrink-0 px-3 py-1 text-xs"
                      onClick={() => applyEdit(p)}
                    >
                      Apply to Plans
                    </button>
                  </li>
                ))}
              </ul>
              {applied && (
                <p className="mt-2 text-sm text-pine" role="status">
                  Added to Plans.{" "}
                  <Link href="/plans" className="underline">
                    View plans →
                  </Link>
                </p>
              )}
            </div>
          )}
        </div>
      ) : (
        <div className="card mx-auto max-w-md space-y-3 p-8 text-center">
          <div
            className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-pine/10 text-2xl"
            aria-hidden
          >
            {state.checkIns.length < 2 ? "📝" : "✨"}
          </div>
          <h2 className="font-display text-xl font-semibold">
            {state.checkIns.length < 2 ? "Log a couple of check-ins first" : "Ready for your first insight"}
          </h2>
          <p className="text-sm text-dusk">
            {state.checkIns.length < 2
              ? "Patterns need a few honest logs. Check in today, then come back."
              : "We’ll look at your check-ins and slips — no judgment, just patterns."}
          </p>
          {state.checkIns.length < 2 ? (
            <Link href="/check-in" className="btn-primary inline-flex">
              Go to check-in
            </Link>
          ) : (
            <button type="button" className="btn-primary" disabled={loading} onClick={generate}>
              {loading ? "Analyzing…" : "Generate insight"}
            </button>
          )}
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
