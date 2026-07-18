"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { HabitType } from "@/domain/types";
import { emptyState, loadState, saveState, uid } from "@/lib/store";
import { invokeCoach } from "@/lib/coach-client";
import { daysPracticed } from "@/domain/metrics";

const HABITS: { id: HabitType; label: string }[] = [
  { id: "screen_time", label: "Excessive screen time" },
  { id: "social_media", label: "Social media / doomscroll" },
  { id: "nicotine", label: "Nicotine" },
  { id: "alcohol", label: "Alcohol" },
  { id: "custom", label: "Something else" },
];

const VALUE_OPTS = ["Health", "Family", "Focus", "Mornings", "Money", "Calm", "Self-respect"];

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [habitType, setHabitType] = useState<HabitType>("social_media");
  const [habitLabel, setHabitLabel] = useState("");
  const [values, setValues] = useState<string[]>(["Focus", "Mornings"]);
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function toggleValue(v: string) {
    setValues((prev) => (prev.includes(v) ? prev.filter((x) => x !== v) : [...prev, v]));
  }

  async function finish() {
    setLoading(true);
    setError("");
    try {
      const profile = await invokeCoach("profile", {
        habitType,
        notes,
        values,
      });
      const suggested = (profile.suggestedPlans as { ifCue: string; thenAction: string }[]) || [];
      const state = {
        ...emptyState(),
        ...loadState(),
        onboarded: true,
        habitType,
        habitLabel:
          habitLabel || HABITS.find((h) => h.id === habitType)?.label || habitType,
        values,
        identity: String(profile.identity || "Someone rebuilding healthier patterns"),
        stageOfChange: String(profile.stageOfChange || "preparation"),
        triggers: (profile.triggers as string[]) || [],
        riskWindows: (profile.riskWindows as string[]) || [],
        plans: suggested.map((p) => ({
          id: uid(),
          ifCue: p.ifCue,
          thenAction: p.thenAction,
          active: true,
          origin: "ai" as const,
        })),
        daysPracticed: daysPracticed(loadState().checkIns),
      };
      saveState(state);
      router.push("/home");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Onboarding failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <h1 className="font-display text-3xl font-semibold">Let&apos;s map your habit loop</h1>
      <p className="text-dusk">Step {step + 1} of 3 — takes about a minute.</p>

      {step === 0 && (
        <fieldset className="card space-y-3 p-5">
          <legend className="font-semibold">What are you working on?</legend>
          <div className="grid gap-2">
            {HABITS.map((h) => (
              <label
                key={h.id}
                className="flex cursor-pointer items-center gap-3 rounded-xl border border-black/10 px-3 py-3 hover:bg-sand"
              >
                <input
                  type="radio"
                  name="habit"
                  checked={habitType === h.id}
                  onChange={() => setHabitType(h.id)}
                />
                <span>{h.label}</span>
              </label>
            ))}
          </div>
          {habitType === "custom" && (
            <div>
              <label className="label" htmlFor="custom-label">
                Describe it
              </label>
              <input
                id="custom-label"
                className="input"
                value={habitLabel}
                onChange={(e) => setHabitLabel(e.target.value)}
              />
            </div>
          )}
          <button type="button" className="btn-primary" onClick={() => setStep(1)}>
            Continue
          </button>
        </fieldset>
      )}

      {step === 1 && (
        <fieldset className="card space-y-3 p-5">
          <legend className="font-semibold">What values matter here?</legend>
          <div className="flex flex-wrap gap-2">
            {VALUE_OPTS.map((v) => {
              const on = values.includes(v);
              return (
                <button
                  key={v}
                  type="button"
                  onClick={() => toggleValue(v)}
                  className={`rounded-full px-3 py-1.5 text-sm font-medium ring-1 ${
                    on ? "bg-pine text-white ring-pine" : "bg-white text-dusk ring-black/10"
                  }`}
                  aria-pressed={on}
                >
                  {v}
                </button>
              );
            })}
          </div>
          <div className="flex gap-2">
            <button type="button" className="btn-ghost" onClick={() => setStep(0)}>
              Back
            </button>
            <button type="button" className="btn-primary" onClick={() => setStep(2)}>
              Continue
            </button>
          </div>
        </fieldset>
      )}

      {step === 2 && (
        <div className="card space-y-3 p-5">
          <label className="label" htmlFor="notes">
            When does it hit hardest? (optional)
          </label>
          <textarea
            id="notes"
            className="input min-h-[100px]"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="e.g. late nights alone, after stressful meetings…"
          />
          {error && (
            <p className="text-sm text-coral" role="alert">
              {error}
            </p>
          )}
          <div className="flex gap-2">
            <button type="button" className="btn-ghost" onClick={() => setStep(1)}>
              Back
            </button>
            <button
              type="button"
              className="btn-primary"
              disabled={loading}
              onClick={finish}
            >
              {loading ? "Building your profile…" : "Create my plans"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
