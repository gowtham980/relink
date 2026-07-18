"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { loadState } from "@/lib/store";
import { invokeCoach } from "@/lib/coach-client";

type Msg = { role: "user" | "assistant"; content: string };

export default function UrgePage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [input, setInput] = useState("I'm having an urge right now.");
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [loading, setLoading] = useState(false);
  const [blocked, setBlocked] = useState<{ reply: string; resources?: { label: string; url: string }[] } | null>(null);
  const [planHint, setPlanHint] = useState<string>("");

  useEffect(() => {
    const s = loadState();
    if (!s.onboarded) router.replace("/onboarding");
    else {
      const top = s.plans.filter((p) => p.active)[0];
      if (top) setPlanHint(`If ${top.ifCue}, then ${top.thenAction}`);
    }
  }, [router]);

  async function send(e?: React.FormEvent) {
    e?.preventDefault();
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput("");
    setMsgs((m) => [...m, { role: "user", content: userMsg }]);
    setLoading(true);
    try {
      const s = loadState();
      const res = await invokeCoach("urge", {
        message: userMsg,
        step,
        history: msgs,
        activePlans: s.plans
          .filter((p) => p.active)
          .slice(0, 3)
          .map((p) => ({ ifCue: p.ifCue, thenAction: p.thenAction })),
      });
      if (res.blocked) {
        setBlocked({
          reply: String(res.reply),
          resources: res.resources as { label: string; url: string }[],
        });
      } else {
        setMsgs((m) => [...m, { role: "assistant", content: String(res.reply) }]);
        setStep(Number(res.nextStep ?? step + 1));
      }
    } catch (err) {
      setMsgs((m) => [
        ...m,
        {
          role: "assistant",
          content: err instanceof Error ? err.message : "Something went wrong",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  const stepNum = Math.min(step + 1, 5);
  const stepLabels = ["Name", "Rate", "Surf", "If-then", "Substitute"];

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <h1 className="font-display text-3xl font-semibold">Urge SOS</h1>
      <p className="text-dusk">
        Ride the wave. Step {stepNum}/5 — name → rate → surf → if-then → substitute.
      </p>
      <div
        className="space-y-2"
        role="progressbar"
        aria-valuemin={1}
        aria-valuemax={5}
        aria-valuenow={stepNum}
        aria-label={`Urge protocol step ${stepNum} of 5`}
      >
        <div className="grid grid-cols-5 gap-1.5">
          {[1, 2, 3, 4, 5].map((n) => (
            <div
              key={n}
              className={`h-2 rounded-full transition ${
                n <= stepNum ? "bg-pine" : "bg-black/10"
              } ${n === stepNum ? "ring-2 ring-pine/30 ring-offset-1" : ""}`}
            />
          ))}
        </div>
        <div className="grid grid-cols-5 gap-1 text-center text-[10px] font-medium text-dusk">
          {stepLabels.map((label, i) => (
            <span key={label} className={i + 1 === stepNum ? "text-pine" : undefined}>
              {label}
            </span>
          ))}
        </div>
      </div>
      {planHint && (
        <p className="rounded-xl bg-pine/10 px-3 py-2 text-sm text-pine">
          Your plan ready: <strong>{planHint}</strong>
        </p>
      )}

      {blocked ? (
        <div className="card space-y-3 border-coral/30 p-5" role="alert">
          <p className="font-semibold text-coral">Safety pause</p>
          <p>{blocked.reply}</p>
          <ul className="list-disc pl-5 text-sm">
            {(blocked.resources || []).map((r) => (
              <li key={r.url}>
                <a className="underline" href={r.url} target="_blank" rel="noreferrer">
                  {r.label}
                </a>
              </li>
            ))}
          </ul>
          <a href="/ethics" className="btn-primary inline-flex">
            Full crisis resources
          </a>
        </div>
      ) : (
        <>
          <div
            className="card min-h-[240px] space-y-3 p-4"
            aria-live="polite"
            aria-relevant="additions"
          >
            {msgs.length === 0 && (
              <p className="text-sm text-dusk">
                Press start to begin a guided urge protocol. Your active if-then plans are included.
              </p>
            )}
            {msgs.map((m, i) => (
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
            {loading && <p className="text-sm text-dusk">Coach is with you…</p>}
          </div>
          <form onSubmit={send} className="flex flex-wrap gap-2">
            <label className="sr-only" htmlFor="urge-input">
              Message
            </label>
            <input
              id="urge-input"
              className="input flex-1"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              maxLength={2000}
            />
            <button type="submit" className="btn-primary" disabled={loading}>
              {msgs.length ? "Send" : "Start SOS"}
            </button>
          </form>
        </>
      )}
    </div>
  );
}
