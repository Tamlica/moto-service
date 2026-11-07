<script>
  import { onMount } from 'svelte';
  import { api } from './lib/api.js';
  import { ui } from './lib/state.svelte.js';
  import Nav from './lib/Nav.svelte';
  import Toast from './lib/Toast.svelte';
  import Login from './pages/Login.svelte';
  import Landing from './pages/Landing.svelte';
  import Garage from './pages/Garage.svelte';
  import Bike from './pages/Bike.svelte';
  import NewBike from './pages/NewBike.svelte';
  import LogService from './pages/LogService.svelte';
  import Settings from './pages/Settings.svelte';

  function parse() {
    const [path, qs] = location.hash.replace(/^#/, '').split('?');
    const q = Object.fromEntries(new URLSearchParams(qs || ''));
    const seg = (path || '/').split('/').filter(Boolean);
    if (seg[0] === 'login') return { name: 'login', q };
    if (seg[0] === 'bike' && seg[1] === 'new') return { name: 'new', q };
    if (seg[0] === 'bike' && seg[1]) return { name: 'bike', id: Number(seg[1]), q };
    if (seg[0] === 'log') return { name: 'log', q };
    if (seg[0] === 'settings') return { name: 'settings', q };
    return { name: 'garage', q };
  }

  let route = $state(parse());
  let key = $derived(route.name + (route.id ?? '') + JSON.stringify(route.q));

  onMount(() => {
    const onHash = () => {
      route = parse();
      window.scrollTo(0, 0);
    };
    window.addEventListener('hashchange', onHash);
    api.me().then(
      (u) => {
        ui.user = u;
        if (route.name === 'login') location.hash = '#/';
      },
      () => {
        ui.user = null;
        // logged-out visitors get the landing page; #/login is the form
      },
    );
    return () => window.removeEventListener('hashchange', onHash);
  });
</script>

{#if ui.user === undefined}
  <p class="boot label">Loading…</p>
{:else if !ui.user && route.name !== 'login'}
  <Landing />
{:else if !ui.user || route.name === 'login'}
  {#key route.q.mode}<Login q={route.q} />{/key}
{:else}
  <Nav {route} />
  <main id="main">
    {#key key}
      {#if route.name === 'garage'}<Garage />
      {:else if route.name === 'bike'}<Bike id={route.id} />
      {:else if route.name === 'new'}<NewBike />
      {:else if route.name === 'log'}<LogService q={route.q} />
      {:else if route.name === 'settings'}<Settings q={route.q} />
      {/if}
    {/key}
  </main>
{/if}
<Toast />

<style>
  .boot { padding: var(--space-xl) var(--space-sm); }
  main { min-width: 0; }
</style>
