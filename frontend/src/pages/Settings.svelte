<script>
  import { api } from '../lib/api.js';
  import { toast, ui } from '../lib/state.svelte.js';
  import { PARTS, PART_IDS } from '../lib/parts.js';
  import { BIKE_TYPES } from '../bikes/index.js';
  import { today } from '../lib/format.js';

  let { q = {} } = $props();

  let bikes = $state(null);
  let loadError = $state('');
  let drafts = $state({}); // per-task edits
  let meta = $state({}); // per-bike name/plate/type edits
  let adds = $state({}); // per-bike new-task forms
  let confirmText = $state({});
  let rowState = $state({}); // key -> 'loading' | 'success' | 'error'
  let rowError = $state({});

  api.bikes().then(
    async (list) => {
      // full views (need nothing more than tasks, which the list already has)
      bikes = list;
      for (const b of list) seed(b);
      if (q.bike) setTimeout(() => document.getElementById(`bike-${q.bike}`)?.scrollIntoView({ block: 'start' }), 50);
    },
    (e) => (loadError = e.message),
  );

  function seed(b) {
    meta[b.id] = { name: b.name, plate: b.plate, type: b.type };
    for (const t of b.tasks) drafts[t.id] = { name: t.name, every_km: t.every_km ?? '', every_days: t.every_days ?? '' };
    const part = Number(q.bike) === b.id && q.part ? q.part : 'general';
    adds[b.id] ??= { part, name: PARTS[part]?.label ?? '', every_km: '', every_days: '' };
  }

  function replace(view) {
    bikes = bikes.map((b) => (b.id === view.id ? view : b));
    seed(view);
  }

  const intOrNull = (v) => (v === '' || v == null ? null : Number(v));

  async function run(key, fn) {
    rowState[key] = 'loading';
    rowError[key] = '';
    try {
      await fn();
      rowState[key] = 'success';
      setTimeout(() => rowState[key] === 'success' && (rowState[key] = undefined), 1400);
    } catch (err) {
      rowState[key] = 'error';
      rowError[key] = err.message;
    }
  }

  const saveMeta = (b) =>
    run(`meta-${b.id}`, async () => {
      const m = meta[b.id];
      if (!m.name.trim()) throw new Error('Name can’t be empty.');
      replace(await api.patchBike(b.id, { name: m.name, plate: m.plate, type: m.type }));
    });

  const saveTask = (b, t) =>
    run(`task-${t.id}`, async () => {
      const d = drafts[t.id];
      replace(await api.patchTask(b.id, t.id, { name: d.name, every_km: intOrNull(d.every_km), every_days: intOrNull(d.every_days) }));
    });

  async function deleteTask(b, t) {
    if (!confirm(`Delete “${t.name}” and its service history? This can’t be undone.`)) return;
    await run(`task-${t.id}`, async () => {
      await api.deleteTask(b.id, t.id);
      replace(await api.bike(b.id));
    });
  }

  const addTask = (b) =>
    run(`add-${b.id}`, async () => {
      const a = adds[b.id];
      if (!a.name.trim()) throw new Error('Give the item a name.');
      if (!a.every_km && !a.every_days) throw new Error('Set a km interval, a day interval, or both.');
      replace(await api.addTask(b.id, { part: a.part, name: a.name, every_km: intOrNull(a.every_km), every_days: intOrNull(a.every_days) }));
      adds[b.id] = { part: 'general', name: PARTS.general.label, every_km: '', every_days: '' };
    });

  async function deleteBike(b) {
    await run(`del-${b.id}`, async () => {
      await api.deleteBike(b.id);
      bikes = bikes.filter((x) => x.id !== b.id);
      toast(`${b.name} deleted.`);
    });
  }

  async function exportData() {
    await run('export', async () => {
      const data = await api.export();
      const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }));
      const a = Object.assign(document.createElement('a'), { href: url, download: `moto-service-${today()}.json` });
      a.click();
      URL.revokeObjectURL(url);
    });
  }

  async function logout() {
    await api.logout().catch(() => {});
    ui.user = null;
    location.hash = '#/login';
  }
</script>

<div class="page">
  <h1>Settings</h1>

  <section class="block">
    <h2>Account</h2>
    <p class="muted">Logged in as <strong class="who">{ui.user?.email}</strong></p>
    <div class="actions">
      <button class="btn" onclick={exportData} data-state={rowState.export} disabled={rowState.export === 'loading'}>
        {rowState.export === 'success' ? '✓ Downloaded' : 'Export my data (JSON)'}
      </button>
      <button class="btn" onclick={logout}>Log out</button>
    </div>
    {#if rowError.export}<p class="error-text">{rowError.export}</p>{/if}
  </section>

  {#if loadError}
    <p class="error-text" role="alert">{loadError}</p>
  {:else if bikes === null}
    <p class="label">Loading…</p>
  {:else}
    {#each bikes as b (b.id)}
      <section class="block" id="bike-{b.id}">
        <h2>{b.name}</h2>

        <form class="meta" onsubmit={(e) => (e.preventDefault(), saveMeta(b))}>
          <label class="field"><span>Name</span><input class="input" maxlength="80" bind:value={meta[b.id].name} /></label>
          <label class="field"><span>Plate</span><input class="input mono" maxlength="20" bind:value={meta[b.id].plate} /></label>
          <label class="field">
            <span>Type</span>
            <select class="input" bind:value={meta[b.id].type}>
              {#each BIKE_TYPES as t (t.id)}<option value={t.id}>{t.label}</option>{/each}
            </select>
          </label>
          <button class="btn" data-state={rowState[`meta-${b.id}`]} disabled={rowState[`meta-${b.id}`] === 'loading'}>
            {rowState[`meta-${b.id}`] === 'success' ? '✓ Saved' : 'Save'}
          </button>
          {#if rowError[`meta-${b.id}`]}<p class="error-text full">{rowError[`meta-${b.id}`]}</p>{/if}
        </form>

        <h3>Service intervals</h3>
        <p class="muted hint">Starting points only. Check your owner’s manual. Leave a field empty to track by the other one.</p>
        <div class="intervals">
          <div class="ihead label" aria-hidden="true"><span>Item</span><span>Every km</span><span>Every days</span><span></span></div>
          {#each b.tasks as t (t.id)}
            {@const key = `task-${t.id}`}
            <form class="irow" onsubmit={(e) => (e.preventDefault(), saveTask(b, t))}>
              <label class="field"><span class="sr-only">Item name</span><input class="input" maxlength="80" bind:value={drafts[t.id].name} /></label>
              <label class="field"><span class="sr-only">Every km for {t.name}</span><input class="input mono" type="number" min="1" inputmode="numeric" placeholder="—" bind:value={drafts[t.id].every_km} /></label>
              <label class="field"><span class="sr-only">Every days for {t.name}</span><input class="input mono" type="number" min="1" inputmode="numeric" placeholder="—" bind:value={drafts[t.id].every_days} /></label>
              <div class="ibtns">
                <button class="btn btn--small" data-state={rowState[key]} disabled={rowState[key] === 'loading'}>{rowState[key] === 'success' ? '✓' : 'Save'}</button>
                <button type="button" class="btn btn--small btn--ghost" onclick={() => deleteTask(b, t)} aria-label="Delete {t.name}">Delete</button>
              </div>
              {#if rowError[key]}<p class="error-text full">{rowError[key]}</p>{/if}
            </form>
          {/each}

          <form class="irow add" onsubmit={(e) => (e.preventDefault(), addTask(b))}>
            <div class="addname">
              <label class="field">
                <span class="sr-only">Part</span>
                <select class="input" bind:value={adds[b.id].part} onchange={() => (adds[b.id].name = PARTS[adds[b.id].part].label)}>
                  {#each PART_IDS as p (p)}<option value={p}>{PARTS[p].label}</option>{/each}
                </select>
              </label>
              <label class="field"><span class="sr-only">New item name</span><input class="input" maxlength="80" placeholder="Item name" bind:value={adds[b.id].name} /></label>
            </div>
            <label class="field"><span class="sr-only">Every km</span><input class="input mono" type="number" min="1" inputmode="numeric" placeholder="km" bind:value={adds[b.id].every_km} /></label>
            <label class="field"><span class="sr-only">Every days</span><input class="input mono" type="number" min="1" inputmode="numeric" placeholder="days" bind:value={adds[b.id].every_days} /></label>
            <div class="ibtns">
              <button class="btn btn--small btn--primary" data-state={rowState[`add-${b.id}`]} disabled={rowState[`add-${b.id}`] === 'loading'}>Add item</button>
            </div>
            {#if rowError[`add-${b.id}`]}<p class="error-text full">{rowError[`add-${b.id}`]}</p>{/if}
          </form>
        </div>

        <details class="danger">
          <summary>Delete this bike</summary>
          <p class="muted">This removes {b.name} with all its service history and odometer readings. Type the bike’s name to confirm.</p>
          <form class="delrow" onsubmit={(e) => (e.preventDefault(), deleteBike(b))}>
            <label class="field"><span class="sr-only">Type {b.name} to confirm</span><input class="input" placeholder={b.name} bind:value={confirmText[b.id]} /></label>
            <button class="btn btn--danger" disabled={confirmText[b.id] !== b.name || rowState[`del-${b.id}`] === 'loading'} data-state={rowState[`del-${b.id}`]}>Delete bike</button>
          </form>
          {#if rowError[`del-${b.id}`]}<p class="error-text">{rowError[`del-${b.id}`]}</p>{/if}
        </details>
      </section>
    {/each}
    <p class="addb"><a class="btn" href="#/bike/new"><span aria-hidden="true">+</span> Add a bike</a></p>
  {/if}
</div>

<style>
  /* Hallmark · genre: atmospheric · design-system: design.md · designed-as-app */
  h1 { margin: var(--space-2xs) 0 var(--space-lg); }
  .block { padding: var(--space-md); margin-bottom: var(--space-sm); background: var(--color-paper-2); border: var(--rule-hair); border-radius: var(--radius-panel); display: grid; gap: var(--space-sm); scroll-margin-top: calc(var(--nav-h) + var(--space-md)); }
  .block h2 { font-size: var(--text-2xl); font-weight: 800; }
  h3 { margin-top: var(--space-sm); font-weight: 700; }
  .who { color: var(--color-ink); font-weight: 600; overflow-wrap: anywhere; }
  .addb { padding-top: var(--space-sm); }
  .hint { font-size: var(--text-sm); }
  .actions { display: flex; flex-wrap: wrap; gap: var(--space-2xs); }
  .meta { display: grid; gap: var(--space-sm); grid-template-columns: minmax(0, 1fr); align-items: end; max-width: 52rem; }
  @media (min-width: 720px) { .meta { grid-template-columns: minmax(0, 2fr) minmax(0, 1fr) minmax(0, 1.3fr) auto; } }
  .full { grid-column: 1 / -1; }
  .intervals { display: grid; max-width: 52rem; }
  .ihead, .irow { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: var(--space-2xs); align-items: center; }
  .ihead { display: none; padding-bottom: var(--space-2xs); border-bottom: var(--rule-strong); }
  .irow { padding: var(--space-xs) 0; border-bottom: var(--rule-hair); }
  .irow > .field:first-child, .addname { grid-column: 1 / -1; }
  .ibtns { grid-column: 1 / -1; display: flex; gap: var(--space-2xs); }
  .addname { display: grid; gap: var(--space-2xs); grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); }
  .add { background: var(--color-paper); padding: var(--space-xs); border: 1px dashed var(--color-rule-2); border-radius: var(--radius-control); margin-top: var(--space-xs); }
  @media (min-width: 720px) {
    .ihead { display: grid; }
    .ihead, .irow { grid-template-columns: minmax(0, 2.2fr) minmax(0, 1fr) minmax(0, 1fr) 9.5rem; }
    .irow > .field:first-child, .addname, .ibtns { grid-column: auto; }
    .ibtns { justify-content: flex-end; }
  }
  .danger { margin-top: var(--space-sm); }
  .danger summary { cursor: pointer; color: var(--color-overdue-ink); font-weight: 700; min-height: 2.75rem; display: flex; align-items: center; }
  .danger p { margin-bottom: var(--space-xs); font-size: var(--text-sm); }
  .delrow { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: var(--space-2xs); max-width: 28rem; }
</style>
