"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import type { Plan, PlanOrigin, UserState } from "@/domain/types";
import { emptyState, loadState, saveState, uid } from "@/lib/store";
import { invokeCoach } from "@/lib/coach-client";

const ORIGIN_LABEL: Record<PlanOrigin, string> = {
  ai: "AI",
  user: "Yours",
  slip: "Repair",
};

export default function PlansPage() {
  const router = useRouter();
  const [state, setState] = useState<UserState>(emptyState());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draft, setDraft] = useState<{ ifCue: string; thenAction: string }>({
    ifCue: "",
    thenAction: "",
  });
  const [showArchived, setShowArchived] = useState(false);
  const [toast, setToast] = useState("");

  useEffect(() => {
    const s = loadState();
    if (!s.onboarded) router.replace("/onboarding");
    else setState(s);
  }, [router]);

  const activePlans = useMemo(() => state.plans.filter((p) => p.active), [state.plans]);
  const archivedPlans = useMemo(() => state.plans.filter((p) => !p.active), [state.plans]);
  const visible = showArchived ? archivedPlans : activePlans;

  function persist(next: UserState, msg?: string) {
    saveState(next);
    setState(next);
    if (msg) {
      setToast(msg);
      window.setTimeout(() => setToast(""), 2500);
    }
  }

  function startEdit(p: Plan) {
    setEditingId(p.id);
    setDraft({ ifCue: p.ifCue, thenAction: p.thenAction });
  }

  function cancelEdit() {
    setEditingId(null);
    setDraft({ ifCue: "", thenAction: "" });
  }

  function saveEdit(id: string) {
    if (!draft.ifCue.trim() || !draft.thenAction.trim()) return;
    const next = {
      ...state,
      plans: state.plans.map((p) =>
        p.id === id
          ? {
              ...p,
              ifCue: draft.ifCue.trim(),
              thenAction: draft.thenAction.trim(),
              origin: p.origin === "ai" ? ("user" as const) : p.origin,
            }
          : p
      ),
    };
    persist(next, "Plan updated");
    cancelEdit();
  }

  function toggleActive(id: string) {
    const next = {
      ...state,
      plans: state.plans.map((p) => (p.id === id ? { ...p, active: !p.active } : p)),
    };
    const p = state.plans.find((x) => x.id === id);
    persist(next, p?.active ? "Plan archived" : "Plan activated");
  }

  function removePlan(id: string) {
    if (!confirm("Delete this plan?")) return;
    persist(
      { ...state, plans: state.plans.filter((p) => p.id !== id) },
      "Plan deleted"
    );
    if (editingId === id) cancelEdit();
  }

  function addManual() {
    const id = uid();
    const plan: Plan = {
      id,
      ifCue: "",
      thenAction: "",
      active: true,
      origin: "user",
    };
    persist({ ...state, plans: [plan, ...state.plans] });
    setEditingId(id);
    setDraft({ ifCue: "", thenAction: "" });
    setShowArchived(false);
  }

  async function runPlanLab(mode: "add" | "replace") {
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
        (p) =>
          ({
            id: uid(),
            ifCue: p.ifCue,
            thenAction: p.thenAction,
            active: true,
            origin: "ai" as const,
          }) satisfies Plan
      );
      if (!plans.length) {
        setError("Plan Lab returned no plans — try again.");
        return;
      }
      const nextPlans = mode === "replace" ? plans : [...plans, ...state.plans];
      persist({ ...state, plans: nextPlans }, mode === "replace" ? "Plans replaced" : "Plans added");
      setShowArchived(false);
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
          <p className="text-dusk">
            Implementation intentions — decide before the urge hits.
            {state.plans.length > 0 && (
              <span className="mt-0.5 block text-sm">
                <strong className="text-ink">{activePlans.length}</strong> active
                {archivedPlans.length > 0 && (
                  <>
                    {" · "}
                    <strong className="text-ink">{archivedPlans.length}</strong> archived
                  </>
                )}
              </span>
            )}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button type="button" className="btn-ghost" onClick={addManual}>
            + New plan
          </button>
          <button
            type="button"
            className="btn-primary"
            disabled={loading}
            onClick={() => runPlanLab("add")}
          >
            {loading ? "Generating…" : "AI Plan Lab"}
          </button>
        </div>
      </div>

      {state.plans.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <button
            type="button"
            className={`rounded-full px-3 py-1 font-medium ${
              !showArchived ? "bg-pine text-white" : "bg-white text-dusk ring-1 ring-black/10"
            }`}
            onClick={() => setShowArchived(false)}
          >
            Active ({activePlans.length})
          </button>
          <button
            type="button"
            className={`rounded-full px-3 py-1 font-medium ${
              showArchived ? "bg-pine text-white" : "bg-white text-dusk ring-1 ring-black/10"
            }`}
            onClick={() => setShowArchived(true)}
          >
            Archived ({archivedPlans.length})
          </button>
          {!showArchived && activePlans.length > 0 && (
            <button
              type="button"
              className="ml-auto text-xs text-dusk underline disabled:opacity-50"
              disabled={loading}
              onClick={() => {
                if (confirm("Replace all plans with a fresh AI set?")) runPlanLab("replace");
              }}
            >
              Replace all with AI
            </button>
          )}
        </div>
      )}

      {error && (
        <p className="text-sm text-coral" role="alert">
          {error}
        </p>
      )}
      {toast && (
        <p className="text-sm text-pine" role="status">
          {toast}
        </p>
      )}

      {visible.length === 0 ? (
        <div className="card mx-auto max-w-md space-y-4 p-8 text-center">
          <div
            className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-pine/10 text-2xl"
            aria-hidden
          >
            {showArchived ? "📦" : "⚡"}
          </div>
          <div>
            <h2 className="font-display text-xl font-semibold">
              {showArchived ? "No archived plans" : "No if-then plans yet"}
            </h2>
            <p className="mt-1 text-sm text-dusk">
              {showArchived
                ? "Archive a plan when it no longer fits — you can reactivate anytime."
                : "Decide before the urge hits. Relink co-writes concrete if-then plans from your triggers and values."}
            </p>
          </div>
          {!showArchived && (
            <div className="flex flex-wrap justify-center gap-2">
              <button
                type="button"
                className="btn-primary"
                disabled={loading}
                onClick={() => runPlanLab("add")}
              >
                {loading ? "Generating…" : "Run AI Plan Lab"}
              </button>
              <button type="button" className="btn-ghost" onClick={addManual}>
                Write my own
              </button>
              {!state.onboarded && (
                <Link href="/onboarding" className="btn-ghost">
                  Start onboarding
                </Link>
              )}
            </div>
          )}
        </div>
      ) : (
        <ul className="space-y-3">
          {visible.map((p) => {
            const editing = editingId === p.id;
            const origin = p.origin;
            return (
              <li
                key={p.id}
                className={`card space-y-3 p-4 ${!p.active ? "opacity-70" : ""}`}
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex flex-wrap items-center gap-2">
                    {origin && (
                      <span
                        className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${
                          origin === "ai"
                            ? "bg-pine/10 text-pine"
                            : origin === "slip"
                              ? "bg-coral/10 text-coral"
                              : "bg-sand text-dusk"
                        }`}
                      >
                        {ORIGIN_LABEL[origin]}
                      </span>
                    )}
                    <span
                      className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${
                        p.active ? "bg-emerald-50 text-pine" : "bg-sand text-dusk"
                      }`}
                    >
                      {p.active ? "Active" : "Archived"}
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {!editing && (
                      <button
                        type="button"
                        className="rounded-lg px-2 py-1 text-xs font-semibold text-dusk hover:bg-black/5"
                        onClick={() => startEdit(p)}
                      >
                        Edit
                      </button>
                    )}
                    <button
                      type="button"
                      className="rounded-lg px-2 py-1 text-xs font-semibold text-dusk hover:bg-black/5"
                      onClick={() => toggleActive(p.id)}
                    >
                      {p.active ? "Archive" : "Activate"}
                    </button>
                    <button
                      type="button"
                      className="rounded-lg px-2 py-1 text-xs font-semibold text-coral hover:bg-coral/10"
                      onClick={() => removePlan(p.id)}
                    >
                      Delete
                    </button>
                  </div>
                </div>

                {editing ? (
                  <div className="space-y-2">
                    <div>
                      <label className="label" htmlFor={`if-${p.id}`}>
                        If…
                      </label>
                      <input
                        id={`if-${p.id}`}
                        className="input"
                        value={draft.ifCue}
                        onChange={(e) => setDraft((d) => ({ ...d, ifCue: e.target.value }))}
                        placeholder="e.g. I unlock my phone in bed after 10pm"
                        maxLength={200}
                      />
                    </div>
                    <div>
                      <label className="label" htmlFor={`then-${p.id}`}>
                        Then I will…
                      </label>
                      <input
                        id={`then-${p.id}`}
                        className="input"
                        value={draft.thenAction}
                        onChange={(e) => setDraft((d) => ({ ...d, thenAction: e.target.value }))}
                        placeholder="e.g. plug it across the room and open Urge SOS"
                        maxLength={200}
                      />
                    </div>
                    <div className="flex gap-2">
                      <button
                        type="button"
                        className="btn-primary"
                        disabled={!draft.ifCue.trim() || !draft.thenAction.trim()}
                        onClick={() => saveEdit(p.id)}
                      >
                        Save
                      </button>
                      <button type="button" className="btn-ghost" onClick={cancelEdit}>
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-2 text-sm">
                    <div className="flex flex-wrap items-start gap-2">
                      <span className="shrink-0 rounded-lg bg-sand px-2 py-1 text-xs font-bold uppercase tracking-wide text-dusk">
                        If
                      </span>
                      <p className="min-w-0 flex-1 pt-0.5 text-ink">{p.ifCue || "—"}</p>
                    </div>
                    <div className="flex items-center gap-2 pl-1 text-pine" aria-hidden>
                      <span className="text-lg leading-none">↓</span>
                      <span className="text-xs font-semibold uppercase tracking-wide">Then</span>
                    </div>
                    <div className="flex flex-wrap items-start gap-2">
                      <span className="shrink-0 rounded-lg bg-pine/10 px-2 py-1 text-xs font-bold uppercase tracking-wide text-pine">
                        I will
                      </span>
                      <p className="min-w-0 flex-1 pt-0.5 font-medium text-ink">
                        {p.thenAction || "—"}
                      </p>
                    </div>
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
