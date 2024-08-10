<script>
  import { alerts, dismiss } from "../stores/alerts"

  const classes = {
    // Needs the whole name for tailwind to include them
    warning: "bg-warning text-warning-content",
    error: "bg-error text-error-content",
    info: "bg-info text-info-content",
    success: "bg-success text-success-content"
  }
</script>

{#if $alerts.length > 0}
  <div class="pointer-events-none absolute z-30 flex h-screen w-screen justify-end">
    <div class="relative flex h-screen max-w-lg flex-col-reverse items-end gap-1 overflow-hidden p-1.5 md:max-w-[60%]">
      {#each $alerts as { msg, level, html }, i}
        <div
          class="pointer-events-auto flex h-fit max-h-[20%] w-fit min-w-[35%] max-w-lg animate-pulse rounded-xl border-2 border-neutral md:max-w-full {classes[
            level
          ]}"
          style:--pulse-color="var(--{level.substring(0, 2)})"
        >
          <div class="m-0 flex flex-1 items-center gap-2 p-2 md:p-3">
            <div class="max-h-full flex-1 overflow-y-auto overflow-x-clip break-all md:text-lg">
              {#if html}
                {@html msg}
              {:else}
                {msg}
              {/if}
            </div>
            <div>
              <button class="btn btn-neutral btn-sm w-max md:btn-md" tabindex="-1" on:click={() => dismiss(i)}>
                <span>✕</span> <span>Dismiss</span>
              </button>
            </div>
          </div>
        </div>
      {/each}
    </div>
  </div>
{/if}
