import type { CheckIn, Slip } from "./types";

/** Days with any check-in (practice metric — not a toxic streak). */
export function daysPracticed(checkIns: CheckIn[]): number {
  const days = new Set(checkIns.map((c) => c.date.slice(0, 10)));
  return days.size;
}

/** Slip recoveries logged. */
export function repairCount(slips: Slip[]): number {
  return slips.length;
}

export function averageUrge(checkIns: CheckIn[]): number {
  if (!checkIns.length) return 0;
  const sum = checkIns.reduce((a, c) => a + c.urgeLevel, 0);
  return Math.round((sum / checkIns.length) * 10) / 10;
}

export function slipRate(checkIns: CheckIn[]): number {
  if (!checkIns.length) return 0;
  const slips = checkIns.filter((c) => c.slipped).length;
  return Math.round((slips / checkIns.length) * 100);
}

/** Best-effort parse of insight plan edits into if-then plans. */
export function parsePlanEdit(text: string): { ifCue: string; thenAction: string } {
  const raw = (text || "").trim();
  const cleaned = raw.replace(/^add:\s*/i, "").trim();
  const m = cleaned.match(/^if\s+(.+?)[,\s]+then\s+(.+)$/i);
  if (m) {
    return { ifCue: m[1].trim(), thenAction: m[2].trim() };
  }
  return {
    ifCue: "When a familiar risk window appears",
    thenAction: cleaned || "Pause, rate the urge 0–10, and open Relink Urge SOS",
  };
}
