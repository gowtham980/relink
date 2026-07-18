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
