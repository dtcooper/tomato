<script>
  import { alerts, dismiss } from "../stores/alerts"
</script>

{#if $alerts.length > 0}
  <div class="toast z-[10000] items-end">
    {#each $alerts as { msg, level, time }, i}
      <div
        class="alert alert-{level} w-max max-w-lg animate-pulse"
        style:--pulse-color="var(--{level.substring(0, 2)})"
      >
        <span class="text-wrap">{msg}</span>
        <div><button class="btn btn-neutral" tabindex="-1" on:click={() => dismiss(i)}>Dismiss</button></div>
      </div>
    {/each}
  </div>
{/if}
