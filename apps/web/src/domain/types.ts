export type HabitType =
  | "screen_time"
  | "social_media"
  | "nicotine"
  | "alcohol"
  | "custom";

export type PlanOrigin = "ai" | "user" | "slip";

export interface Plan {
  id: string;
  ifCue: string;
  thenAction: string;
  active: boolean;
  origin?: PlanOrigin;
}

export interface CheckIn {
  id: string;
  date: string;
  mood: number;
  urgeLevel: number;
  slipped: boolean;
  note: string;
}

export interface Slip {
  id: string;
  at: string;
  context: string;
  next24h: string;
}

export interface Insight {
  summary: string;
  patterns: string[];
  suggestedPlanEdits: string[];
  at: string;
}

export interface UserState {
  onboarded: boolean;
  habitType: HabitType;
  habitLabel: string;
  values: string[];
  identity: string;
  stageOfChange: string;
  triggers: string[];
  riskWindows: string[];
  plans: Plan[];
  checkIns: CheckIn[];
  slips: Slip[];
  insight: Insight | null;
  coachHistory: { role: "user" | "assistant"; content: string }[];
  daysPracticed: number;
  repairs: number;
}
