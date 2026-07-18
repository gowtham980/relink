"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import type { CheckIn } from "@/domain/types";
import { daysPracticed } from "@/domain/metrics";
import { loadState, saveState, uid } from "@/lib/store";

const MOOD_EMOJI = ["", "😞", "😟", "😐", "🙂", "😄"];
const MOOD_LABELS = ["", "Low", "Off", "Okay", "Good", "Great"];

function isSameDay(iso: string, d = new Date()): boolean {
  const a = new Date(iso);
  return (
    a.getFullYear() === d.getFullYear() &&
    a.getMonth() === d.getMonth() &&
    a.getDate() === d.getDate()
  );
}

function urgeWord(n: number): string {
  if (n <= 2) return "Calm";
  if (n <= 5) return "Moderate";
  if (n <= 7) return "Strong";
  return "Intense";
}

export default function CheckInPage() {
  const router = useRouter();
  const [mood, setMood] = useState(3);
  const [urge, setUrge] = useState(4);
  const [slipped, setSlipped] = useState(false);
  const [note, setNote] = useState("");
  const [saved, setSaved] = useState(false);
  const [savedSlipped, setSavedSlipped] = useState(false);
  const [slipHref, setSlipHref] = useState("/slip");
  const [practiced, setPracticed] = useState(0);
  const [recent, setRecent] = useState<CheckIn[]>([]);
  const [todayLog, setTodayLog] = useState<CheckIn | null>(null);
  const [confirmDup, setConfirmDup] = useState(false);

  useEffect(() => {
    const s = loadState();
    if (!s.onboarded) router.replace("/onboarding");
    else {
      setRecent(s.checkIns.slice(0, 3));
      setPracticed(daysPracticed(s.checkIns));
      const last = s.checkIns[0];
      if (last && isSameDay(last.date)) setTodayLog(last);
    }
  }, [router]);

  const urgeHint = useMemo(() => urgeWord(urge), [urge]);

  function doSave() {
    const state = loadState();
    const date = new Date().toISOString();
    state.checkIns = [
      {
        id: uid(),
        date,
        mood,
        urgeLevel: urge,
        slipped,
        note,
      },
      ...state.checkIns,
    ];
    state.daysPracticed = daysPracticed(state.checkIns);
    saveState(state);
    setPracticed(state.daysPracticed);
    setRecent(state.checkIns.slice(0, 3));
    setTodayLog(state.checkIns[0]);
    setSavedSlipped(slipped);
    if (slipped) {
      const ctx = note.trim() || `Slipped today · mood ${mood} · urge ${urge}`;
      setSlipHref(`/slip?context=${encodeURIComponent(ctx)}`);
    } else {
      setSlipHref("/slip");
    }
    setSaved(true);
    setConfirmDup(false);
    setMood(3);
    setUrge(4);
    setSlipped(false);
    setNote("");
  }

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (todayLog && !confirmDup && !saved) {
      setConfirmDup(true);
      return;
    }
    doSave();
  }

  return (
    <div className="mx-auto max-w-lg space-y-4">
      <div>
        <h1 className="font-display text-3xl font-semibold">Daily check-in</h1>
        <p className="text-dusk">Honest logs beat perfect streaks.</p>
      </div>

      {todayLog && !saved && (
        <div className="card border-pine/20 bg-emerald-50/60 px-4 py-3 text-sm text-dusk" role="status">
          <strong className="text-pine">Already checked in today</strong>
          <span className="mt-0.5 block">
            {MOOD_EMOJI[todayLog.mood]} mood {todayLog.mood} · urge {todayLog.urgeLevel}
            {todayLog.slipped ? " · slipped" : ""}
            {todayLog.note ? ` · “${todayLog.note}”` : ""}
          </span>
          <span className="mt-1 block text-xs">Log again only if something changed.</span>
        </div>
      )}

      <form onSubmit={submit} className="card space-y-5 p-5">
        <div>
          <div className="mb-2 flex items-end justify-between">
            <label className="label mb-0" htmlFor="mood">
              Mood
            </label>
            <span className="text-2xl" aria-hidden>
              {MOOD_EMOJI[mood]}
            </span>
          </div>
          <div className="mb-2 flex justify-between gap-1" role="group" aria-label="Quick mood">
            {[1, 2, 3, 4, 5].map((n) => (
              <button
                key={n}
                type="button"
                onClick={() => setMood(n)}
                className={`flex flex-1 flex-col items-center rounded-xl py-2 text-lg transition ${
                  mood === n ? "bg-pine/15 ring-2 ring-pine" : "bg-sand hover:bg-black/5"
                }`}
                aria-pressed={mood === n}
                aria-label={`Mood ${n}: ${MOOD_LABELS[n]}`}
              >
                <span aria-hidden>{MOOD_EMOJI[n]}</span>
                <span className="text-[10px] font-medium text-dusk">{MOOD_LABELS[n]}</span>
              </button>
            ))}
          </div>
          <input
            id="mood"
            type="range"
            min={1}
            max={5}
            value={mood}
            onChange={(e) => setMood(Number(e.target.value))}
            className="w-full accent-pine"
            aria-valuetext={`${mood} ${MOOD_LABELS[mood]}`}
          />
        </div>

        <div>
          <div className="mb-1 flex items-end justify-between">
            <label className="label mb-0" htmlFor="urge">
              Urge level
            </label>
            <span className="rounded-full bg-pine/10 px-2.5 py-0.5 text-sm font-semibold text-pine">
              {urge}/10 · {urgeHint}
            </span>
          </div>
          <input
            id="urge"
            type="range"
            min={0}
            max={10}
            value={urge}
            onChange={(e) => setUrge(Number(e.target.value))}
            className="w-full accent-pine"
            aria-valuetext={`${urge} ${urgeHint}`}
          />
          <div className="mt-1 flex justify-between text-[11px] text-dusk">
            <span>Calm 0</span>
            <span>Moderate 5</span>
            <span>Intense 10</span>
          </div>
        </div>

        <button
          type="button"
          onClick={() => setSlipped((v) => !v)}
          className={`w-full rounded-2xl border px-4 py-3 text-left transition ${
            slipped
              ? "border-coral/40 bg-coral/10 ring-2 ring-coral/30"
              : "border-black/10 bg-white hover:bg-sand"
          }`}
          aria-pressed={slipped}
        >
          <span className="flex items-center justify-between gap-2">
            <span className="font-semibold text-ink">I slipped today</span>
            <span
              className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
                slipped ? "bg-coral text-white" : "bg-sand text-dusk"
              }`}
            >
              {slipped ? "Yes" : "No"}
            </span>
          </span>
          <span className="mt-1 block text-xs text-dusk">
            That&apos;s data, not failure — we&apos;ll help you repair it.
          </span>
        </button>

        <div>
          <label className="label" htmlFor="note">
            One-line note <span className="font-normal text-dusk/70">(optional)</span>
          </label>
          <input
            id="note"
            className="input"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            maxLength={280}
            placeholder="e.g. late night, after a hard meeting…"
          />
        </div>

        {confirmDup && (
          <div className="rounded-xl border border-pine/20 bg-sand px-3 py-3 text-sm" role="alertdialog">
            <p className="text-dusk">You already logged today. Save another entry?</p>
            <div className="mt-2 flex gap-2">
              <button type="button" className="btn-ghost" onClick={() => setConfirmDup(false)}>
                Cancel
              </button>
              <button type="button" className="btn-primary" onClick={doSave}>
                Save another
              </button>
            </div>
          </div>
        )}

        {!confirmDup && (
          <button type="submit" className="btn-primary w-full">
            Save check-in
          </button>
        )}

        {saved && (
          <div className="rounded-xl bg-pine/10 px-3 py-3 text-sm text-pine" role="status">
            <p className="font-semibold">Saved · Day {practiced} practiced</p>
            <p className="mt-1">
              {savedSlipped ? (
                <Link href={slipHref} className="font-semibold underline">
                  Open slip recovery →
                </Link>
              ) : (
                <Link href="/home" className="font-semibold underline">
                  Back home →
                </Link>
              )}
              {" · "}
              <Link href="/insights" className="underline">
                Insights
              </Link>
            </p>
          </div>
        )}
      </form>

      <section aria-label="Recent check-ins">
        <h2 className="mb-2 text-sm font-semibold text-ink">Recent logs</h2>
        {recent.length === 0 ? (
          <p className="text-sm text-dusk">None yet — your first check-in starts the practice count.</p>
        ) : (
          <ul className="space-y-2">
            {recent.map((c) => (
              <li
                key={c.id}
                className="card flex flex-wrap items-center justify-between gap-2 px-3 py-2 text-sm"
              >
                <span className="text-dusk">
                  {new Date(c.date).toLocaleString(undefined, {
                    month: "short",
                    day: "numeric",
                    hour: "numeric",
                    minute: "2-digit",
                  })}
                </span>
                <span>
                  <span aria-hidden>{MOOD_EMOJI[c.mood] || "·"}</span> mood {c.mood} · urge{" "}
                  {c.urgeLevel}
                  {c.slipped ? (
                    <span className="ml-1 rounded-full bg-coral/15 px-1.5 py-0.5 text-xs text-coral">
                      slipped
                    </span>
                  ) : null}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
