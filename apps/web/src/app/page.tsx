import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="grid gap-10 py-8 md:grid-cols-2 md:items-center">
      <div className="space-y-6">
        <p className="text-sm font-semibold uppercase tracking-wider text-pine">
          GenAI habit coach
        </p>
        <h1 className="font-display text-4xl font-semibold leading-tight text-ink sm:text-5xl">
          Pause the urge.
          <br />
          Plan the next move.
          <br />
          <span className="text-pine">Relink who you&apos;re becoming.</span>
        </h1>
        <p className="max-w-prose text-lg text-dusk">
          Blockers get turned off under stress. Streaks punish one slip. Relink combines
          if-then plans, urge SOS, adaptive coaching, and shame-free recovery — powered by
          multi-agent GenAI.
        </p>
        <div className="flex flex-wrap gap-3">
          <Link href="/onboarding" className="btn-primary">
            Get started
          </Link>
          <Link href="/ethics" className="btn-ghost">
            Safety &amp; ethics
          </Link>
        </div>
        <p className="text-sm text-dusk">Takes about a minute — no account needed.</p>
        <ul className="grid gap-2 text-sm text-dusk sm:grid-cols-2">
          <li className="card px-3 py-2">✓ Intelligent nudges</li>
          <li className="card px-3 py-2">✓ Personalized tracking</li>
          <li className="card px-3 py-2">✓ Adaptive MI/CBT coaching</li>
          <li className="card px-3 py-2">✓ Slip recovery support</li>
        </ul>
      </div>
      <div className="card space-y-4 p-6">
        <h2 className="font-display text-xl font-semibold">How it works</h2>
        <ol className="space-y-3 text-sm text-dusk">
          <li>
            <strong className="text-ink">1. Map</strong> — habit, triggers, values, identity
          </li>
          <li>
            <strong className="text-ink">2. Plan</strong> — AI co-writes implementation intentions
          </li>
          <li>
            <strong className="text-ink">3. Ride</strong> — Urge SOS when cravings spike
          </li>
          <li>
            <strong className="text-ink">4. Repair</strong> — slips update risk maps, not shame
          </li>
        </ol>
        <p className="rounded-xl bg-sand px-3 py-2 text-xs text-dusk">
          Not a medical device. Not therapy. For clinical addiction care, see a licensed
          professional.
        </p>
      </div>
    </div>
  );
}
