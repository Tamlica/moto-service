<script>
  import { api } from '../lib/api.js';
  import { ui } from '../lib/state.svelte.js';
  import Schematic from '../lib/Schematic.svelte';

  let { q = {} } = $props();
  let mode = $state(q.mode === 'register' ? 'register' : 'login');
  let email = $state('');
  let password = $state('');
  let busy = $state(false);
  let error = $state('');

  async function submit(e) {
    e.preventDefault();
    error = '';
    busy = true;
    try {
      ui.user = await (mode === 'login' ? api.login : api.register)({ email, password });
      location.hash = '#/';
    } catch (err) {
      error = err.message;
    } finally {
      busy = false;
    }
  }
</script>

<div class="login">
  <section class="copy">
    <a class="brand" href="#/"><span class="dot" aria-hidden="true"></span>MOTO SERVICE</a>
    <h1>Know what your bike needs next</h1>
    <p class="lede">
      Log oil changes, parts and kilometres. Each job is tracked by distance and by date, whichever comes first, so
      nothing slips.
    </p>

    <form onsubmit={submit} novalidate>
      <div class="tabs" role="group" aria-label="Account">
        <button type="button" aria-pressed={mode === 'login'} onclick={() => ((mode = 'login'), (error = ''))}>Log in</button>
        <button type="button" aria-pressed={mode === 'register'} onclick={() => ((mode = 'register'), (error = ''))}>Create account</button>
      </div>
      <label class="field">
        <span>Email</span>
        <input class="input" type="email" autocomplete="email" required bind:value={email} aria-invalid={!!error} />
      </label>
      <label class="field">
        <span>Password</span>
        <input
          class="input"
          type="password"
          minlength="8"
          autocomplete={mode === 'login' ? 'current-password' : 'new-password'}
          required
          bind:value={password}
          aria-invalid={!!error}
          aria-describedby="pw-hint"
        />
        <small id="pw-hint">{mode === 'register' ? 'At least 8 characters.' : ''}</small>
      </label>
      {#if error}<p class="error-text" role="alert">{error}</p>{/if}
      <button class="btn btn--primary submit" data-state={busy ? 'loading' : undefined} disabled={busy}>
        {mode === 'login' ? 'Log in' : 'Create account'}
      </button>
    </form>
  </section>

  <figure class="stage" aria-hidden="true">
    <Schematic type="sport" mini title="Motorcycle schematic" />
    <span class="lstamp stamp stamp--round">Serviced<small>on time</small></span>
    <figcaption class="label">Sport · side view · every part tracked by km and date</figcaption>
  </figure>

  <footer class="foot label">
    <span>Moto Service</span><span>Service log by km and date</span>
  </footer>
</div>

<style>
  /* Hallmark · genre: atmospheric · footer: Ft4 colophon line · design-system: design.md */
  .login {
    min-height: 100dvh;
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    grid-template-rows: auto auto 1fr auto;
    gap: var(--space-xl);
    padding: var(--space-lg) var(--gutter) var(--space-sm);
    max-width: var(--sheet-w);
    margin: 0 auto;
  }
  .copy { display: grid; gap: var(--space-md); align-content: start; max-width: 34rem; }
  .brand { justify-self: start; text-decoration: none; display: inline-flex; align-items: center; gap: var(--space-2xs); font: 800 var(--text-base)/1 var(--font-display); letter-spacing: 0.14em; color: var(--color-ink); }
  .dot { width: 0.6rem; height: 0.6rem; border-radius: 50%; background: var(--color-accent); box-shadow: 0 0 10px var(--color-accent-glow); }
  h1 { font-size: clamp(2.5rem, 1rem + 4vw, 4rem); }
  .lede { font-size: var(--text-lg); color: var(--color-ink-2); max-width: 36ch; }
  form { display: grid; gap: var(--space-sm); padding: var(--space-md); background: var(--color-paper-2); border: var(--rule-hair); border-radius: var(--radius-panel); }
  .tabs { display: flex; padding: 3px; gap: 3px; background: var(--color-paper); border-radius: var(--radius-control); }
  .tabs button {
    flex: 1;
    min-height: 2.75rem;
    background: none;
    border: 0;
    border-radius: 8px;
    font: 700 var(--text-xs)/1 var(--font-display);
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--color-muted);
    cursor: pointer;
    white-space: nowrap;
    transition: background-color var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out);
  }
  .tabs button:hover { color: var(--color-ink); }
  .tabs button[aria-pressed="true"] { color: var(--color-ink); background: var(--color-paper-3); box-shadow: inset 0 -2px 0 var(--color-accent); }
  .submit { width: 100%; min-height: 3rem; }
  .stage {
    position: relative;
    margin: 0;
    background: var(--color-graphite);
    border: var(--rule-hair);
    border-radius: var(--radius-panel);
    padding: var(--space-lg) var(--space-md);
    display: grid;
    align-content: center;
    gap: var(--space-sm);
    min-width: 0;
    overflow: hidden;
  }
  .stage figcaption { color: var(--color-on-dark-2); }
  .lstamp { position: absolute; top: var(--space-md); right: var(--space-md); width: 5.5rem; font-size: var(--text-xs); }
  .foot { display: flex; flex-wrap: wrap; justify-content: space-between; gap: var(--space-2xs) var(--space-sm); padding-top: var(--space-sm); border-top: var(--rule-hair); }
  @media (min-width: 900px) {
    .login {
      grid-template-columns: minmax(0, 5fr) minmax(0, 7fr);
      grid-template-rows: 1fr auto;
      column-gap: var(--space-2xl);
      padding-block: var(--space-xl) var(--space-md);
      align-items: center;
    }
    .stage { align-self: stretch; padding: var(--space-xl) var(--space-lg); }
    .foot { grid-column: 1 / -1; }
  }
</style>
