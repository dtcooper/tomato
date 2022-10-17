<script>
  import { logout, address } from './stores/connection'
  import { sync, generateStopset, stopsets, rotators, assets } from './stores/store'
  import { randomChoice } from './utils'

  export let generated = generateStopset()
</script>

<div class="flex flex-col space-y-1 items-center justify-center min-h-screen">
  <button on:click={logout} class="btn btn-warning">Logout</button>
  <button on:click={sync} class="btn btn-primary">Sync</button>
  <button on:click={() => generated = generateStopset()} class="btn btn-secondary">Generate Stopset</button>
  <span>{$address}</span>
  {#if generated}
    <span>{generated.stopset.name}</span>
    <ol class="list-decimal">
      {#each generated.assets as [rotator, asset]}
        <li>{rotator.name} &mdash; {asset.name}</li>
      {/each}
    </ol>
  {:else}
    <span>No stopset generated!</span>
  {/if}
</div>
