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

  useEffect(() => {
    if (!loadState().onboarded) router.replace("/onboarding");
  }, [router]);

  async function send(e?: React.FormEvent) {
    e?.preventDefault();
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput("");
    setMsgs((m) => [...m, { role: "user", content: userMsg }]);
    setLoading(true);
    try {
      const res = await invokeCoach("urge", {
        message: userMsg,
        step,
        history: msgs,
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

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <h1 className="font-display text-3xl font-semibold">Urge SOS</h1>
      <p className="text-dusk">
        Ride the wave. Step {Math.min(step + 1, 5)}/5 — name → rate → surf → if-then → substitute.
      </p>

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
                Press start to begin a guided urge protocol. Your plans stay on the Plans page.
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
