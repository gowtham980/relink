"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { emptyState, loadState, saveState } from "@/lib/store";

type Health = {
  ok?: boolean;
  provider?: string;
  model_coach?: string;
  model_struct?: string;
  fallback?: string | null;
  ollama_timeout_s?: number;
  coachService?: string;
  [key: string]: unknown;
};

function providerLabel(p?: string): string {
  if (p === "ollama") return "Ollama Cloud";
  if (p === "gemini") return "Vertex Gemini";
  if (p === "mock" || p === "mock-fallback") return "Offline mock";
  return p || "Unknown";
}

export default function SettingsPage() {
  const [health, setHealth] = useState<Health | null>(null);
  const [cleared, setCleared] = useState(false);

  useEffect(() => {
    fetch("/api/coach")
      .then((r) => r.json())
      .then((d) => setHealth(d as Health))
      .catch(() => setHealth({ ok: false, coachService: "down" }));
  }, []);

  function exportData() {
    const blob = new Blob([JSON.stringify(loadState(), null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "relink-export.json";
    a.click();
    URL.revokeObjectURL(url);
  }

  function reset() {
    if (!confirm("Delete all local Relink data on this device?")) return;
    saveState(emptyState());
    setCleared(true);
  }

  const online = health?.ok !== false && health?.coachService !== "down";
  const provider = providerLabel(String(health?.provider || ""));

  return (
    <div className="mx-auto max-w-lg space-y-4">
      <h1 className="font-display text-3xl font-semibold">Settings</h1>

      <div className="card space-y-3 p-5">
        <h2 className="font-semibold">Coach status</h2>
        {health === null ? (
          <p className="text-sm text-dusk">Checking coach…</p>
        ) : (
          <ul className="space-y-2 text-sm">
            <li className="flex items-center justify-between gap-2">
              <span className="text-dusk">Service</span>
              <span
                className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
                  online ? "bg-pine/10 text-pine" : "bg-coral/10 text-coral"
                }`}
              >
                {online ? `Online · ${provider}` : "Offline mode"}
              </span>
            </li>
            {health.model_coach && (
              <li className="flex items-center justify-between gap-2">
                <span className="text-dusk">Coach model</span>
                <span className="font-medium text-ink">{String(health.model_coach)}</span>
              </li>
            )}
            {health.model_struct && (
              <li className="flex items-center justify-between gap-2">
                <span className="text-dusk">Structured model</span>
                <span className="font-medium text-ink">{String(health.model_struct)}</span>
              </li>
            )}
            {health.fallback && (
              <li className="flex items-center justify-between gap-2">
                <span className="text-dusk">Fallback</span>
                <span className="font-medium text-ink">
                  {health.fallback === "vertex" ? "Vertex Gemini" : String(health.fallback)}
                </span>
              </li>
            )}
            {typeof health.ollama_timeout_s === "number" && (
              <li className="flex items-center justify-between gap-2">
                <span className="text-dusk">Timeout</span>
                <span className="font-medium text-ink">{health.ollama_timeout_s}s</span>
              </li>
            )}
          </ul>
        )}
        <p className="text-xs text-dusk">
          Keys stay on the coach server. Your habit data stays in this browser until you export or
          delete it.
        </p>
        <details className="rounded-xl bg-sand px-3 py-2 text-xs">
          <summary className="cursor-pointer font-medium text-dusk">Technical details</summary>
          <pre className="mt-2 overflow-x-auto text-[11px] text-dusk">
            {JSON.stringify(health, null, 2)}
          </pre>
        </details>
      </div>

      <div className="card space-y-3 p-5">
        <h2 className="font-semibold">Your data</h2>
        <p className="text-sm text-dusk">
          Export a JSON backup or wipe everything on this device. No cloud account in this OSS
          build.
        </p>
        <div className="flex flex-wrap gap-2">
          <button type="button" className="btn-primary" onClick={exportData}>
            Export my data
          </button>
          <button type="button" className="btn-danger" onClick={reset}>
            Delete local data
          </button>
        </div>
        {cleared && (
          <p className="text-sm text-pine" role="status">
            Local data cleared.{" "}
            <Link href="/onboarding" className="underline">
              Re-onboard
            </Link>
          </p>
        )}
      </div>

      <p className="text-center text-sm text-dusk">
        <Link href="/ethics" className="underline">
          Ethics & crisis resources
        </Link>
      </p>
    </div>
  );
}
