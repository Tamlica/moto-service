<script>
  import { Tween } from 'svelte/motion';
  import { cubicOut } from 'svelte/easing';
  import { BIKES } from '../bikes/index.js';
  import { PARTS } from './parts.js';
  import { describe, readout, STATE_LABEL } from './format.js';

  /** tasks: server tasks (sorted worst-first). mini: thumbnail, no interaction. */
  let { type, tasks = [], exploded = false, selected = null, onselect = null, mini = false, light = false, title = '' } = $props();

  const OX = 100; // drawing is shifted right to leave room for the left label column
  const K = 0.35; // explode distance factor
  const reduce = typeof matchMedia !== 'undefined' && matchMedia('(prefers-reduced-motion: reduce)').matches;
  const t = new Tween(0, { duration: reduce ? 0 : 450, easing: cubicOut });
  $effect(() => {
    t.target = exploded ? 1 : 0;
  });

  let width = $state(0);
  let svg;
  let bike = $derived(BIKES[type] ?? BIKES.scooter);
  let showLabels = $derived(!mini && width >= 720);
  let viewBox = $derived(mini ? '300 90 640 400' : showLabels ? '0 40 1200 470' : '300 90 650 410');

  let parts = $derived(
    bike.parts.map((p) => {
      const task = tasks.find((x) => x.part === p.id);
      const [cx, cy] = bike.center;
      return {
        ...p,
        task,
        state: task ? task.state : 'none',
        ex: (p.at[0] - cx) * K,
        ey: (p.at[1] - cy) * K,
        name: task?.name ?? PARTS[p.id]?.label ?? p.id,
      };
    }),
  );

  let layout = $derived.by(() => {
    const left = [];
    const right = [];
    for (const p of parts) (p.at[0] < bike.center[0] ? left : right).push(p);
    const out = {};
    for (const [col, side] of [[left, 'left'], [right, 'right']]) {
      col.sort((a, b) => a.at[1] - b.at[1]);
      const n = col.length;
      const step = n > 1 ? Math.min(66, 390 / (n - 1)) : 0;
      const top = 275 - (step * (n - 1)) / 2;
      col.forEach((p, i) => (out[p.id] = { y: top + i * step, side }));
    }
    return out;
  });

  const pos = (p) => [p.at[0] + OX + p.ex * t.current, p.at[1] + p.ey * t.current];

  function pick(id) {
    onselect?.(id);
  }

  // Tap anywhere: select the nearest part. Makes small hotspots usable on phones.
  function nearest(e) {
    if (!onselect || mini || !svg) return;
    const pt = svg.createSVGPoint();
    pt.x = e.clientX;
    pt.y = e.clientY;
    const m = svg.getScreenCTM();
    if (!m) return;
    const q = pt.matrixTransform(m.inverse());
    let best = null;
    let bd = 80;
    for (const p of parts) {
      const [x, y] = pos(p);
      const d = Math.hypot(x - q.x, y - q.y);
      if (d < bd) [bd, best] = [d, p];
    }
    if (best) pick(best.id);
  }
</script>

<div class="schem" class:mini class:light bind:clientWidth={width}>
  <!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_noninteractive_element_interactions -->
  <svg
    bind:this={svg}
    {viewBox}
    role={mini ? 'img' : 'group'}
    aria-label={title || `${type} schematic`}
    onclick={nearest}
  >
    <line class="ground" x1={OX + 150} y1="472" x2={OX + 860} y2="472" />
    <g transform="translate({OX} 0)">
      <g class="frame">
        {#each bike.frame as [tag, a], i (i)}
          <svelte:element this={tag} {...a} />
        {/each}
      </g>
      {#each parts as p (p.id)}
        <!-- svelte-ignore a11y_no_noninteractive_tabindex -->
        <g
          class="part s-{p.state}"
          class:sel={selected === p.id}
          transform="translate({p.ex * t.current} {p.ey * t.current})"
          role={mini ? undefined : 'button'}
          tabindex={mini ? undefined : 0}
          aria-label={mini ? undefined : `${p.name}: ${STATE_LABEL[p.state]}. ${describe(p.task)}`}
          aria-pressed={mini ? undefined : selected === p.id}
          onclick={(e) => {
            e.stopPropagation();
            pick(p.id);
          }}
          onkeydown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              pick(p.id);
            }
          }}
        >
          {#each p.shapes as [tag, a], i (i)}
            <svelte:element this={tag} {...a} class="shape" />
          {/each}
          {#if !mini}
            <circle class="halo" cx={p.at[0]} cy={p.at[1]} r="9" />
            <circle class="hot" cx={p.at[0]} cy={p.at[1]} r="7" />
          {/if}
        </g>
      {/each}
    </g>

    {#if showLabels}
      {#each parts as p (p.id)}
        {@const l = layout[p.id]}
        {@const [ax, ay] = pos(p)}
        {@const lx = l.side === 'left' ? 280 : 940}
        {@const elbow = l.side === 'left' ? lx + 26 : lx - 26}
        <!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
        <g class="lbl s-{p.state}" class:sel={selected === p.id} aria-hidden="true" onclick={(e) => { e.stopPropagation(); pick(p.id); }}>
          <polyline class="leader" points="{ax},{ay} {elbow},{l.y} {lx},{l.y}" />
          <circle class="tick" cx={lx} cy={l.y} r="2" />
          <text x={l.side === 'left' ? lx - 10 : lx + 10} y={l.y - 2} text-anchor={l.side === 'left' ? 'end' : 'start'}>
            <tspan class="lbl-name">{p.name.toUpperCase()}</tspan>
            <tspan class="lbl-read" x={l.side === 'left' ? lx - 10 : lx + 10} dy="16">{readout(p.task)}</tspan>
          </text>
        </g>
      {/each}
    {/if}
  </svg>
</div>

<style>
  .schem { min-width: 0; }
  .mini svg { overflow: hidden; }
  svg { display: block; width: 100%; height: auto; overflow: visible; user-select: none; -webkit-tap-highlight-color: transparent; }
  .ground { stroke: var(--color-graphite-rule); stroke-width: 1.5; stroke-dasharray: 6 8; vector-effect: non-scaling-stroke; }
  .frame :global(*) {
    fill: none;
    stroke: var(--color-line);
    stroke-width: 1.4;
    stroke-linecap: round;
    stroke-linejoin: round;
    vector-effect: non-scaling-stroke;
  }
  .part, .lbl { --status: var(--color-line-dim); }
  .s-ok { --status: var(--color-ok); }
  .s-soon { --status: var(--color-soon); }
  .s-overdue { --status: var(--color-overdue); }
  .s-due { --status: var(--color-due); }
  .part { cursor: pointer; outline: none; }
  .mini .part { cursor: inherit; }
  .part :global(.shape) {
    fill: none;
    stroke: var(--status);
    stroke-width: 2.4;
    stroke-linecap: round;
    stroke-linejoin: round;
    vector-effect: non-scaling-stroke;
    transition: stroke-width var(--dur-fast) var(--ease-out);
  }
  .mini .part :global(.shape) { stroke-width: 1.8; }
  .part:hover :global(.shape), .part.sel :global(.shape) { stroke-width: 3.6; }
  .hot { fill: var(--status); stroke: var(--color-graphite); stroke-width: 3; }
  .halo { fill: none; stroke: var(--status); stroke-width: 2; opacity: 0; transform-box: fill-box; transform-origin: center; }
  .s-overdue .halo { animation: pulse-once 1.4s var(--ease-out) 300ms 1 both; }
  .part.sel .hot { stroke: var(--color-on-dark); }
  .part:focus-visible .halo { animation: none; opacity: 1; stroke: var(--color-accent-on-dark); stroke-width: 2.5; transform: scale(1.9); }
  @keyframes pulse-once {
    0% { opacity: 0.95; transform: scale(1); }
    100% { opacity: 0; transform: scale(3.4); }
  }

  .lbl { cursor: pointer; }
  .leader { fill: none; stroke: var(--color-line-dim); stroke-width: 1; vector-effect: non-scaling-stroke; }
  .tick { fill: var(--color-line-dim); }
  .lbl.sel .leader { stroke: var(--color-accent-on-dark); }
  .lbl-name { font: 600 12px var(--font-body); letter-spacing: 0.09em; fill: var(--color-on-dark-2); }
  .lbl.sel .lbl-name, .lbl:hover .lbl-name { fill: var(--color-on-dark); }
  .lbl-read { font: 800 13px var(--font-body); letter-spacing: 0.02em; font-variant-numeric: tabular-nums; fill: var(--status); }
  .s-none .lbl-read { fill: var(--color-line-dim); }

  /* light variant: drawn on the paper sheet (garage index, type picker) */
  .light .ground { stroke: var(--color-rule-2); }
  .light .frame :global(*) { stroke: var(--color-ink-2); }
  .light .part { --status: var(--color-rule-2); }
  .light .s-ok { --status: var(--color-ok-ink); }
  .light .s-soon { --status: var(--color-soon-ink); }
  .light .s-overdue { --status: var(--color-overdue); }
  .light .s-due { --status: var(--color-due-ink); }
  .light .part :global(.shape) { stroke-width: 2.2; }

  @media (prefers-reduced-motion: reduce) {
    .s-overdue .halo { animation: none; }
  }
</style>
