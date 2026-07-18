export default function EthicsPage() {
  return (
    <article className="prose prose-neutral mx-auto max-w-2xl space-y-4">
      <h1 className="font-display text-3xl font-semibold">Ethics &amp; safety</h1>
      <div className="card space-y-3 p-5 text-sm text-dusk">
        <p>
          <strong className="text-ink">Relink is a wellness support tool</strong>, not a medical
          device, not therapy, and not a substitute for professional care.
        </p>
        <p>
          We do not claim to cure addiction. Abruptly stopping alcohol or benzodiazepines can be
          dangerous — seek licensed medical supervision.
        </p>
        <h2 className="font-display text-xl font-semibold text-ink">Crisis resources</h2>
        <ul className="list-disc space-y-1 pl-5">
          <li>
            <a
              className="text-pine underline"
              href="https://www.iasp.info/suicidalthoughts/"
              target="_blank"
              rel="noreferrer"
            >
              IASP — resources for suicidal thoughts
            </a>
          </li>
          <li>Local emergency number (e.g. 112 / 911) if you are in immediate danger</li>
        </ul>
        <h2 className="font-display text-xl font-semibold text-ink">How we use AI</h2>
        <p>
          Coach modes use multi-agent protocols (profiler, plan lab, urge, slip, MI, insight) with
          a safety classifier first. API keys stay on the server. Your browser store is local to
          your device in this OSS build.
        </p>
        <h2 className="font-display text-xl font-semibold text-ink">Design principles</h2>
        <ul className="list-disc pl-5">
          <li>No public shame leaderboards</li>
          <li>Slips increase “repairs,” not identity failure</li>
          <li>Days practiced over toxic all-or-nothing streaks</li>
        </ul>
      </div>
    </article>
  );
}
