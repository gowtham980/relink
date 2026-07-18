"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import type { UserState } from "@/domain/types";
import { emptyState, loadState } from "@/lib/store";
import { averageUrge, daysPracticed, repairCount } from "@/domain/metrics";

export default function HomePage() {
  const [state, setState] = useState<UserState>(emptyState());

  useEffect(() => {
    setState(loadState());
  }, []);

  if (!state.onboarded) {
    return (
      <div className="card mx-auto max-w-lg space-y-4 p-6 text-center">
        <h1 className="font-display text-2xl font-semibold">Welcome to Relink</h1>
        <p className="text-dusk">Complete a short onboarding to personalize coaching.</p>
        <Link href="/onboarding" className="btn-primary">
          Start onboarding
        </Link>
      </div>
    );
  }

  const practiced = daysPracticed(state.checkIns);
  const repairs = repairCount(state.slips);
  const avg = averageUrge(state.checkIns);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-3xl font-semibold">Today</h1>
        <p className="text-dusk">
          Working on <strong className="text-ink">{state.habitLabel}</strong>
          {state.identity ? ` · “${state.identity}”` : ""}
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <div className="card p-4">
          <p className="text-xs uppercase text-dusk">Days practiced</p>
          <p className="font-display text-3xl font-semibold text-pine">{practiced}</p>
        </div>
        <div className="card p-4">
          <p className="text-xs uppercase text-dusk">Repairs</p>
          <p className="font-display text-3xl font-semibold text-pine">{repairs}</p>
        </div>
        <div className="card p-4">
          <p className="text-xs uppercase text-dusk">Avg urge</p>
          <p className="font-display text-3xl font-semibold text-pine">{avg || "—"}</p>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <Link
          href="/urge"
          className="card flex flex-col gap-2 border-pine/20 bg-gradient-to-br from-white to-emerald-50 p-5 hover:ring-2 hover:ring-moss"
        >
          <span className="text-sm font-semibold text-pine">Need help now</span>
          <span className="font-display text-2xl font-semibold">Urge SOS</span>
          <span className="text-sm text-dusk">Guided 5-minute urge surfing protocol</span>
        </Link>
        <Link href="/check-in" className="card flex flex-col gap-2 p-5 hover:ring-2 hover:ring-moss">
          <span className="text-sm font-semibold text-dusk">Daily loop</span>
          <span className="font-display text-2xl font-semibold">Check-in</span>
          <span className="text-sm text-dusk">Mood, urge rating, slip log</span>
        </Link>
        <Link href="/plans" className="card flex flex-col gap-2 p-5 hover:ring-2 hover:ring-moss">
          <span className="text-sm font-semibold text-dusk">If-then</span>
          <span className="font-display text-2xl font-semibold">
            {state.plans.length} active plans
          </span>
          <span className="text-sm text-dusk">Edit implementation intentions</span>
        </Link>
        <Link href="/coach" className="card flex flex-col gap-2 p-5 hover:ring-2 hover:ring-moss">
          <span className="text-sm font-semibold text-dusk">Adaptive</span>
          <span className="font-display text-2xl font-semibold">Coach chat</span>
          <span className="text-sm text-dusk">MI-style conversation with memory</span>
        </Link>
      </div>

      {state.riskWindows.length > 0 && (
        <div className="card p-4 text-sm text-dusk">
          <strong className="text-ink">Risk windows:</strong> {state.riskWindows.join(", ")}
          {state.triggers.length > 0 && (
            <>
              {" "}
              · <strong className="text-ink">Triggers:</strong> {state.triggers.join(", ")}
            </>
          )}
        </div>
      )}
    </div>
  );
}
