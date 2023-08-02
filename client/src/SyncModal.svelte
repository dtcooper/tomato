<script>
  import { syncProgress as progress } from "./stores/assets"
  import { closeSyncModal, syncModalStore as store } from "./stores/sync-modal"
  import { config } from "./stores/config"

  import autorenewIcon from "../assets/icons/mdi-autorenew.svg"
  import { onDestroy } from "svelte"

  onDestroy(() => {
    // When login sync modal is destroyed, don't show it on recreation
    store.update($store => ({...$store, show: false}))
  })

</script>

{#if $store.show}
  <svelte:element
    this={$store.canDismiss ? "dialog" : "div"}
    class="modal"
    class:modal-open={!$store.canDismiss}
    open={$store.canDismiss}
  >
    <svelte:element
      this={$store.canDismiss ? "form" : "div"}
      method={$store.canDismiss && "dialog"}
      class="modal-box flex flex-col items-center justify-center gap-y-2 bg-secondary text-secondary-content"
    >
      {#if $store.canDismiss}
        <button class="btn btn-circle btn-ghost btn-sm absolute right-2 top-2" on:click|preventDefault={closeSyncModal}>✕</button>
      {/if}
      {#if $progress.syncing }
        <!-- TODO: don't use radio progress! -->
        <div class="radial-progress" style="--value: {$progress.percent}">
          {Math.round($progress.percent)}%
        </div>
        <div class="flex items-center gap-x-1">
          <div class="animate-[spin_2s_linear_infinite]">{@html autorenewIcon}</div>
          <h2 class="text-3xl italic">{$store.title}</h2>
        </div>
        <span>Downloading file {$progress.current} of {$progress.total}</span>
        <span class="max-w-md truncate font-mono text-sm">{$progress.item}</span>
      {:else}
        <h2 class="text-3xl italic">Not currently sync'ing with {$config.STATION_NAME}</h2>
      {/if}
    </svelte:element>
    {#if $store.canDismiss}
      <form method="dialog" class="modal-backdrop">
        <button on:click|preventDefault={closeSyncModal}>close</button>
      </form>
    {/if}
  </svelte:element>
{/if}
