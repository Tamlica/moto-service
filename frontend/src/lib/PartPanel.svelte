<script>
  import { onMount } from 'svelte';
  import { fly, fade } from 'svelte/transition';
  import { cubicOut } from 'svelte/easing';
  import { api } from './api.js';
  import { toast } from './state.svelte.js';
  import { PARTS } from './parts.js';
  import { date, describe, interval, km, money, num, today, dateShort } from './format.js';
  import Gauge from './Gauge.svelte';
  import StatusBadge from './StatusBadge.svelte';

  /** task may be null when the part isn't tracked on this bike */
  let { bike, part, task, onclose, onchange } = $props();

  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const wide = matchMedia('(min-width: 900px)').matches;
  const flyIn = reduce ? { duration: 120, opacity: 0 } : wide ? { x: 48, duration: 260, easing: cubicOut } : { y: 64, duration: 260, easing: cubicOut };

  let panel;
  let busy = $state(false);
  let done = $state(false);
  let error = $state('');
  let info = $derived(PARTS[part] ?? PARTS.general);
  let history = $derived(task ? bike.logs.filter((l) => l.task_id === task.id) : []);

  onMount(() => {
    const prev = document.activeElement;
    panel.querySelector('[data-autofocus]')?.focus();
    return () => prev?.focus?.();
  });

  function onkey(e) {
    if (e.key === 'Escape') return onclose();
    if (e.key !== 'Tab') return;
    const f = [...panel.querySelectorAll('a[href], button:not([disabled]), input, [tabindex="0"]')];
    if (!f.length) return;
    const [first, last] = [f[0], f.at(-1)];
    if (e.shiftKey && document.activeElement === first) (last.focus(), e.preventDefault());
    else if (!e.shiftKey && document.activeElement === last) (first.focus(), e.preventDefault());
  }

  async function markDone() {
    busy = true;
    error = '';
    try {
      const view = await api.addLogs(bike.id, { task_ids: [task.id], date: today(), km: bike.current_km });
      const ids = view.created_log_ids;
      onchange(view);
      done = true;
      setTimeout(() => (done = false), 1600);
      toast(`${task.name} logged at ${km(bike.current_km)}.`, {
        label: 'Undo',
        run: async () => {
          for (const id of ids) await api.deleteLog(bike.id, id);
          onchange(await api.bike(bike.id));
        },
      });
    } catch (err) {
      error = err.message;
    } finally {
      busy = false;
    }
  }
</script>

<svelte:window onkeydown={onkey} />

<!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
<div class="scrim" onclick={onclose} transition:fade={{ duration: reduce ? 100 : 180 }}></div>
<div
  class="panel"
  bind:this={panel}
  role="dialog"
  aria-modal="true"
  aria-labelledby="panel-title"
  transition:fly={flyIn}
>
  <header>
    <div>
      {#if task && task.name !== info.label}<p class="label">{info.label}</p>{/if}
      <h2 id="panel-title">{task?.name ?? info.label}</h2>
    </div>
    <button class="btn btn--ghost btn--small close" onclick={onclose} aria-label="Close" data-autofocus>✕</button>
  </header>

  {#if task}
    <div class="status">
      <Gauge {task} size={96} />
      <div class="st">
        <StatusBadge state={task.state} />
        <p class="desc">{describe(task)}</p>
      </div>
      {#if done}<span class="donestamp stamp stamp--round thunk" role="status">Done<small>{dateShort(today())}</small></span>{/if}
    </div>

    <dl class="readouts">
      {#if task.every_km}
        <div><dt class="label">Km left</dt><dd class="mono">{task.km_left == null ? '—' : num(task.km_left)}</dd></div>
      {/if}
      {#if task.every_days}
        <div><dt class="label">Days left</dt><dd class="mono">{task.days_left == null ? '—' : num(task.days_left)}</dd></div>
      {/if}
      <div><dt class="label">Next due</dt><dd class="mono small">{task.predicted ? '~' + date(task.predicted) : '—'}</dd></div>
    </dl>

    <dl class="facts">
      <div><dt>Interval</dt><dd>{interval(task)}</dd></div>
      <div><dt>Last done</dt><dd>{task.last_date ? `${date(task.last_date)} at ${km(task.last_km)}` : 'Never logged'}</dd></div>
      {#if task.next_km}<div><dt>Due at</dt><dd class="mono">{km(task.next_km)}</dd></div>{/if}
    </dl>

    <p class="why"><strong>Why it matters.</strong> {info.why}</p>

    {#if error}<p class="error-text" role="alert">{error}</p>{/if}
    <div class="actions">
      <button class="btn btn--primary" onclick={markDone} disabled={busy} data-state={busy ? 'loading' : done ? 'success' : undefined}>
        {done ? '✓ Logged' : `Mark done today at ${km(bike.current_km)}`}
      </button>
      <a class="btn" href="#/log?bike={bike.id}&task={task.id}">Log with cost or notes</a>
    </div>

    <section class="hist">
      <h3 class="label">History</h3>
      {#if history.length}
        <ol>
          {#each history as l (l.id)}
            <li>
              <span class="mono">{date(l.date)}</span>
              <span class="mono muted">{km(l.km)}</span>
              {#if l.cost != null}<span class="mono muted">{money(l.cost)}</span>{/if}
              {#if l.note}<span class="note">{l.note}</span>{/if}
            </li>
          {/each}
        </ol>
      {:else}
        <p class="muted">Nothing logged yet.</p>
      {/if}
    </section>
  {:else}
    <div class="status"><StatusBadge state="none" /></div>
    <p class="why"><strong>Why it matters.</strong> {info.why}</p>
    <p class="muted">This part isn't tracked on {bike.name}. Add it with your own interval in Settings.</p>
    <div class="actions">
      <a class="btn btn--primary" href="#/settings?bike={bike.id}&part={part}">Track this part</a>
    </div>
  {/if}
</div>

<style>
  .scrim { position: fixed; inset: 0; z-index: 70; background: var(--color-scrim); backdrop-filter: blur(2px); }
  .panel {
    position: fixed;
    z-index: 71;
    inset: auto 0 0 0;
    max-height: 88dvh;
    overflow-y: auto;
    overscroll-behavior: contain;
    background: var(--color-paper-2);
    border-top: var(--rule-strong);
    border-radius: var(--radius-panel) var(--radius-panel) 0 0;
    box-shadow: 0 -2px 0 var(--color-accent-glow);
    padding: var(--space-md) var(--gutter) calc(var(--space-lg) + env(safe-area-inset-bottom));
    display: grid;
    gap: var(--space-md);
    align-content: start;
  }
  @media (min-width: 900px) {
    .panel {
      inset: var(--space-sm) var(--space-sm) var(--space-sm) auto;
      width: min(30rem, 100%);
      max-height: none;
      border: var(--rule-strong);
      border-radius: var(--radius-panel);
      box-shadow: 0 24px 64px var(--color-scrim);
      padding: var(--space-lg);
    }
  }
  header { display: flex; justify-content: space-between; align-items: start; gap: var(--space-sm); }
  header .label { margin-bottom: var(--space-2xs); }
  h2 { font: 800 var(--text-3xl)/1 var(--font-display); }
  .close { font-size: var(--text-lg); width: 2.75rem; min-height: 2.75rem; padding: 0; }
  .status { position: relative; display: flex; align-items: center; gap: var(--space-sm); padding: var(--space-sm); background: var(--color-paper); border: var(--rule-hair); border-radius: var(--radius-control); }
  .st { display: grid; gap: var(--space-2xs); justify-items: start; min-width: 0; }
  .desc { font: 600 var(--text-lg)/1.3 var(--font-body); color: var(--color-ink); }
  .donestamp { position: absolute; right: var(--space-sm); top: 50%; translate: 0 -50%; width: 5.25rem; font-size: var(--text-xs); }
  .readouts { display: grid; grid-template-columns: repeat(auto-fit, minmax(7rem, 1fr)); gap: var(--space-2xs); margin: 0; }
  .readouts div { padding: var(--space-xs); background: var(--color-paper); border: var(--rule-hair); border-radius: var(--radius-control); }
  dd { margin: 0; }
  .readouts dd { font: 800 var(--text-2xl)/1 var(--font-display); color: var(--color-accent); text-shadow: 0 0 14px var(--color-accent-glow); margin-top: var(--space-2xs); font-variant-numeric: tabular-nums; }
  .readouts dd.small { font-size: var(--text-lg); }
  .facts { display: grid; margin: 0; font-size: var(--text-sm); }
  .facts div { display: grid; grid-template-columns: 7rem minmax(0, 1fr); gap: var(--space-xs); padding: var(--space-2xs) 0; border-bottom: var(--rule-hair); }
  .facts dt { font: 600 var(--text-xs)/1.6 var(--font-display); letter-spacing: 0.14em; text-transform: uppercase; color: var(--color-muted); }
  .facts dd { color: var(--color-ink); font-weight: 500; }
  .why { font-size: var(--text-sm); padding: var(--space-xs) var(--space-sm); border-left: 3px solid var(--color-accent); background: var(--color-paper); border-radius: 0 var(--radius-control) var(--radius-control) 0; color: var(--color-ink-2); }
  .why strong { color: var(--color-ink); font-weight: 600; }
  .actions { display: grid; gap: var(--space-2xs); }
  .actions .btn { width: 100%; min-height: 3rem; }
  .hist { display: grid; gap: var(--space-xs); }
  .hist ol { list-style: none; margin: 0; padding: 0; display: grid; }
  .hist li { display: flex; flex-wrap: wrap; gap: 0 var(--space-sm); padding: var(--space-2xs) 0; border-bottom: var(--rule-hair); font-size: var(--text-sm); }
  .note { flex-basis: 100%; color: var(--color-ink-2); }
</style>
