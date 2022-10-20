<script>
  import { logout, address, online } from './stores/connection'
  import { darkMode, sync, syncing, generateStopset } from './stores/store'

  export let generated = generateStopset()
</script>

<div class="flex flex-col space-y-1 items-center justify-center min-h-screen">
  <button on:click={logout} class="btn btn-warning">Logout</button>
  <button on:click={sync} class="btn btn-primary" disabled={$syncing}>Sync</button>
  <button on:click={() => generated = generateStopset()} class="btn btn-secondary">Generate Stopset</button>
  <button on:click={() => $darkMode = !$darkMode} class="btn btn-info">{$darkMode ? 'Day' : 'Night'} mode</button>
  <span>{$address} ({$online ? 'online' : 'offline'})</span>
  {#if generated}
    <span>{generated.stopset.name}</span>
    <ol class="list-decimal">
      {#each generated.assets as [rotator, asset]}
        <li>{rotator.name} &mdash; {#if asset}{asset.name}{:else}<strong class="text-error">No asset available to generate</strong>{/if}</li>
      {/each}
    </ol>
  {:else}
    <span>No stopset generated!</span>
  {/if}
</div>
