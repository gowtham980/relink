import { NextRequest, NextResponse } from "next/server";

const COACH_URL = process.env.COACH_URL || "http://127.0.0.1:8787";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const action = String(body.action || "");
    const payload = body.payload || {};
    if (!action) {
      return NextResponse.json({ error: "action required" }, { status: 400 });
    }
    if (JSON.stringify(payload).length > 50_000) {
      return NextResponse.json({ error: "payload too large" }, { status: 413 });
    }

    const r = await fetch(`${COACH_URL}/v1/invoke`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, payload }),
      signal: AbortSignal.timeout(90_000),
    });

    if (!r.ok) {
      // Fallback mock if coach service down
      if (r.status >= 500 || r.status === 0) {
        return NextResponse.json(localMock(action, payload));
      }
      const text = await r.text();
      return NextResponse.json({ error: text }, { status: r.status });
    }
    const data = await r.json();
    return NextResponse.json(data);
  } catch {
    try {
      const body = await req.clone().json();
      return NextResponse.json(localMock(String(body.action || "coach"), body.payload || {}));
    } catch {
      return NextResponse.json(localMock("coach", {}));
    }
  }
}

function localMock(action: string, payload: Record<string, unknown>) {
  const disclaimer =
    "Relink is a wellness support tool, not medical care or therapy.";
  switch (action) {
    case "profile":
      return {
        stageOfChange: "preparation",
        triggers: ["boredom", "late night"],
        riskWindows: ["21:00-24:00"],
        identity: "Someone who protects their mornings",
        suggestedPlans: [
          {
            ifCue: "I unlock my phone in bed after 10pm",
            thenAction: "I plug it across the room and open Relink Urge SOS",
          },
          {
            ifCue: "I feel bored between tasks",
            thenAction: "I stand up, drink water, and set a 10-minute timer",
          },
          {
            ifCue: "I want to open social media",
            thenAction: "I open Relink check-in first and rate my urge 0-10",
          },
        ],
        disclaimer,
      };
    case "plans":
      return {
        plans: [
          {
            ifCue: "I feel the urge to scroll",
            thenAction: "I name the urge, rate it, and wait 2 minutes",
          },
          {
            ifCue: "Friends invite a high-risk setting",
            thenAction: "I suggest a lower-risk alternative first",
          },
          {
            ifCue: "I slip",
            thenAction: "I open Slip Recovery within 1 hour without self-blame",
          },
        ],
      };
    case "urge":
      return {
        blocked: false,
        mode: "urge",
        reply:
          "Name the urge. Rate it 0–10. Breathe for 90 seconds — urges rise and fall. Then run your if-then plan. Opening Relink is already a vote for who you're becoming.",
        nextStep: Number(payload.step || 0) + 1,
        disclaimer,
      };
    case "slip":
      return {
        blocked: false,
        mode: "slip",
        reply:
          "A slip is data, not identity. What happened right before? For the next 24 hours: one small plan, one check-in. You practiced recovery — that counts.",
        disclaimer,
      };
    case "insight":
      return {
        summary: "Harder evenings often follow unstructured nights.",
        patterns: ["Urges peak late evening"],
        suggestedPlanEdits: [
          "If it is 20:30 and I am alone, then I start a 15-minute walk.",
        ],
        disclaimer,
      };
    case "nudge":
      return { nudge: "One small vote now: delay the habit by two minutes.", disclaimer };
    default:
      return {
        blocked: false,
        mode: "mi",
        reply:
          "Thanks for showing up. What matters most to you about changing this habit? What's one step that feels doable today?",
        disclaimer,
      };
  }
}

export async function GET() {
  try {
    const r = await fetch(`${COACH_URL}/health`, { signal: AbortSignal.timeout(3000) });
    if (r.ok) return NextResponse.json(await r.json());
  } catch {
    /* empty */
  }
  return NextResponse.json({ ok: true, provider: "mock-fallback", coachService: "down" });
}
