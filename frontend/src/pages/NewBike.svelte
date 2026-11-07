<script>
  import { api } from '../lib/api.js';
  import { toast } from '../lib/state.svelte.js';
  import { BIKE_TYPES } from '../bikes/index.js';
  import Schematic from '../lib/Schematic.svelte';

  let name = $state('');
  let plate = $state('');
  let type = $state('scooter');
  let kmValue = $state('');
  let busy = $state(false);
  let errors = $state({});

  async function submit(e) {
    e.preventDefault();
    errors = {};
    if (!name.trim()) errors.name = 'Give the bike a name, e.g. "Vario 125".';
    const k = Number(kmValue);
    if (kmValue === '' || !Number.isFinite(k) || k < 0) errors.km = 'Enter the current odometer reading in km.';
    if (Object.keys(errors).length) return;
    busy = true;
    try {
      const bike = await api.createBike({ name: name.trim(), plate: plate.trim(), type, km: k });
      toast(`${bike.name} added with ${bike.tasks.length} service items.`);
      location.hash = `#/bike/${bike.id}`;
    } catch (err) {
      errors.form = err.message;
      busy = false;
    }
  }
</script>

<div class="page">
  <a class="back" href="#/">← Garage</a>
  <h1>Add a bike</h1>
  <p class="lede">Pick the type, name it, enter the km. Common service intervals are filled in for you.</p>
  <form onsubmit={submit} novalidate>
    <fieldset class="step-set types">
      <legend><span class="step">01</span>Type <small class="muted">sets the drawing and default service items</small></legend>
      <div class="grid">
        {#each BIKE_TYPES as t (t.id)}
          <label class="type" class:on={type === t.id}>
            <input class="sr-only" type="radio" name="type" value={t.id} bind:group={type} />
            <span class="sil"><Schematic type={t.id} mini title="{t.label} silhouette" /></span>
            <span class="tl">{t.label}</span>
            <small class="muted">{t.hint}</small>
          </label>
        {/each}
      </div>
    </fieldset>

    <fieldset class="step-set">
    <legend><span class="step">02</span>Name and odometer</legend>
    <div class="row">
      <label class="field">
        <span>Name</span>
        <input class="input" bind:value={name} maxlength="80" placeholder="Vario 125" aria-invalid={!!errors.name} aria-describedby="name-err" />
        {#if errors.name}<small id="name-err" class="error-text">{errors.name}</small>{/if}
      </label>
      <label class="field">
        <span>Current odometer (km)</span>
        <input class="input mono" type="number" inputmode="numeric" min="0" bind:value={kmValue} aria-invalid={!!errors.km} aria-describedby="km-err" />
        {#if errors.km}<small id="km-err" class="error-text">{errors.km}</small>{/if}
      </label>
      <label class="field">
        <span>Plate <small class="muted">optional</small></span>
        <input class="input mono" bind:value={plate} maxlength="20" placeholder="B 1234 XYZ" />
      </label>
    </div>
    </fieldset>

    {#if errors.form}<p class="error-text" role="alert">{errors.form}</p>{/if}
    <div class="actions">
      <button class="btn btn--primary" data-state={busy ? 'loading' : undefined} disabled={busy}>Add bike <span class="arrow" aria-hidden="true">→</span></button>
      <a class="btn btn--ghost" href="#/">Cancel</a>
    </div>
  </form>
</div>

<style>
  /* Hallmark · genre: atmospheric · design-system: design.md · designed-as-app */
  h1 { margin-top: var(--space-2xs); }
  form { display: grid; gap: var(--space-sm); }
  .grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-2xs); }
  @media (min-width: 900px) { .grid { grid-template-columns: repeat(4, minmax(0, 1fr)); } }
  .type {
    display: grid;
    gap: var(--space-3xs);
    align-content: start;
    padding: var(--space-sm) var(--space-xs);
    background: var(--color-graphite);
    border: 1px solid var(--color-rule);
    border-radius: var(--radius-control);
    cursor: pointer;
    transition: background-color var(--dur-fast) var(--ease-out), border-color var(--dur-fast) var(--ease-out);
    min-width: 0;
  }
  .type:hover { border-color: var(--color-rule-2); background: var(--color-graphite-2); }
  .type.on { border-color: var(--color-accent); box-shadow: 0 0 0 1px var(--color-accent), 0 0 20px var(--color-accent-glow); }
  .type:has(:focus-visible) { outline: 2px solid var(--color-focus); outline-offset: 2px; }
  .sil { display: block; margin-bottom: var(--space-2xs); }
  .tl { font: 700 var(--text-lg)/1.1 var(--font-display); color: var(--color-ink); }
  .type.on .tl { color: var(--color-accent); }
  .type small { font-size: var(--text-xs); line-height: 1.35; }
  .row { display: grid; gap: var(--space-sm); grid-template-columns: minmax(0, 1fr); }
  @media (min-width: 640px) { .row { grid-template-columns: minmax(0, 2fr) minmax(0, 1.4fr) minmax(0, 1fr); } }
  .actions { display: flex; flex-wrap: wrap; gap: var(--space-2xs); padding-top: var(--space-xs); }
</style>
