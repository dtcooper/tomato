<script>
  import { alerts, dismiss } from "../stores/alerts"

  const classes = {
    // Needs the whole name for tailwind to include them
    warning: "alert-warning",
    error: "alert-error",
    info: "alert-info",
    success: "alert-success"
  }
</script>

{#if $alerts.length > 0}
  <div class="toast z-[10000] items-end">
    {#each $alerts as { msg, level, time }, i}
      <div
        class="alert {classes[level]} w-max max-w-lg animate-pulse"
        style:--pulse-color="var(--{level.substring(0, 2)})"
      >
        <span class="text-wrap">{msg}</span>
        <div>
          <button class="btn btn-neutral btn-sm" tabindex="-1" on:click={() => dismiss(i)}>
            <span>✕</span><span>Dismiss</span>
          </button>
        </div>
      </div>
    {/each}
  </div>
{/if}
