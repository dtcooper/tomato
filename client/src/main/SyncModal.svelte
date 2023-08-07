<script>
  import { syncProgress as progress } from "../stores/db"
  import { conn } from "../stores/connection"
  import { config } from "../stores/config"

  import autorenewIcon from "../../assets/icons/mdi-autorenew.svg"
  import lanConnectIcon from "../../assets/icons/mdi-lan-connect.svg"

  export let show = true
  export let canDismiss = true
  export let title = `Sync status with ${$config.STATION_NAME}...`

  const close = () => show = false
</script>

{#if show}
  <svelte:element
    this={canDismiss ? "dialog" : "div"}
    class="modal bg-black bg-opacity-50"
    class:modal-open={!canDismiss}
    open={canDismiss}
  >
    <svelte:element
      this={canDismiss ? "form" : "div"}
      method={canDismiss && "dialog"}
      class="modal-box max-w-2xl flex flex-col items-center justify-center gap-y-2"
    >
      {#if canDismiss}
        <button class="btn btn-circle btn-ghost btn-sm absolute right-2 top-2" on:click|preventDefault={close}>✕</button>
      {/if}
      <div class="flex items-center gap-x-3">
        <div class:animate-[spin_2s_linear_infinite]={$progress.syncing}>
          {#if $progress.syncing}{@html autorenewIcon}{:else}{@html lanConnectIcon}{/if}
        </div>
        <h2 class="text-3xl">{title}</h2>
      </div>
      {#if $progress.syncing}
        <span>Downloading file {$progress.current} of {$progress.total}</span>
        <progress class="progress progress-primary w-full" value={$progress.percent} max="100"></progress>
        <span class="max-w-md truncate font-mono text-sm">{$progress.item}</span>
      {:else if $conn.connected}
        <h2 class="text-xl italic text-success">You are fully up-to-date with the server!</h2>
      {:else}
        <h2 class="text-xl italic text-error">You are currently disconnected from the server. Tomato is attempting to reconnect.</h2>
      {/if}
    </svelte:element>
    {#if canDismiss}
      <form method="dialog" class="modal-backdrop">
        <button on:click|preventDefault={close}>close</button>
      </form>
    {/if}
  </svelte:element>
{/if}
