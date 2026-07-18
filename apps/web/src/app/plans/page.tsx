"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import type { Plan, UserState } from "@/domain/types";
import { emptyState, loadState, saveState, uid } from "@/lib/store";
import { invokeCoach } from "@/lib/coach-client";

export default function PlansPage() {
  const router = useRouter();
  const [state, setState] = useState<UserState>(emptyState());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const s = loadState();
    if (!s.onboarded) router.replace("/onboarding");
    else setState(s);
  }, [router]);

  function persist(next: UserState) {
    saveState(next);
    setState(next);
  }

  function updatePlan(id: string, patch: Partial<Plan>) {
    const next = {
      ...state,
      plans: state.plans.map((p) => (p.id === id ? { ...p, ...patch } : p)),
    };
    persist(next);
  }

  async function regenerate() {
    setLoading(true);
    setError("");
    try {
      const res = await invokeCoach("plans", {
        context: {
          habit: state.habitLabel,
          triggers: state.triggers,
          values: state.values,
        },
      });
      const plans = ((res.plans as { ifCue: string; thenAction: string }[]) || []).map(
        (p) => ({
          id: uid(),
          ifCue: p.ifCue,
          thenAction: p.thenAction,
          active: true,
        })
      );
      persist({ ...state, plans: [...plans, ...state.plans] });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl font-semibold">If-then plans</h1>
          <p className="text-dusk">Implementation intentions — decide before the urge hits.</p>
        </div>
        <button type="button" className="btn-primary" disabled={loading} onClick={regenerate}>
          {loading ? "Generating…" : "AI Plan Lab"}
        </button>
      </div>
      {error && (
        <p className="text-sm text-coral" role="alert">
          {error}
        </p>
      )}
      {state.plans.length === 0 ? (
        <div className="card p-6 text-dusk">
          No plans yet. Run Plan Lab or finish onboarding.
        </div>
      ) : (
        <ul className="space-y-3">
          {state.plans.map((p) => (
            <li key={p.id} className="card space-y-2 p-4">
              <label className="label" htmlFor={`if-${p.id}`}>
                If…
              </label>
              <input
                id={`if-${p.id}`}
                className="input"
                value={p.ifCue}
                onChange={(e) => updatePlan(p.id, { ifCue: e.target.value })}
              />
              <label className="label" htmlFor={`then-${p.id}`}>
                Then I will…
              </label>
              <input
                id={`then-${p.id}`}
                className="input"
                value={p.thenAction}
                onChange={(e) => updatePlan(p.id, { thenAction: e.target.value })}
              />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
