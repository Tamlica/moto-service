<script>
  import { untrack } from 'svelte';
  import { api } from '../lib/api.js';
  import { toast } from '../lib/state.svelte.js';
  import { describe, km, today } from '../lib/format.js';
  import StatusBadge from '../lib/StatusBadge.svelte';

  let { q = {} } = $props();

  let bikes = $state(null);
  let bikeId = $state(null);
  // page remounts on route change, so the initial query is all we need
  const initialTask = untrack(() => q.task);
  let picked = $state(new Set(initialTask ? [Number(initialTask)] : []));
  let day = $state(today());
  let kmValue = $state('');
  let cost = $state('');
  let note = $state('');
  let busy = $state(false);
  let errors = $state({});
  let loadError = $state('');

  api.bikes().then(
    (b) => {
      bikes = b;
      const first = b.find((x) => x.id === Number(q.bike)) ?? b[0];
      if (first) choose(first.id, false);
    },
    (e) => (loadError = e.message),
  );

  let bike = $derived(bikes?.find((b) => b.id === bikeId) ?? null);

  function choose(id, reset = true) {
    bikeId = id;
    const b = bikes.find((x) => x.id === id);
    kmValue = String(b.current_km);
    if (reset) picked = new Set();
  }

  function toggle(id) {
    const next = new Set(picked);
    next.has(id) ? next.delete(id) : next.add(id);
    picked = next;
  }

  async function submit(e) {
    e.preventDefault();
    errors = {};
    const k = Number(kmValue);
    if (!picked.size) errors.tasks = 'Tick at least one service you did.';
    if (kmValue === '' || !Number.isFinite(k) || k < 0) errors.km = 'Enter the odometer reading in km.';
    if (!day) errors.date = 'Pick the date of the service.';
    else if (day > today()) errors.date = "The date can't be in the future.";
    if (cost !== '' && !(Number(cost) >= 0)) errors.cost = 'Cost must be a number, or leave it empty.';
    if (Object.keys(errors).length) return;
    busy = true;
    try {
      await api.addLogs(bike.id, {
        task_ids: [...picked],
        date: day,
        km: k,
        cost: cost === '' ? null : String(cost),
        note,
      });
      toast(`Logged ${picked.size} ${picked.size === 1 ? 'service' : 'services'} on ${bike.name}.`);
      location.hash = `#/bike/${bike.id}`;
    } catch (err) {
      errors.form = err.message;
      busy = false;
    }
  }
</script>

<div class="page">
  <a class="back" href={bike ? `#/bike/${bike.id}` : '#/'}>← Back</a>
  <h1>Log service</h1>
  <p class="lede">Tick what was done, check the km, save. Date and odometer start at today's values.</p>
  {#if loadError}
    <p class="error-text" role="alert">{loadError}</p>
  {:else if bikes === null}
    <p class="label">Loading…</p>
  {:else if !bikes.length}
    <p class="muted">Add a bike first, then you can log services for it.</p>
    <p><a class="btn btn--primary" href="#/bike/new">Add a bike</a></p>
  {:else}
    <form onsubmit={submit} novalidate>
      {#if bikes.length > 1}
        <fieldset class="step-set">
          <legend><span class="step">01</span>Bike</legend>
          <div class="bikes">
            {#each bikes as b (b.id)}
              <label class="pill" class:on={bikeId === b.id}>
                <input class="sr-only" type="radio" name="bike" checked={bikeId === b.id} onchange={() => choose(b.id)} />
                {b.name}
              </label>
            {/each}
          </div>
        </fieldset>
      {/if}

      <fieldset class="step-set" aria-describedby="tasks-err">
        <legend><span class="step">{bikes.length > 1 ? '02' : '01'}</span>What was done? <small class="muted">tick everything from this visit</small></legend>
        <ul class="tasks">
          {#each bike.tasks as t (t.id)}
            <li>
              <label class="task" class:on={picked.has(t.id)}>
                <input type="checkbox" checked={picked.has(t.id)} onchange={() => toggle(t.id)} />
                <span class="tn">{t.name}</span>
                <StatusBadge state={t.state} />
                <small class="muted td">{describe(t)}</small>
              </label>
            </li>
          {/each}
        </ul>
        {#if errors.tasks}<p id="tasks-err" class="error-text" role="alert">{errors.tasks}</p>{/if}
      </fieldset>

      <fieldset class="step-set">
      <legend><span class="step">{bikes.length > 1 ? '03' : '02'}</span>When and where</legend>
      <div class="row">
        <label class="field">
          <span>Date</span>
          <input class="input mono" type="date" max={today()} bind:value={day} aria-invalid={!!errors.date} />
          {#if errors.date}<small class="error-text">{errors.date}</small>{/if}
        </label>
        <label class="field">
          <span>Odometer (km)</span>
          <input class="input mono" type="number" inputmode="numeric" min="0" bind:value={kmValue} aria-invalid={!!errors.km} />
          {#if errors.km}<small class="error-text">{errors.km}</small>
          {:else if Number(kmValue) < bike.current_km}<small>Lower than the last reading ({km(bike.current_km)}). Fine for an older service.</small>{/if}
        </label>
        <label class="field">
          <span>Cost <small class="muted">optional, whole visit</small></span>
          <input class="input mono" type="number" inputmode="decimal" min="0" step="any" bind:value={cost} aria-invalid={!!errors.cost} />
          {#if errors.cost}<small class="error-text">{errors.cost}</small>{/if}
        </label>
      </div>
      <label class="field note">
        <span>Note <small class="muted">optional</small></span>
        <textarea class="input" maxlength="500" bind:value={note} placeholder="Shop, oil brand, part number…"></textarea>
      </label>
      </fieldset>

      {#if errors.form}<p class="error-text" role="alert">{errors.form}</p>{/if}
      <div class="actions">
        <p class="sum"><span class="count">{picked.size}</span> {picked.size === 1 ? 'job' : 'jobs'} on {bike.name}</p>
        <a class="btn btn--ghost" href="#/bike/{bike.id}">Cancel</a>
        <button class="btn btn--primary" data-state={busy ? 'loading' : undefined} disabled={busy}>
          Save {picked.size || ''} {picked.size === 1 ? 'service' : 'services'}
        </button>
      </div>
    </form>
  {/if}
</div>

<style>
  /* Hallmark · genre: atmospheric · design-system: design.md · designed-as-app */
  h1 { margin-top: var(--space-2xs); }
  form { display: grid; gap: var(--space-sm); max-width: 50rem; }
  .bikes { display: flex; flex-wrap: wrap; gap: var(--space-2xs); }
  .pill {
    display: inline-flex; align-items: center; min-height: 3rem; padding: 0 var(--space-sm);
    border: 1px solid var(--color-rule-2); border-radius: var(--radius-control); cursor: pointer; white-space: nowrap;
    font: 700 var(--text-base)/1 var(--font-display); color: var(--color-ink);
    transition: background-color var(--dur-fast) var(--ease-out), border-color var(--dur-fast) var(--ease-out);
  }
  .pill:hover { background: var(--color-paper-3); border-color: var(--color-muted); }
  .pill.on { background: var(--color-accent); border-color: var(--color-accent); color: var(--color-accent-ink); box-shadow: 0 0 16px var(--color-accent-glow); }
  .pill:has(:focus-visible) { outline: 2px solid var(--color-focus); outline-offset: 2px; }
  .tasks { list-style: none; margin: 0; padding: 0; display: grid; gap: var(--space-3xs); }
  .task {
    display: grid;
    grid-template-columns: auto minmax(0, 1fr) auto;
    gap: var(--space-3xs) var(--space-sm);
    align-items: center;
    min-height: 3.5rem;
    padding: var(--space-xs) var(--space-sm);
    background: var(--color-paper);
    border: 1px solid transparent;
    border-radius: var(--radius-control);
    cursor: pointer;
    transition: background-color var(--dur-fast) var(--ease-out), border-color var(--dur-fast) var(--ease-out);
  }
  .task:hover { background: var(--color-paper-3); }
  .task.on { border-color: var(--color-accent); background: var(--color-paper-3); }
  .task:has(:focus-visible) { outline: 2px solid var(--color-focus); outline-offset: 2px; }
  .task input { width: 1.4rem; height: 1.4rem; accent-color: var(--color-accent); margin: 0; }
  .tn { color: var(--color-ink); font-weight: 600; font-size: var(--text-lg); }
  .td { grid-column: 2 / -1; }
  .row { display: grid; gap: var(--space-sm); grid-template-columns: minmax(0, 1fr); }
  @media (min-width: 640px) { .row { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
  /* sticky save bar: saving is always one tap away */
  .actions {
    position: sticky;
    bottom: 0;
    z-index: 5;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--space-2xs);
    padding: var(--space-sm) 0 calc(var(--space-sm) + env(safe-area-inset-bottom));
    background: color-mix(in srgb, var(--color-paper) 92%, transparent);
    backdrop-filter: blur(8px);
    border-top: var(--rule-hair);
  }
  .sum { margin-right: auto; font-weight: 600; color: var(--color-ink); }
  .count { font: 800 var(--text-2xl)/1 var(--font-display); color: var(--color-accent); text-shadow: 0 0 14px var(--color-accent-glow); font-variant-numeric: tabular-nums; }
</style>
