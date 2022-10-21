<script>
  import { logout, address, online } from './stores/connection'
  import { darkMode, sync, syncing, generateStopset } from './stores/store'
  import { colors } from '../../server/constants.json'

  export let generated = generateStopset()
  export const getColor = (name, value = 'value') => colors.find(color => color.name === name)[value]
</script>

<div class="flex flex-col space-y-1 items-center h-screen max-h-screen w-full max-w-full p-2">
  <div class="btn-group mt-2">
    <button on:click={logout} class="btn btn-warning">Logout</button>
    <button on:click={sync} class="btn btn-primary" disabled={$syncing}>Sync</button>
    <button on:click={() => generated = generateStopset()} class="btn btn-secondary">Generate Stopset</button>
    <button on:click={() => $darkMode = !$darkMode} class="btn btn-info">{$darkMode ? 'Day' : 'Night'} mode</button>
  </div>

  <span>{$address} ({$online ? 'online' : 'offline'})</span>
  {#if generated}
    {@const stopset = generated.stopset}
    {@const assets = generated.assets}
    <div class="grow w-full max-w-full overflow-y-auto font-sans">
      <div class="w-2/3 flex flex-col space-y-1 rounded-xl bg-base-200">
        <h2 class="p-2 text-xl font-bold">{stopset.name}</h2>
        {#each assets as {rotator, asset}}
          <div
            class="p-2 rounded-xl"
            style:background-color={getColor(rotator.color)}
            style:color={getColor(rotator.color, 'content')}
          >
            <h3 class="font-bold">{rotator.name}</h3>
            <div>
              {#if asset}
                {asset.name}
                [{#if asset.duration.asSeconds() >= 3600}{Math.floor(asset.duration.asHours())}:{/if}{asset.duration.format('mm:ss')}]
              {:else}
                No asset in this rotator
              {/if}
            </div>
          </div>
        {/each}
      </div>
    </div>
  {:else}
    <span>No stopset generated!</span>
  {/if}
</div>
