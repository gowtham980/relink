"use client";

import type { UserState } from "@/domain/types";

const KEY = "relink.user.v1";

export const emptyState = (): UserState => ({
  onboarded: false,
  habitType: "screen_time",
  habitLabel: "",
  values: [],
  identity: "",
  stageOfChange: "",
  triggers: [],
  riskWindows: [],
  plans: [],
  checkIns: [],
  slips: [],
  insight: null,
  coachHistory: [],
  daysPracticed: 0,
  repairs: 0,
});

export function loadState(): UserState {
  if (typeof window === "undefined") return emptyState();
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return emptyState();
    return { ...emptyState(), ...JSON.parse(raw) };
  } catch {
    return emptyState();
  }
}

export function saveState(state: UserState): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(KEY, JSON.stringify(state));
}

export function uid(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}
