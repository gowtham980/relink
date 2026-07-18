"use client";

import { useEffect, useState } from "react";
import { emptyState, loadState, saveState } from "@/lib/store";

export default function SettingsPage() {
  const [health, setHealth] = useState<Record<string, unknown> | null>(null);
  const [cleared, setCleared] = useState(false);

  useEffect(() => {
    fetch("/api/coach")
      .then((r) => r.json())
      .then(setHealth)
      .catch(() => setHealth({ ok: false }));
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

  return (
    <div className="mx-auto max-w-lg space-y-4">
      <h1 className="font-display text-3xl font-semibold">Settings</h1>
      <div className="card space-y-2 p-5 text-sm">
        <h2 className="font-semibold">Coach service</h2>
        <pre className="overflow-x-auto rounded-lg bg-sand p-3 text-xs">
          {JSON.stringify(health, null, 2)}
        </pre>
        <p className="text-dusk">
          Set <code className="rounded bg-sand px-1">RELINK_LLM_PROVIDER=ollama</code> and{" "}
          <code className="rounded bg-sand px-1">OLLAMA_API_KEY</code> on the coach service for
          Ollama Cloud (<code>glm-5.2</code> + <code>kimi-k2.7-code</code>). Default is mock.
        </p>
      </div>
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
          <a href="/onboarding" className="underline">
            Re-onboard
          </a>
        </p>
      )}
    </div>
  );
}
