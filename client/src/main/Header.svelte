<script>
  import tomatoIcon from "../../assets/icons/tomato.svg"
  import lanConnectIcon from "../../assets/icons/mdi-lan-connect.svg"
  import lanDisonnectIcon from "../../assets/icons/mdi-lan-disconnect.svg"
  import autorenewIcon from "../../assets/icons/mdi-autorenew.svg"
  import cogOutline from "../../assets/icons/mdi-cog-outline.svg"
  import { conn } from "../stores/connection"
  import { config, userConfig } from "../stores/config"
  import { syncProgress } from "../stores/db"

  export let showSyncModal = false
  export let showSettingsModal = false
</script>

<div class="col-span-3 flex flex-col gap-6">
  <div class="py-2 px-5 flex bg-base-200 justify-between items-center">
    <div class="text-3xl flex items-center gap-2 tomato">
      {@html tomatoIcon}
      {$config.STATION_NAME}
    </div>
    <div class="icons flex items-center gap-3">
      {#if $userConfig.uiMode >= 1}
        <button class="btn btn-secondary" on:click={() => $userConfig.uiMode = 0}>← Back to simple view</button>
      {/if}
      <button
        class="btn btn-circle btn-ghost"
        class:text-error={!$conn.connected}
        class:text-success={$conn.connected && !$syncProgress.syncing}
        class:text-info={$conn.connected && $syncProgress.syncing}
        on:click={() => showSyncModal = true}
      >
        {#if !$conn.connected}
          {@html lanDisonnectIcon}
        {:else if $syncProgress.syncing}
          {@html autorenewIcon}
        {:else}
          {@html lanConnectIcon}
        {/if}
      </button>
      <button class="btn btn-circle btn-ghost" on:click={() => showSettingsModal = true}>
        {@html cogOutline}
      </button>
    </div>
  </div>
</div>

<style lang="postcss">
  .tomato > :global(svg) {
    @apply h-12 w-12;
  }
  .icons :global(svg) {
    @apply h-8 w-8;
  }
</style>
