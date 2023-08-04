<script>
  import { syncProgress as progress } from "../stores/assets"
  import { config } from "../stores/config"

  import autorenewIcon from "../../assets/icons/mdi-autorenew.svg"
  import checkNetworkOutlineIcon from "../../assets/icons/mdi-check-network-outline.svg"

  export let show = true
  export let canDismiss = true
  export let title = `Sync'ing with ${$config.STATION_NAME}...`

  const close = () => show = false
</script>

{#if show}
  <svelte:element
    this={canDismiss ? "dialog" : "div"}
    class="modal"
    class:modal-open={!canDismiss}
    open={canDismiss}
  >
    <svelte:element
      this={canDismiss ? "form" : "div"}
      method={canDismiss && "dialog"}
      class="modal-box flex flex-col items-center justify-center gap-y-2 bg-secondary text-secondary-content"
    >
      {#if canDismiss}
        <button class="btn btn-circle btn-ghost btn-sm absolute right-2 top-2" on:click|preventDefault={close}>✕</button>
      {/if}
      <div class="flex items-center gap-x-1">
        <div class:animate-[spin_2s_linear_infinite]={$progress.syncing}>
          {#if $progress.syncing}{@html autorenewIcon}{:else}{@html checkNetworkOutlineIcon}{/if}
        </div>
        <h2 class="text-3xl italic">{title}</h2>
      </div>
      {#if $progress.syncing }
        <span>Downloading file {$progress.current} of {$progress.total}</span>
        <progress class="progress progress-primary w-full" value={$progress.percent} max="100"></progress>
        <span class="max-w-md truncate font-mono text-sm">{$progress.item}</span>
      {:else}
        <h2 class="text-xl italic italic">You are fully up-to-date with the server!</h2>
      {/if}
    </svelte:element>
    {#if canDismiss}
      <form method="dialog" class="modal-backdrop">
        <button on:click|preventDefault={close}>close</button>
      </form>
    {/if}
  </svelte:element>
{/if}
