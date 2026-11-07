<script>
  import { STATE_ICON, STATE_LABEL } from './format.js';
  let { state = 'none' } = $props();
</script>

<span class="chip chip--{state}"><span aria-hidden="true">{STATE_ICON[state]}</span>{STATE_LABEL[state]}</span>
