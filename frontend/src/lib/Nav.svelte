<script>
  import { api } from './api.js';
  import { ui } from './state.svelte.js';
  let { route } = $props();
  async function logout() {
    await api.logout().catch(() => {});
    ui.user = null;
    location.hash = '#/login';
  }
  const is = (...names) => names.includes(route.name);
</script>

<!-- N9 edge-aligned: wordmark hard-left, two quiet links, the one amber button hard-right -->
<header class="nav">
  <div class="in">
    <a class="brand" href="#/" aria-label="Moto Service, garage"><span class="dot" aria-hidden="true"></span>MOTO<span class="long">&nbsp;SERVICE</span></a>
    <nav aria-label="Main">
      <a href="#/" aria-current={is('garage', 'bike', 'new') ? 'page' : undefined}>Garage</a>
      <a href="#/settings" aria-current={is('settings') ? 'page' : undefined}>Settings</a>
    </nav>
    <button class="out" onclick={logout}>Log out</button>
    <a class="btn btn--primary log" href="#/log" aria-current={is('log') ? 'page' : undefined}>
      <span aria-hidden="true">+</span><span>Log<span class="long">&nbsp;service</span></span>
    </a>
  </div>
</header>

<style>
  .nav {
    position: sticky;
    top: 0;
    z-index: 50;
    background: color-mix(in srgb, var(--color-paper) 88%, transparent);
    backdrop-filter: blur(10px);
    border-bottom: var(--rule-hair);
  }
  .in {
    max-width: var(--sheet-w);
    margin: 0 auto;
    padding: 0 var(--gutter);
    min-height: var(--nav-h);
    display: flex;
    align-items: center;
    gap: var(--space-sm);
  }
  .brand {
    display: inline-flex;
    align-items: center;
    gap: var(--space-2xs);
    font: 800 var(--text-base)/1 var(--font-display);
    letter-spacing: 0.14em;
    color: var(--color-ink);
    text-decoration: none;
    white-space: nowrap;
  }
  .dot { width: 0.6rem; height: 0.6rem; border-radius: 50%; background: var(--color-accent); box-shadow: 0 0 10px var(--color-accent-glow); }
  nav { display: flex; gap: var(--space-3xs); margin-right: auto; }
  nav a {
    display: inline-flex;
    align-items: center;
    min-height: 2.75rem;
    padding: 0 var(--space-2xs);
    font: 600 var(--text-xs)/1 var(--font-display);
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--color-muted);
    text-decoration: none;
    white-space: nowrap;
    border-bottom: 2px solid transparent;
    transition: color var(--dur-fast) var(--ease-out);
  }
  nav a:hover { color: var(--color-ink); }
  nav a[aria-current='page'] { color: var(--color-ink); border-bottom-color: var(--color-accent); }
  .out {
    display: none;
    min-height: 2.75rem;
    padding: 0 var(--space-2xs);
    background: none;
    border: 0;
    font: 600 var(--text-xs)/1 var(--font-display);
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--color-muted);
    cursor: pointer;
    white-space: nowrap;
    transition: color var(--dur-fast) var(--ease-out);
  }
  .out:hover { color: var(--color-ink); }
  .out:active { transform: translateY(1px); }
  @media (min-width: 720px) { .out { display: inline-flex; align-items: center; } }
  .long { display: none; }
  @media (min-width: 520px) {
    .long { display: inline; }
    nav { gap: var(--space-xs); margin-left: var(--space-sm); }
  }
</style>
