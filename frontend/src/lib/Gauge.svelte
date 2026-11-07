<script>
  import { wear } from './format.js';
  /** A dash gauge: the arc is the share of the interval used. */
  let { task, size = 64 } = $props();
  const C = 2 * Math.PI * 26;
  let w = $derived(wear(task));
  let state = $derived(task?.state ?? 'none');
  let mid = $derived(state === 'overdue' ? '!' : state === 'due' ? '?' : w == null ? '–' : `${Math.round(w * 100)}%`);
</script>

<svg class="gauge s-{state}" viewBox="0 0 64 64" width={size} height={size} aria-hidden="true">
  <circle class="trk" cx="32" cy="32" r="26" />
  {#if w != null}
    <circle class="arc" cx="32" cy="32" r="26" stroke-dasharray="{C * w} {C}" />
  {/if}
  <text x="32" y="37" text-anchor="middle">{mid}</text>
</svg>

<style>
  .gauge { display: block; flex: none; --g: var(--color-muted); }
  .s-ok { --g: var(--color-ok); }
  .s-soon { --g: var(--color-soon); }
  .s-overdue { --g: var(--color-overdue); }
  .s-due { --g: var(--color-due); }
  .trk { fill: none; stroke: var(--color-rule); stroke-width: 6; }
  .s-due .trk { stroke: var(--g); stroke-dasharray: 3 5; stroke-width: 3; }
  .arc {
    fill: none;
    stroke: var(--g);
    stroke-width: 6;
    stroke-linecap: round;
    transform: rotate(-90deg);
    transform-origin: 32px 32px;
    filter: drop-shadow(0 0 4px var(--g));
    animation: sweep var(--dur-slow) var(--ease-out) both;
  }
  text { font: 700 13px var(--font-display); fill: var(--color-ink); font-variant-numeric: tabular-nums; }
  .s-overdue text { fill: var(--color-overdue-ink); font-size: 20px; }
  .s-due text { fill: var(--g); font-size: 18px; }
  @keyframes sweep { from { stroke-dashoffset: 163; opacity: 0.3; } }
</style>
