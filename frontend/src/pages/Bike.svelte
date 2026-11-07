<script>
  import { untrack } from 'svelte';
  import { api } from '../lib/api.js';
  import { date, dateShort, describe, interval, km, money, num, today } from '../lib/format.js';
  import { BIKES, BIKE_TYPES } from '../bikes/index.js';
  import Schematic from '../lib/Schematic.svelte';
  import PartPanel from '../lib/PartPanel.svelte';
  import Gauge from '../lib/Gauge.svelte';

  let { id } = $props();
  let bike = $state(null);
  let error = $state('');
  let exploded = $state(false);
  let sel = $state(null); // { part, taskId }
  let kmValue = $state('');
  let kmBusy = $state(false);
  let kmError = $state('');

  api.bike(untrack(() => id)).then((b) => (bike = b), (e) => (error = e.message));

  const GROUPS = [
    ['overdue', 'Overdue'],
    ['soon', 'Due soon'],
    ['due', 'Never logged'],
    ['ok', 'OK'],
  ];

  let groups = $derived(bike ? GROUPS.map(([s, title]) => ({ s, title, tasks: bike.tasks.filter((t) => t.state === s) })).filter((g) => g.tasks.length) : []);
  let count = (s) => bike.tasks.filter((t) => t.state === s).length;
  let selTask = $derived(sel && bike ? (bike.tasks.find((t) => t.id === sel.taskId) ?? null) : null);
  let totalCost = $derived(bike ? bike.logs.reduce((s, l) => s + (l.cost == null ? 0 : Number(l.cost)), 0) : 0);
  let diagramParts = $derived(bike ? new Set(BIKES[bike.type].parts.map((p) => p.id)) : new Set());
  let typeLabel = $derived(BIKE_TYPES.find((t) => t.id === bike?.type)?.label ?? '');

  // one workshop visit = same date + same odometer reading
  let visits = $derived.by(() => {
    if (!bike) return [];
    const out = [];
    for (const l of bike.logs) {
      const last = out.at(-1);
      if (last && last.date === l.date && last.km === l.km) last.logs.push(l);
      else out.push({ key: `${l.date}-${l.km}-${l.id}`, date: l.date, km: l.km, logs: [l] });
    }
    for (const v of out) {
      v.cost = v.logs.reduce((s, l) => s + (l.cost == null ? 0 : Number(l.cost)), 0);
      v.notes = [...new Set(v.logs.map((l) => l.note).filter(Boolean))];
    }
    return out;
  });

  function selectPart(part) {
    const task = bike.tasks.find((t) => t.part === part);
    sel = { part, taskId: task?.id ?? null };
  }

  async function updateKm(e) {
    e.preventDefault();
    const value = Number(kmValue);
    kmError = '';
    if (!Number.isFinite(value) || value <= 0) return (kmError = 'Enter the odometer reading in km.');
    if (value < bike.current_km) return (kmError = `That's lower than the last reading (${km(bike.current_km)}).`);
    kmBusy = true;
    try {
      await api.addKm(bike.id, { km: value, date: today() });
      bike = await api.bike(bike.id);
      kmValue = '';
    } catch (err) {
      kmError = err.message;
    } finally {
      kmBusy = false;
    }
  }
</script>

<div class="page">
  <a class="back" href="#/">← Garage</a>
  {#if error}
    <p class="error-text" role="alert">{error}</p>
  {:else if !bike}
    <p class="label">Loading…</p>
  {:else}
    <header class="head">
      <h1>{bike.name}</h1>
      <p class="meta">
        <span class="label">{typeLabel}</span>
        {#if bike.plate}<span class="plate">{bike.plate}</span>{/if}
      </p>
    </header>

    <!-- the cluster: odometer readout, warning lamps, quick actions -->
    <section class="cluster panel-box" aria-label="Odometer">
      <div class="odo">
        <p class="label">ODO</p>
        <p class="n lcd">{num(bike.current_km)}<small>KM</small></p>
        {#if bike.avg_km_day}<p class="muted">≈ {bike.avg_km_day} km / day</p>{/if}
      </div>
      <dl class="lamps">
        <div class="l-overdue" class:on={count('overdue')}><dt class="label">Overdue</dt><dd>{count('overdue')}</dd></div>
        <div class="l-soon" class:on={count('soon')}><dt class="label">Due soon</dt><dd>{count('soon')}</dd></div>
        <div class="l-due" class:on={count('due')}><dt class="label">Not logged</dt><dd>{count('due')}</dd></div>
        <div class="l-ok" class:on={count('ok')}><dt class="label">OK</dt><dd>{count('ok')}</dd></div>
      </dl>
      <div class="side">
        <form class="km" onsubmit={updateKm}>
          <label class="field">
            <span>Update odometer</span>
            <input class="input" type="number" inputmode="numeric" min="0" placeholder="e.g. {bike.current_km + 120}" bind:value={kmValue} aria-invalid={!!kmError} />
          </label>
          <button class="btn" data-state={kmBusy ? 'loading' : undefined} disabled={kmBusy}>Save km</button>
          {#if kmError}<p class="error-text" role="alert">{kmError}</p>{/if}
        </form>
        <div class="links">
          <a class="btn btn--primary" href="#/log?bike={bike.id}">Log a service <span class="arrow" aria-hidden="true">→</span></a>
          <a class="btn btn--ghost" href="#/settings?bike={bike.id}">Edit intervals</a>
        </div>
      </div>
    </section>

    <section class="stage" aria-label="Schematic">
      <div class="toolbar">
        <p class="label">{typeLabel} · side view · tap a part</p>
        <button class="toggle" aria-pressed={exploded} onclick={() => (exploded = !exploded)}>
          <span class="knob" aria-hidden="true"></span>Exploded view
        </button>
      </div>
      <Schematic
        type={bike.type}
        tasks={bike.tasks}
        {exploded}
        selected={sel?.part}
        onselect={selectPart}
        title="{bike.name} schematic. Tap a part for details."
      />
      <ul class="legend" aria-label="Legend">
        <li class="ok">● OK</li>
        <li class="soon">▲ Due soon</li>
        <li class="overdue">■ Overdue</li>
        <li class="due">◆ Not logged</li>
        <li class="none">○ Not tracked</li>
      </ul>
    </section>

    <section class="parts" aria-labelledby="parts-h">
      <h2 id="parts-h">Service items</h2>
      {#each groups as g (g.s)}
        <div class="group s-{g.s}">
          <h3 class="gh label"><span class="gn">{g.tasks.length}</span>{g.title}</h3>
          <ul class="tiles">
            {#each g.tasks as t (t.id)}
              <li>
                <button class="tile" onclick={() => (sel = { part: t.part, taskId: t.id })}>
                  <Gauge task={t} size={58} />
                  <span class="tt">
                    <span class="tn">{t.name}</span>
                    <span class="td">{describe(t)}</span>
                    <span class="ti">{interval(t)}{#if !diagramParts.has(t.part)} · not on diagram{/if}</span>
                  </span>
                </button>
              </li>
            {/each}
          </ul>
        </div>
      {/each}
    </section>

    <section class="history" aria-labelledby="hist-h">
      <div class="hhead">
        <h2 id="hist-h">Service book</h2>
        {#if totalCost > 0}<p class="label">Total spent <span class="spent">{money(totalCost)}</span></p>{/if}
      </div>
      {#if visits.length}
        <ol class="visits">
          {#each visits as v, i (v.key)}
            <li class="visit">
              <p class="vwhen"><span class="vd">{date(v.date)}</span><span class="vk">{km(v.km)}</span></p>
              <ul class="vjobs">{#each v.logs as l (l.id)}<li>{l.task}</li>{/each}</ul>
              {#each v.notes as n (n)}<p class="note">{n}</p>{/each}
              {#if v.cost > 0}<p class="vcost">{money(v.cost)}</p>{/if}
              <span class="vstamp stamp stamp--round" style="--tilt: {i % 2 ? 9 : -11}deg" aria-hidden="true">Done<small>{dateShort(v.date)}</small></span>
            </li>
          {/each}
        </ol>
      {:else}
        <p class="muted">No services logged yet. Tap a part on the drawing and choose “Mark done”, or use Log a service.</p>
      {/if}
      <details class="odo-log">
        <summary>Odometer readings ({bike.odometer.length})</summary>
        <ol>
          {#each bike.odometer as o (o.id)}<li class="mono"><span>{date(o.date)}</span><span>{km(o.km)}</span></li>{/each}
        </ol>
      </details>
    </section>

    {#if sel}
      <PartPanel {bike} part={sel.part} task={selTask} onclose={() => (sel = null)} onchange={(b) => (bike = b)} />
    {/if}
  {/if}
</div>

<style>
  /* Hallmark · genre: atmospheric · macrostructure: Stat-Led · design-system: design.md · designed-as-app */
  .head { display: grid; gap: var(--space-2xs); padding-block: var(--space-2xs) var(--space-md); }
  .meta { display: flex; flex-wrap: wrap; align-items: center; gap: var(--space-xs); }
  .plate { font: 700 var(--text-sm)/1 var(--font-mono); letter-spacing: 0.1em; padding: 0.3em 0.5em; border: 1px solid var(--color-rule-2); border-radius: 4px; color: var(--color-ink-2); }

  /* the cluster */
  .cluster { display: grid; grid-template-columns: minmax(0, 1fr); gap: var(--space-md); padding: var(--space-md); }
  .odo { display: grid; gap: var(--space-3xs); min-width: 0; }
  .odo .n { font-size: var(--text-numeral); line-height: 0.9; overflow-wrap: anywhere; }
  .odo .n small { font: 600 var(--text-lg)/1 var(--font-display); color: var(--color-muted); text-shadow: none; margin-left: var(--space-2xs); letter-spacing: 0.14em; }
  .lamps { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-2xs); margin: 0; }
  .lamps div { --lamp: var(--color-muted); padding: var(--space-xs); background: var(--color-paper); border: var(--rule-hair); border-radius: var(--radius-control); }
  .lamps dd { margin: var(--space-3xs) 0 0; font: 800 var(--text-3xl)/1 var(--font-display); color: var(--color-line-dim); font-variant-numeric: tabular-nums; }
  .lamps .l-overdue { --lamp: var(--color-overdue-ink); }
  .lamps .l-soon { --lamp: var(--color-soon); }
  .lamps .l-due { --lamp: var(--color-due); }
  .lamps .l-ok { --lamp: var(--color-ok); }
  .lamps .on { border-color: color-mix(in srgb, var(--lamp) 45%, var(--color-rule)); }
  .lamps .on dd { color: var(--lamp); text-shadow: 0 0 14px color-mix(in srgb, var(--lamp) 45%, transparent); }
  .side { display: grid; gap: var(--space-sm); align-content: end; }
  .km { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: var(--space-2xs); align-items: end; }
  .km .error-text { grid-column: 1 / -1; }
  .links { display: flex; flex-wrap: wrap; gap: var(--space-2xs); }
  @media (min-width: 900px) {
    .cluster { grid-template-columns: minmax(0, 6fr) minmax(0, 5fr); column-gap: var(--space-lg); }
    .lamps { grid-template-columns: repeat(4, minmax(0, 1fr)); grid-column: 1; }
    .side { grid-column: 2; grid-row: 1 / span 2; }
  }

  /* schematic stage */
  .stage { display: grid; gap: var(--space-sm); margin-top: var(--space-md); padding: var(--space-sm) var(--space-sm) var(--space-md); background: var(--color-graphite); border: var(--rule-hair); border-radius: var(--radius-panel); }
  .toolbar { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: var(--space-2xs); }
  .toggle {
    display: inline-flex; align-items: center; gap: var(--space-2xs);
    min-height: 2.75rem; padding: 0 var(--space-xs);
    background: transparent; color: var(--color-on-dark);
    border: 1px solid var(--color-graphite-rule); border-radius: var(--radius-control);
    font: 700 var(--text-xs)/1 var(--font-display); letter-spacing: 0.14em; text-transform: uppercase;
    cursor: pointer; white-space: nowrap;
    transition: border-color var(--dur-fast) var(--ease-out);
  }
  .toggle:hover { border-color: var(--color-on-dark-2); }
  .knob { width: 2rem; height: 1.1rem; border-radius: 999px; background: var(--color-graphite-rule); position: relative; transition: background-color var(--dur-base) var(--ease-out); }
  .knob::after { content: ''; position: absolute; top: 0.15rem; left: 0.15rem; width: 0.8rem; height: 0.8rem; border-radius: 50%; background: var(--color-on-dark); transition: transform var(--dur-base) var(--ease-out); }
  .toggle[aria-pressed='true'] .knob { background: var(--color-accent); box-shadow: 0 0 10px var(--color-accent-glow); }
  .toggle[aria-pressed='true'] .knob::after { transform: translateX(0.9rem); background: var(--color-accent-ink); }
  .legend { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: var(--space-2xs) var(--space-sm); font: 600 var(--text-xs)/1.3 var(--font-display); letter-spacing: 0.12em; text-transform: uppercase; color: var(--color-on-dark-2); }
  .legend .ok::first-letter { color: var(--color-ok); }
  .legend .soon::first-letter { color: var(--color-soon); }
  .legend .overdue::first-letter { color: var(--color-overdue); }
  .legend .due::first-letter { color: var(--color-due); }
  .legend .none::first-letter { color: var(--color-line-dim); }

  /* gauge tiles, grouped by state */
  .parts { display: grid; gap: var(--space-lg); padding-top: var(--space-xl); }
  .gh { display: flex; align-items: center; gap: var(--space-2xs); margin-bottom: var(--space-xs); }
  .gn { display: inline-grid; place-items: center; min-width: 1.6rem; height: 1.6rem; padding: 0 0.3em; border-radius: 6px; background: var(--color-paper-3); color: var(--color-ink); font-size: var(--text-sm); }
  .s-overdue .gn { background: var(--color-overdue); color: var(--color-accent-ink); }
  .s-soon .gn { background: var(--color-soon); color: var(--color-accent-ink); }
  .tiles { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: minmax(0, 1fr); gap: var(--space-2xs); }
  @media (min-width: 640px) { .tiles { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
  @media (min-width: 1040px) { .tiles { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
  .tile {
    display: flex; align-items: center; gap: var(--space-sm);
    width: 100%; height: 100%;
    padding: var(--space-xs) var(--space-sm) var(--space-xs) var(--space-xs);
    background: var(--color-paper-2); border: var(--rule-hair); border-radius: var(--radius-panel);
    text-align: left; font: inherit; color: inherit; cursor: pointer;
    transition: background-color var(--dur-fast) var(--ease-out), border-color var(--dur-fast) var(--ease-out), transform var(--dur-fast) var(--ease-out);
  }
  .tile:hover { background: var(--color-paper-3); border-color: var(--color-rule-2); }
  .tile:active { transform: translateY(1px); }
  .s-overdue .tile { border-color: color-mix(in srgb, var(--color-overdue) 40%, var(--color-rule)); }
  .tt { display: grid; gap: 0.1rem; min-width: 0; }
  .tn { color: var(--color-ink); font-weight: 600; font-size: var(--text-lg); line-height: 1.2; }
  .td { color: var(--color-ink-2); font-variant-numeric: tabular-nums; }
  .ti { color: var(--color-muted); font-size: var(--text-sm); }

  /* service book: stamped visits */
  .history { padding-top: var(--space-2xl); }
  .hhead { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: baseline; gap: var(--space-2xs); padding-bottom: var(--space-sm); }
  .spent { font: 800 var(--text-xl)/1 var(--font-display); color: var(--color-accent); margin-left: var(--space-2xs); letter-spacing: 0; }
  .visits { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: minmax(0, 1fr); gap: var(--space-sm); }
  @media (min-width: 720px) { .visits { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
  .visit { position: relative; display: grid; gap: var(--space-2xs); align-content: start; min-height: 8.5rem; padding: var(--space-sm) 6.5rem var(--space-sm) var(--space-sm); background: var(--color-paper-2); border: 1px dashed var(--color-rule-2); border-radius: var(--radius-control); }
  .vwhen { display: flex; flex-wrap: wrap; gap: 0 var(--space-sm); align-items: baseline; }
  .vd { font: 700 var(--text-lg)/1.2 var(--font-display); color: var(--color-ink); }
  .vk { font: 700 var(--text-sm)/1 var(--font-mono); letter-spacing: 0.08em; color: var(--color-muted); font-variant-numeric: tabular-nums; }
  .vjobs { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: var(--space-3xs) var(--space-2xs); }
  .vjobs li { padding: 0.15em 0.5em; border-radius: 4px; background: var(--color-paper-3); color: var(--color-ink); font-size: var(--text-sm); font-weight: 500; }
  .note { font-size: var(--text-sm); color: var(--color-ink-2); }
  .vcost { font: 700 var(--text-base)/1 var(--font-display); color: var(--color-ink); font-variant-numeric: tabular-nums; }
  .vstamp { position: absolute; top: 50%; right: var(--space-sm); translate: 0 -50%; font-size: var(--text-xs); width: 5rem; }
  .odo-log { margin-top: var(--space-md); font-size: var(--text-sm); }
  .odo-log summary { cursor: pointer; min-height: 2.75rem; display: flex; align-items: center; font: 600 var(--text-xs)/1 var(--font-display); letter-spacing: 0.14em; text-transform: uppercase; color: var(--color-ink-2); }
  .odo-log summary:hover { color: var(--color-accent); }
  .odo-log ol { list-style: none; padding: 0; margin: 0; max-width: 24rem; }
  .odo-log li { display: flex; justify-content: space-between; padding: var(--space-3xs) 0; border-bottom: var(--rule-hair); }
</style>
