<script>
  import { fly } from 'svelte/transition';
  import { cubicOut } from 'svelte/easing';
  import { ui, dismissToast } from './state.svelte.js';
  const reduce = typeof matchMedia !== 'undefined' && matchMedia('(prefers-reduced-motion: reduce)').matches;

  function act() {
    const run = ui.toast.action.run;
    dismissToast();
    run();
  }
</script>

<div class="toast-region" role="status" aria-live="polite">
  {#if ui.toast}
    {#key ui.toast.id}
      <div class="toast" transition:fly={{ y: reduce ? 0 : 12, duration: reduce ? 120 : 220, easing: cubicOut }}>
        <span>{ui.toast.message}</span>
        {#if ui.toast.action}
          <button class="undo" onclick={act}>{ui.toast.action.label}</button>
        {/if}
      </div>
    {/key}
  {/if}
</div>

<style>
  .toast-region {
    position: fixed;
    z-index: 80;
    left: 50%;
    transform: translateX(-50%);
    bottom: calc(var(--space-sm) + env(safe-area-inset-bottom));
    width: min(28rem, calc(100% - 2 * var(--space-sm)));
    pointer-events: none;
  }
  @media (min-width: 900px) {
    .toast-region { bottom: var(--space-lg); }
  }
  .toast {
    pointer-events: auto;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--space-sm);
    padding: var(--space-xs) var(--space-sm);
    background: var(--color-paper-3);
    color: var(--color-on-dark);
    border: var(--rule-strong);
    border-left: 4px solid var(--color-accent);
    border-radius: var(--radius-control);
    box-shadow: 0 12px 32px var(--color-scrim);
    font: 500 var(--text-sm)/1.4 var(--font-body);
  }
  .undo {
    background: none;
    border: 0;
    padding: var(--space-2xs);
    color: var(--color-accent-on-dark);
    font: 700 var(--text-xs)/1 var(--font-display);
    letter-spacing: 0.14em;
    text-transform: uppercase;
    min-height: 2.75rem;
    cursor: pointer;
    white-space: nowrap;
  }
  .undo:hover { text-decoration: underline; text-underline-offset: 3px; }
</style>
