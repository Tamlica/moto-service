<script>
  import { api } from '../lib/api.js';
  import { toast } from '../lib/state.svelte.js';
  import { dateShort, describe, km, num, today, RANK } from '../lib/format.js';
  import Schematic from '../lib/Schematic.svelte';
  import StatusBadge from '../lib/StatusBadge.svelte';
  import Gauge from '../lib/Gauge.svelte';

  let bikes = $state(null);
  let error = $state('');
  let kmInput = $state({});
  let kmBusy = $state({});
  let kmError = $state({});
  let doneState = $state(undefined);
  let justDone = $state(null); // { key, name } — drives the DONE stamp

  api.bikes().then((b) => (bikes = b), (e) => (error = e.message));

  const replace = (view) => (bikes = bikes.map((b) => (b.id === view.id ? view : b)));

  let sorted = $derived(bikes ? [...bikes].sort((a, b) => RANK[a.worst] - RANK[b.worst]) : []);

  let counts = $derived.by(() => {
    const c = { overdue: 0, soon: 0, due: 0 };
    for (const b of bikes ?? []) for (const t of b.tasks) if (t.state in c) c[t.state]++;
    return c;
  });

  // the single most urgent job across every bike
  let next = $derived.by(() => {
    let best = null;
    for (const bike of bikes ?? [])
      for (const t of bike.tasks) {
        if (t.state !== 'overdue' && t.state !== 'soon') continue;
        const score = RANK[t.state] * 1e9 + (t.km_left ?? (t.days_left ?? 0) * 30);
        if (!best || score < best.score) best = { bike, t, score };
      }
    return best;
  });

  async function markNext() {
    const { bike, t } = next;
    doneState = 'loading';
    try {
      const view = await api.addLogs(bike.id, { task_ids: [t.id], date: today(), km: bike.current_km });
      const ids = view.created_log_ids;
      justDone = { key: Date.now(), name: t.name };
      setTimeout(() => (justDone = null), 1800);
      replace(view);
      doneState = undefined;
      toast(`${t.name} stamped on ${bike.name} at ${km(bike.current_km)}.`, {
        label: 'Undo',
        run: async () => {
          for (const id of ids) await api.deleteLog(bike.id, id);
          replace(await api.bike(bike.id));
        },
      });
    } catch (err) {
      doneState = 'error';
      toast(err.message);
    }
  }

  async function updateKm(e, bike) {
    e.preventDefault();
    const value = Number(kmInput[bike.id]);
    kmError[bike.id] = '';
    if (!Number.isFinite(value) || value <= 0) return (kmError[bike.id] = 'Enter the odometer reading in km.');
    if (value < bike.current_km) return (kmError[bike.id] = `That's lower than the last reading (${km(bike.current_km)}).`);
    kmBusy[bike.id] = true;
    try {
      replace(await api.addKm(bike.id, { km: value, date: today() }));
      kmInput[bike.id] = '';
    } catch (err) {
      kmError[bike.id] = err.message;
    } finally {
      kmBusy[bike.id] = false;
    }
  }
</script>

<div class="page">
  <header class="head">
    <h1>Garage</h1>
    {#if bikes?.length}
      <dl class="cells" aria-label="Service summary">
        <div class:hot={counts.overdue}><dt class="label">Overdue</dt><dd>{counts.overdue}</dd></div>
        <div class:warm={counts.soon}><dt class="label">Due soon</dt><dd>{counts.soon}</dd></div>
        <div><dt class="label">Never logged</dt><dd>{counts.due}</dd></div>
        <div><dt class="label">Bikes</dt><dd>{bikes.length}</dd></div>
      </dl>
    {/if}
  </header>

  {#if error}
    <p class="error-text" role="alert">{error}</p>
  {:else if bikes === null}
    <p class="label">Loading bikes…</p>
  {:else if bikes.length === 0}
    <section class="empty panel-box">
      <h2>Add your first bike</h2>
      <ol class="steps">
        <li><span class="label">1</span>Pick the type: scooter, underbone, sport or trail.</li>
        <li><span class="label">2</span>Give it a name and enter the odometer.</li>
        <li><span class="label">3</span>Common service intervals are filled in. Edit them any time.</li>
      </ol>
      <a class="btn btn--primary" href="#/bike/new">Add a bike <span class="arrow" aria-hidden="true">→</span></a>
    </section>
  {:else}
    <section class="next panel-box" class:clear={!next} aria-labelledby="next-h">
      <p class="label">Next job</p>
      {#if next}
        <h2 id="next-h">{next.t.name}</h2>
        <p class="nmeta">
          on <a href="#/bike/{next.bike.id}">{next.bike.name}</a>
          <span class="sep" aria-hidden="true">·</span>
          <span class="mono">{describe(next.t)}</span>
        </p>
        <div class="nact">
          <button class="btn btn--primary" onclick={markNext} disabled={doneState === 'loading'} data-state={doneState}>
            Done today at {km(next.bike.current_km)}
          </button>
          <a class="btn" href="#/log?bike={next.bike.id}&task={next.t.id}">Log with cost or notes</a>
        </div>
        {#key next.t.id}
          <span class="nstamp stamp {next.t.state === 'overdue' ? 'stamp--red' : 'stamp--soon'}" aria-hidden="true">
            {next.t.state === 'overdue' ? 'Overdue' : 'Due soon'}
          </span>
        {/key}
      {:else}
        <h2 id="next-h">Nothing due</h2>
        <p class="muted">Every bike is inside its intervals. Update the km after a ride to keep this accurate.</p>
      {/if}
      {#if justDone}
        {#key justDone.key}
          <span class="donestamp stamp stamp--round thunk" role="status">Done<small>{dateShort(today())}</small></span>
        {/key}
      {/if}
    </section>

    <section class="bikes" aria-label="Bikes">
      {#each sorted as bike (bike.id)}
        <article class="bike panel-box s-{bike.worst}">
          <header class="bh">
            <h3><a href="#/bike/{bike.id}">{bike.name}</a></h3>
            <StatusBadge state={bike.worst} />
            {#if bike.plate}<span class="plate">{bike.plate}</span>{/if}
          </header>
          <div class="dash">
            <a class="thumb" href="#/bike/{bike.id}" aria-label="Open {bike.name} diagram">
              <Schematic type={bike.type} tasks={bike.tasks} mini title="{bike.name} schematic" />
            </a>
            <p class="odo">
              <span class="label">ODO</span>
              <span class="n lcd">{num(bike.current_km)}<small>KM</small></span>
              {#if bike.avg_km_day}<span class="muted sub">≈ {bike.avg_km_day} km / day</span>{/if}
            </p>
          </div>
          <ul class="jobs" aria-label="Next services for {bike.name}">
            {#each bike.tasks.slice(0, 3) as t (t.id)}
              <li>
                <Gauge task={t} size={46} />
                <span class="jt"><span class="jn">{t.name}</span><span class="jd mono">{describe(t)}</span></span>
              </li>
            {/each}
          </ul>
          <form class="km" onsubmit={(e) => updateKm(e, bike)}>
            <label class="sr-only" for="km-{bike.id}">Odometer for {bike.name}</label>
            <input
              id="km-{bike.id}"
              class="input"
              type="number"
              inputmode="numeric"
              min="0"
              placeholder="New km, e.g. {bike.current_km + 120}"
              bind:value={kmInput[bike.id]}
              aria-invalid={!!kmError[bike.id]}
              aria-describedby="km-err-{bike.id}"
            />
            <button class="btn" data-state={kmBusy[bike.id] ? 'loading' : undefined} disabled={kmBusy[bike.id]}>Update km</button>
            <p id="km-err-{bike.id}" class="error-text" role={kmError[bike.id] ? 'alert' : undefined}>{kmError[bike.id] ?? ''}</p>
          </form>
          <footer class="bf">
            <a class="link" href="#/bike/{bike.id}">Open dash <span aria-hidden="true">→</span></a>
            <a class="link" href="#/log?bike={bike.id}">Log a service <span aria-hidden="true">→</span></a>
          </footer>
        </article>
      {/each}
      <a class="add" href="#/bike/new"><span class="plus" aria-hidden="true">+</span>Add a bike</a>
    </section>
  {/if}
</div>

<style>
  /* Hallmark · genre: atmospheric · macrostructure: Index-First · design-system: design.md · designed-as-app */
  .head { display: grid; gap: var(--space-md); padding-block: var(--space-sm) var(--space-lg); }
  .cells { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-2xs); margin: 0; }
  .cells div { padding: var(--space-xs) var(--space-sm); background: var(--color-paper-2); border: var(--rule-hair); border-radius: var(--radius-control); }
  .cells dd { margin: var(--space-3xs) 0 0; font: 800 var(--text-3xl)/1 var(--font-display); color: var(--color-ink); font-variant-numeric: tabular-nums; }
  .cells .hot { border-color: color-mix(in srgb, var(--color-overdue) 55%, var(--color-rule)); }
  .cells .hot dd { color: var(--color-overdue-ink); text-shadow: 0 0 16px color-mix(in srgb, var(--color-overdue) 40%, transparent); }
  .cells .warm dd { color: var(--color-soon); }
  @media (min-width: 720px) { .cells { grid-template-columns: repeat(4, minmax(0, 1fr)); } }

  /* next job */
  .next { position: relative; display: grid; gap: var(--space-xs); padding: var(--space-md) var(--space-md) var(--space-lg); margin-bottom: var(--space-lg); overflow: hidden; }
  .next h2 { font-size: clamp(2rem, 1.2rem + 3.4vw, 3.25rem); font-weight: 800; padding-right: 7rem; }
  .nmeta { display: flex; flex-wrap: wrap; align-items: baseline; gap: var(--space-3xs) var(--space-2xs); font-size: var(--text-lg); }
  .nmeta a { font-weight: 600; }
  .sep { color: var(--color-muted); }
  .nact { display: flex; flex-wrap: wrap; gap: var(--space-2xs); padding-top: var(--space-2xs); }
  .nstamp { position: absolute; top: var(--space-md); right: var(--space-md); font-size: var(--text-base); }
  .donestamp { position: absolute; right: var(--space-lg); bottom: var(--space-lg); font-size: var(--text-lg); }
  .clear h2 { color: var(--color-ok); }

  /* bike cards */
  .bikes { display: grid; grid-template-columns: minmax(0, 1fr); gap: var(--space-sm); }
  @media (min-width: 900px) { .bikes { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
  .bike { display: grid; gap: var(--space-sm); padding: var(--space-sm) var(--space-sm) var(--space-xs); align-content: start; }
  .bike.s-overdue { border-color: color-mix(in srgb, var(--color-overdue) 40%, var(--color-rule)); }
  .bh { display: flex; flex-wrap: wrap; align-items: center; gap: var(--space-2xs) var(--space-xs); }
  .bh h3 { font-size: var(--text-2xl); font-weight: 800; margin-right: auto; }
  .bh h3 a { text-decoration: none; }
  .bh h3 a:hover { color: var(--color-accent); }
  .plate { font: 700 var(--text-sm)/1 var(--font-mono); letter-spacing: 0.1em; padding: 0.3em 0.5em; border: 1px solid var(--color-rule-2); border-radius: 4px; color: var(--color-ink-2); }
  .dash { display: grid; grid-template-columns: minmax(0, 1fr); gap: var(--space-xs); align-items: end; }
  .thumb { display: block; padding: var(--space-xs) var(--space-sm) var(--space-2xs); background: var(--color-graphite); border-radius: var(--radius-control); border: var(--rule-hair); }
  .odo { display: grid; gap: var(--space-3xs); }
  .odo .n { font-size: clamp(2.5rem, 1.5rem + 3vw, 3.25rem); line-height: 1; }
  .odo .n small { font: 600 var(--text-sm)/1 var(--font-display); color: var(--color-muted); text-shadow: none; margin-left: var(--space-2xs); letter-spacing: 0.14em; }
  .sub { font-size: var(--text-sm); }
  @media (min-width: 520px) { .dash { grid-template-columns: minmax(0, 3fr) minmax(0, 2fr); } }
  .jobs { list-style: none; margin: 0; padding: 0; display: grid; gap: var(--space-2xs); }
  .jobs li { display: flex; align-items: center; gap: var(--space-xs); padding: var(--space-3xs) var(--space-2xs); background: var(--color-paper); border-radius: var(--radius-control); }
  .jt { display: grid; min-width: 0; }
  .jn { color: var(--color-ink); font-weight: 600; }
  .jd { font-size: var(--text-sm); color: var(--color-muted); }
  .km { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: var(--space-2xs); }
  .km .error-text { grid-column: 1 / -1; }
  .km .error-text:empty { display: none; }
  .bf { display: flex; flex-wrap: wrap; justify-content: space-between; gap: var(--space-2xs); border-top: var(--rule-hair); padding-top: var(--space-3xs); }
  .link { display: inline-flex; align-items: center; gap: var(--space-2xs); min-height: 2.75rem; font: 600 var(--text-xs)/1 var(--font-display); letter-spacing: 0.14em; text-transform: uppercase; text-decoration: none; color: var(--color-ink-2); }
  .link:hover { color: var(--color-accent); }
  .link span { transition: transform var(--dur-fast) var(--ease-out); }
  .link:hover span { transform: translateX(3px); }

  .add {
    display: flex; align-items: center; justify-content: center; gap: var(--space-xs);
    min-height: 8rem;
    border: 1.5px dashed var(--color-rule-2);
    border-radius: var(--radius-panel);
    font: 700 var(--text-lg)/1 var(--font-display);
    letter-spacing: 0.06em;
    color: var(--color-ink-2);
    text-decoration: none;
    transition: border-color var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out);
  }
  .add:hover { border-color: var(--color-accent); color: var(--color-accent); }
  .plus { display: inline-grid; place-items: center; width: 2rem; height: 2rem; border-radius: 50%; background: var(--color-accent); color: var(--color-accent-ink); font-size: var(--text-xl); line-height: 1; }

  .empty { display: grid; gap: var(--space-md); justify-items: start; padding: var(--space-lg); max-width: 40rem; }
  .steps { list-style: none; margin: 0; padding: 0; display: grid; gap: var(--space-2xs); width: 100%; }
  .steps li { display: grid; grid-template-columns: 2rem minmax(0, 1fr); align-items: baseline; color: var(--color-ink); font-size: var(--text-lg); }
  .steps .label { color: var(--color-accent); }
</style>
