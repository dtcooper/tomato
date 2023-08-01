<script>
  import { syncProgress as progress } from "../stores/assets"
  import { config } from "../stores/config"

  import autorenewIcon from "../../assets/icons/mdi-autorenew.svg"

  export let title = `Sync'ing with ${$config.STATION_NAME}...`
  export let canDismiss = true
  export let open = true

  const close = () => open = false
</script>

{#if $progress.syncing}
  <svelte:element
    this={canDismiss ? "dialog" : "div"}
    class="modal"
    class:modal-open={!canDismiss} open={canDismiss && open}
  >
    <svelte:element
      this={canDismiss ? "form" : "div"}
      method={canDismiss && "dialog"}
      class="modal-box bg-secondary text-secondary-content flex flex-col items-center justify-center gap-y-2"
    >
      {#if canDismiss}
        <button class="btn btn-sm btn-circle btn-ghost absolute right-2 top-2" on:click={close}>✕</button>
      {/if}
      <!-- TODO: don't use radio progress! -->
      <div class="radial-progress" style="--value: {$progress.percent}">
        {Math.round($progress.percent)}%
      </div>
      <div class="flex items-center gap-x-1">
        <div class="animate-[spin_2s_linear_infinite]">{@html autorenewIcon}</div>
        <h2 class="text-3xl italic">{title}</h2>
      </div>
      <span>Downloading file {$progress.current} of {$progress.total}</span>
      <span class="max-w-md truncate font-mono text-sm">{$progress.item}</span>
    </svelte:element>
    {#if canDismiss}
      <form method="dialog" class="modal-backdrop">
        <button on:click={close}>close</button>
      </form>
    {/if}
  </svelte:element>
{/if}
