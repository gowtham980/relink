export type CoachAction =
  | "profile"
  | "plans"
  | "urge"
  | "slip"
  | "coach"
  | "insight"
  | "nudge";

export async function invokeCoach(
  action: CoachAction,
  payload: Record<string, unknown> = {}
): Promise<Record<string, unknown>> {
  const res = await fetch("/api/coach", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, payload }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || `Coach error ${res.status}`);
  }
  return res.json();
}
