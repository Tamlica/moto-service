<script>
  import Schematic from '../lib/Schematic.svelte';
  import Gauge from '../lib/Gauge.svelte';
  import { describe, num } from '../lib/format.js';

  const REPO_URL = 'https://github.com/Tamlica/moto-service';
  const INSTALL = `git clone ${REPO_URL}.git
cd moto-service
cp .env.example .env
docker compose up -d --build`;

  // live demo: engine oil every 3,000 km or 90 days, same rule as app/due.py
  let kmSince = $state(2200);
  let daysSince = $state(40);
  let oil = $derived.by(() => {
    const km_left = 3000 - kmSince;
    const days_left = 90 - daysSince;
    const state = km_left <= 0 || days_left <= 0 ? 'overdue' : km_left <= 300 || days_left <= 14 ? 'soon' : 'ok';
    return { id: 1, part: 'engine_oil', name: 'Engine oil', every_km: 3000, every_days: 90, km_left, days_left, state };
  });
  const fixed = [
    { id: 2, part: 'chain', name: 'Chain clean & lube', every_km: 500, km_left: 120, state: 'soon' },
    { id: 3, part: 'oil_filter', name: 'Oil filter', every_km: 6000, km_left: 3800, state: 'ok' },
    { id: 4, part: 'air_filter', name: 'Air filter', every_km: 12000, km_left: 7400, state: 'ok' },
    { id: 5, part: 'spark_plug', name: 'Spark plug', every_km: 8000, km_left: 2600, state: 'ok' },
    { id: 6, part: 'brake_front', name: 'Front brake pads', every_km: 10000, km_left: 5100, state: 'ok' },
    { id: 7, part: 'brake_rear', name: 'Rear brake', every_km: 10000, km_left: 6900, state: 'ok' },
    { id: 8, part: 'brake_fluid', name: 'Brake fluid', every_days: 730, days_left: 410, state: 'ok' },
    { id: 9, part: 'coolant', name: 'Coolant', every_days: 730, days_left: 520, state: 'ok' },
    { id: 10, part: 'tire_front', name: 'Front tire', every_km: 20000, km_left: 11800, state: 'ok' },
    { id: 11, part: 'tire_rear', name: 'Rear tire', every_km: 15000, km_left: 4300, state: 'ok' },
  ];
  let tasks = $derived([oil, ...fixed]);
  const STAMP = { ok: ['OK', ''], soon: ['Due soon', 'stamp--soon'], overdue: ['Overdue', 'stamp--red'] };

  let copyState = $state(undefined);
  async function copy() {
    try {
      await navigator.clipboard.writeText(INSTALL);
      copyState = 'success';
    } catch {
      copyState = 'error';
    }
    setTimeout(() => (copyState = undefined), 1600);
  }

  const TRACKS = [
    ['Km or date, whichever comes first', 'Every item has a distance and a time interval. Oil that sat through a rainy season still gets flagged.'],
    ['A drawing of your bike', 'Scooter, underbone, sport or trail. Each part is coloured by its status. Tap one to see its history.'],
    ['One tap to mark it done', 'Back from the workshop? Tap Done. Changed your mind? Undo is right there, no confirm dialogs.'],
    ['A service book that keeps itself', 'Every visit with its date, km, cost and notes, grouped the way the mechanic did the work.'],
    ['Predicted due dates', 'Your average km per day turns "1,200 km left" into an actual date.'],
    ['Your data, exportable', 'Download everything as JSON any time. Self-host it and it never leaves your server.'],
  ];
</script>

<header class="lnav">
  <div class="in">
    <a class="brand" href="#/" aria-label="Moto Service home"><span class="dot" aria-hidden="true"></span>MOTO<span class="long">&nbsp;SERVICE</span></a>
    <nav aria-label="Main">
      <a class="gh" href={REPO_URL} rel="noopener">GitHub</a>
      <a href="#/login">Log in</a>
    </nav>
    <a class="btn btn--primary" href="#/login?mode=register">Create account</a>
  </div>
</header>

<main class="landing">
  <section class="hero">
    <h1>Know what your bike needs next</h1>
    <p class="lede">
      A service tracker for everyday riders. Log oil changes, parts and kilometres, and see what's due before it becomes a
      problem. Free and open source.
    </p>
    <div class="cta">
      <a class="btn btn--primary big" href="#/login?mode=register">Create account <span class="arrow" aria-hidden="true">→</span></a>
      <a class="btn big" href="#self-host">Self-host it</a>
    </div>
  </section>

  <!-- the demo cluster: drag the sliders, the drawing and the stamp follow -->
  <section class="demo panel-box" aria-labelledby="demo-h">
    <div class="stage">
      <p class="label">Example bike · drag the sliders</p>
      <Schematic type="sport" {tasks} title="Example sport bike, coloured by service status" />
    </div>
    <div class="ctrl">
      <h2 id="demo-h">Engine oil</h2>
      <p class="muted">Every 3,000 km or 90 days</p>
      <div class="read">
        <Gauge task={oil} size={112} />
        <div class="rt">
          <p class="desc">{describe(oil)}</p>
          {#key oil.state}
            <span class="stamp thunk {STAMP[oil.state][1]}" aria-live="polite">{STAMP[oil.state][0]}</span>
          {/key}
        </div>
      </div>
      <label class="field">
        <span>Ridden since last change <b class="lcd v">{num(kmSince)} km</b></span>
        <input type="range" min="0" max="3600" step="50" bind:value={kmSince} />
      </label>
      <label class="field">
        <span>Days since last change <b class="lcd v">{daysSince} d</b></span>
        <input type="range" min="0" max="120" bind:value={daysSince} />
      </label>
    </div>
  </section>

  <section class="tracks" aria-labelledby="tracks-h">
    <h2 id="tracks-h">What it keeps track of</h2>
    <ul>
      {#each TRACKS as [t, d] (t)}
        <li><h3>{t}</h3><p>{d}</p></li>
      {/each}
    </ul>
  </section>

  <section class="self panel-box" id="self-host" aria-labelledby="self-h">
    <div class="sc">
      <h2 id="self-h">Run it on your own server</h2>
      <p>
        One Docker Compose file: the app, Postgres and Caddy for automatic HTTPS. Point a domain at your VPS, set a password
        in <code>.env</code>, and it's live. MIT licensed: fork it, change it, share it.
      </p>
      <div class="sa">
        <a class="btn btn--primary" href={REPO_URL} rel="noopener">View on GitHub <span class="arrow" aria-hidden="true">→</span></a>
        <a class="btn btn--ghost" href="{REPO_URL}#self-hosting-on-a-vps" rel="noopener">Deploy guide</a>
      </div>
    </div>
    <figure class="code">
      <pre><code>{INSTALL}</code></pre>
      <button class="btn btn--small copy" onclick={copy} data-state={copyState}>
        {copyState === 'success' ? '✓ Copied' : copyState === 'error' ? 'Copy failed' : 'Copy'}
      </button>
      <span class="mit stamp stamp--round" aria-hidden="true">MIT<small>open source</small></span>
    </figure>
  </section>

  <section class="last" aria-labelledby="last-h">
    <h2 id="last-h">Start your service book</h2>
    <p class="muted">Add a bike, enter the odometer, and the common intervals are filled in for you.</p>
    <a class="btn btn--primary big" href="#/login?mode=register">Create account <span class="arrow" aria-hidden="true">→</span></a>
  </section>
</main>

<footer class="foot label">
  <span>Moto Service</span>
  <span>MIT licensed · <a href={REPO_URL} rel="noopener">source on GitHub</a></span>
</footer>

<style>
  /* Hallmark · page: landing · genre: atmospheric · theme: custom "Night dash + stamps" · design-system: design.md
   * macrostructure: Demo-Led (live cluster under a typographic hero) · nav: N9 edge-aligned · footer: Ft4 colophon line
   * enrichment: Tier B hand-built SVG schematic driven by live sliders · motion: gauge sweep · stamp thunk
   * pre-emit critique: P4 H5 E4 S5 R4 V4
   */
  .lnav { position: sticky; top: 0; z-index: 50; background: color-mix(in srgb, var(--color-paper) 88%, transparent); backdrop-filter: blur(10px); border-bottom: var(--rule-hair); }
  .in { max-width: var(--sheet-w); margin: 0 auto; padding: 0 var(--gutter); min-height: var(--nav-h); display: flex; align-items: center; gap: var(--space-xs); }
  .brand { display: inline-flex; align-items: center; gap: var(--space-2xs); font: 800 var(--text-base)/1 var(--font-display); letter-spacing: 0.14em; color: var(--color-ink); text-decoration: none; white-space: nowrap; }
  .dot { width: 0.6rem; height: 0.6rem; border-radius: 50%; background: var(--color-accent); box-shadow: 0 0 10px var(--color-accent-glow); }
  nav { display: flex; gap: var(--space-3xs); margin-left: auto; }
  nav a { display: inline-flex; align-items: center; min-height: 2.75rem; padding: 0 var(--space-2xs); font: 600 var(--text-xs)/1 var(--font-display); letter-spacing: 0.14em; text-transform: uppercase; color: var(--color-muted); text-decoration: none; white-space: nowrap; }
  nav a:hover { color: var(--color-ink); }
  .gh, .long { display: none; }
  @media (min-width: 560px) { .gh, .long { display: inline-flex; } }

  .landing { max-width: var(--sheet-w); margin: 0 auto; padding: 0 var(--gutter); }
  .hero { display: grid; gap: var(--space-md); justify-items: start; padding-block: var(--space-2xl) var(--space-xl); }
  .hero h1 { font-size: clamp(2.6rem, 1rem + 6vw, 5.25rem); line-height: 1; max-width: 14ch; }
  .lede { font-size: var(--text-lg); max-width: 40rem; }
  .cta { display: flex; flex-wrap: wrap; gap: var(--space-2xs); }
  .big { min-height: 3.25rem; padding: 0 var(--space-md); }

  .demo { display: grid; grid-template-columns: minmax(0, 1fr); gap: var(--space-md); padding: var(--space-sm); }
  .stage { display: grid; gap: var(--space-2xs); padding: var(--space-sm); background: var(--color-graphite); border: var(--rule-hair); border-radius: var(--radius-control); min-width: 0; }
  .ctrl { display: grid; gap: var(--space-sm); align-content: start; padding: var(--space-2xs) var(--space-2xs) var(--space-sm); }
  .ctrl h2 { font-size: var(--text-2xl); }
  .ctrl > .muted { margin-top: calc(-1 * var(--space-xs)); }
  .read { display: flex; align-items: center; gap: var(--space-sm); padding: var(--space-xs); background: var(--color-paper); border: var(--rule-hair); border-radius: var(--radius-control); }
  .rt { display: grid; gap: var(--space-xs); justify-items: start; min-width: 0; }
  .desc { font: 600 var(--text-lg)/1.3 var(--font-body); color: var(--color-ink); }
  .rt .stamp { font-size: var(--text-base); }
  .field > span { display: flex; justify-content: space-between; align-items: baseline; gap: var(--space-2xs); }
  .v { font-size: var(--text-lg); letter-spacing: 0.02em; text-transform: none; }
  input[type='range'] { width: 100%; min-height: 2.75rem; accent-color: var(--color-accent); cursor: pointer; }
  input[type='range']:focus-visible { outline: 2px solid var(--color-focus); outline-offset: 2px; }
  @media (min-width: 960px) {
    .demo { grid-template-columns: minmax(0, 7fr) minmax(0, 3fr); }
  }

  .tracks { padding-block: var(--space-2xl) var(--space-xl); }
  .tracks h2, .last h2 { font-size: var(--text-3xl); font-weight: 800; }
  .tracks ul { list-style: none; margin: var(--space-md) 0 0; padding: 0; display: grid; grid-template-columns: minmax(0, 1fr); border-top: var(--rule-hair); }
  .tracks li { display: grid; gap: var(--space-3xs); padding: var(--space-sm) 0; border-bottom: var(--rule-hair); }
  .tracks h3 { font-size: var(--text-lg); }
  .tracks p { max-width: 34rem; }
  @media (min-width: 720px) {
    .tracks ul { grid-template-columns: repeat(2, minmax(0, 1fr)); column-gap: var(--space-lg); }
  }

  .self { display: grid; grid-template-columns: minmax(0, 1fr); gap: var(--space-md); padding: var(--space-md); }
  .sc { display: grid; gap: var(--space-sm); align-content: start; }
  .self h2 { font-size: var(--text-2xl); }
  .sc p { max-width: 34rem; }
  code { font: 500 0.95em/1.6 var(--font-code); color: var(--color-ink); }
  .sa { display: flex; flex-wrap: wrap; gap: var(--space-2xs); }
  .code { position: relative; margin: 0; min-width: 0; background: var(--color-paper); border: var(--rule-hair); border-radius: var(--radius-control); }
  pre { margin: 0; padding: 3.5rem var(--space-sm) 4.5rem; overflow-x: auto; }
  pre code { font-size: var(--text-sm); }
  .copy { position: absolute; top: var(--space-2xs); right: var(--space-2xs); background: var(--color-paper-2); }
  .mit { position: absolute; right: var(--space-sm); bottom: calc(-1 * var(--space-sm)); width: 5rem; font-size: var(--text-xs); background: var(--color-paper-2); }
  @media (min-width: 900px) {
    .self { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); align-items: center; padding: var(--space-lg); }
  }

  .last { display: grid; gap: var(--space-sm); justify-items: start; padding-block: var(--space-3xl) var(--space-2xl); }
  .foot { max-width: var(--sheet-w); margin: 0 auto; display: flex; flex-wrap: wrap; justify-content: space-between; gap: var(--space-2xs) var(--space-sm); padding: var(--space-sm) var(--gutter) var(--space-md); border-top: var(--rule-hair); }
  .foot a { color: inherit; }
</style>
