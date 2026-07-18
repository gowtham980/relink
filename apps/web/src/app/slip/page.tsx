"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { loadState, saveState, uid } from "@/lib/store";
import { invokeCoach } from "@/lib/coach-client";
import { repairCount } from "@/domain/metrics";

function SlipForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [context, setContext] = useState("");
  const [next24h, setNext24h] = useState("");
  const [reply, setReply] = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!loadState().onboarded) router.replace("/onboarding");
    const pre = searchParams.get("context");
    if (pre) setContext(pre);
  }, [router, searchParams]);

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
        const cue = context.trim()
          ? `After: ${context.trim().slice(0, 80)}`
          : "In the next 24 hours after a slip";
        state.plans = [
          {
            id: uid(),
            ifCue: cue,
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
    <>
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
            <div className="flex flex-wrap gap-3 text-sm font-semibold text-pine">
              <Link href="/plans" className="underline">
                View updated plans →
              </Link>
              <Link href="/coach" className="underline">
                Talk with coach →
              </Link>
            </div>
          )}
        </div>
      )}
    </>
  );
}

export default function SlipPage() {
  return (
    <div className="mx-auto max-w-lg space-y-4">
      <h1 className="font-display text-3xl font-semibold">Slip recovery</h1>
      <p className="text-dusk">
        A lapse is not a relapse. We repair the plan — we don&apos;t erase your identity.
      </p>
      <Suspense fallback={<div className="card p-5 text-sm text-dusk">Loading…</div>}>
        <SlipForm />
      </Suspense>
    </div>
  );
}
