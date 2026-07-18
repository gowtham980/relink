"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { daysPracticed } from "@/domain/metrics";
import { loadState, saveState, uid } from "@/lib/store";

export default function CheckInPage() {
  const router = useRouter();
  const [mood, setMood] = useState(3);
  const [urge, setUrge] = useState(4);
  const [slipped, setSlipped] = useState(false);
  const [note, setNote] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!loadState().onboarded) router.replace("/onboarding");
  }, [router]);

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const state = loadState();
    state.checkIns = [
      {
        id: uid(),
        date: new Date().toISOString(),
        mood,
        urgeLevel: urge,
        slipped,
        note,
      },
      ...state.checkIns,
    ];
    state.daysPracticed = daysPracticed(state.checkIns);
    saveState(state);
    setSaved(true);
  }

  return (
    <div className="mx-auto max-w-lg space-y-4">
      <h1 className="font-display text-3xl font-semibold">Daily check-in</h1>
      <p className="text-dusk">Honest logs beat perfect streaks.</p>
      <form onSubmit={submit} className="card space-y-4 p-5">
        <div>
          <label className="label" htmlFor="mood">
            Mood (1–5): {mood}
          </label>
          <input
            id="mood"
            type="range"
            min={1}
            max={5}
            value={mood}
            onChange={(e) => setMood(Number(e.target.value))}
            className="w-full"
          />
        </div>
        <div>
          <label className="label" htmlFor="urge">
            Urge level (0–10): {urge}
          </label>
          <input
            id="urge"
            type="range"
            min={0}
            max={10}
            value={urge}
            onChange={(e) => setUrge(Number(e.target.value))}
            className="w-full"
          />
        </div>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={slipped}
            onChange={(e) => setSlipped(e.target.checked)}
          />
          I slipped today (that&apos;s data, not failure)
        </label>
        <div>
          <label className="label" htmlFor="note">
            One-line note
          </label>
          <input
            id="note"
            className="input"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            maxLength={280}
          />
        </div>
        <button type="submit" className="btn-primary">
          Save check-in
        </button>
        {saved && (
          <p className="text-sm text-pine" role="status">
            Saved.{" "}
            {slipped ? (
              <a href="/slip" className="underline">
                Open slip recovery →
              </a>
            ) : (
              <a href="/home" className="underline">
                Back home →
              </a>
            )}
          </p>
        )}
      </form>
    </div>
  );
}
