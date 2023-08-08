<script>
  import Icon from "../components/Icon.svelte"

  import { tomatoIcon } from "../utils"
  import lanConnect from "@iconify/icons-mdi/lan-connect"
  import lanDisconnect from "@iconify/icons-mdi/lan-disconnect"
  import autorenew from "@iconify/icons-mdi/autorenew"
  import cogOutline from "@iconify/icons-mdi/cog-outline"
  import { conn } from "../stores/connection"
  import { config, userConfig } from "../stores/config"
  import { syncProgress } from "../stores/db"

  export let showSyncModal = false
  export let showSettingsModal = false
</script>

<div class="col-span-3 flex flex-col gap-6">
  <div class="flex items-center justify-between bg-base-200 px-5 py-2">
    <div class="flex items-center gap-3 text-3xl">
      <Icon icon={tomatoIcon} class="h-12 w-12" shape-rendering="crispEdges" viewBox="0 -.5 16 16" />
      {$config.STATION_NAME}
    </div>
    <div class="flex items-center gap-3">
      {#if $userConfig.uiMode >= 1}
        <button class="btn btn-secondary" on:click={() => ($userConfig.uiMode = 0)}>← Back to simple view</button>
      {/if}
      <button
        class="btn btn-circle btn-ghost flex items-center justify-center overflow-hidden"
        on:click={() => (showSyncModal = true)}
        class:!bg-transparent={$userConfig.uiMode === 0}
        disabled={$userConfig.uiMode === 0}
      >
        {#if !$conn.connected}
          <Icon icon={lanDisconnect} class="h-8 w-8 text-error" />
        {:else if $syncProgress.syncing}
          <Icon icon={autorenew} class="h-8 w-8 animate-[spin_2s_linear_infinite] text-info" />
        {:else}
          <Icon icon={lanConnect} class="h-8 w-8 text-success" />
        {/if}
      </button>
      <button class="btn btn-circle btn-ghost" on:click={() => (showSettingsModal = true)}>
        <Icon icon={cogOutline} class="h-8 w-8" />
      </button>
    </div>
  </div>
</div>