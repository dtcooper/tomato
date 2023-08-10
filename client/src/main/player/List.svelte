<script>
  import { fade } from "svelte/transition"
  import { prettyDuration, humanDuration } from "../../utils"
  import { config, userConfig } from "../../stores/config"

  export let items
</script>

<!-- col-span-2 until we have a single play rotator player -->
<div class="col-span-2 flex h-0 min-h-full flex-col gap-2 rounded-lg border-base-content bg-base-200 p-1.5">
  <div class="flex flex-1 flex-col overflow-y-auto" id="playlist">
    {#each items as item, index (item.generatedId)}
      {@const isFirstItem = index === 0}
      <div class="flex flex-col gap-2 px-2" out:fade={{ duration: 800 }}>
        <div
          class="divider mb-0 mt-2"
          class:text-secondary={item.type === "stopset"}
          class:text-accent={item.type === "wait"}
        >
          <span>{item.name} <span class="font-mono">[{prettyDuration(item.duration)}]</span></span>
        </div>
        {#if item.type === "stopset"}
          {#each item.items as asset}
            <div
              class="border-l-4 pl-2"
              class:border-base-300={asset.finished}
              class:border-success={isFirstItem && asset.active}
              class:border-base-content={!isFirstItem || (!asset.finished && !asset.active)}
            >
              <div
                class="flex min-h-[5rem] items-center gap-3 overflow-hidden px-3 py-1"
                style={asset.finished
                  ? ""
                  : `background: linear-gradient(to right, hsl(var(--sf)) 0%, hsl(var(--sf)) ${asset.percentDone}%, hsl(var(--s)) ${asset.percentDone}%, hsl(var(--s)) 100%);`}
                class:bg-neutral={asset.finished}
                class:text-secondary-content={!asset.finished}
                class:text-neutral-content={asset.finished}
              >
                {#if $userConfig.uiMode > 0}
                  <div
                    class="h-18 w-18 radial-progress font-mono text-sm"
                    style:--value={(asset.elapsed / asset.duration) * 100}
                    style:--thickness={asset.elapsed === 0 ? "0" : "0.4rem"}
                  >
                    {prettyDuration(asset.remaining)}
                  </div>
                {/if}
                <div class="flex flex-1 flex-col overflow-x-hidden">
                  <div class="font-sm truncate">
                    <span
                      class="badge border-secondary-content font-medium"
                      style:background-color={asset.color.value}
                      style:color={asset.color.content}
                    >
                      {asset.rotator.name}
                    </span>
                  </div>
                  <div class="truncate text-xl">{asset.name}</div>
                </div>
                <div class="self-start font-mono text-sm">
                  {#if $userConfig.uiMode >= 1}
                    {prettyDuration(asset.elapsed, asset.duration)} /
                  {:else}
                    Length:
                  {/if}
                  {prettyDuration(asset.duration)}
                </div>
              </div>
            </div>
          {/each}
        {:else if item.type === "wait"}
          <div class="border-l-4 pl-2" class:border-base-content={!isFirstItem} class:border-success={isFirstItem}>
            <div
              class="flex min-h-[5rem] items-center gap-3 overflow-hidden px-3 py-1 text-neutral-content"
              style:background-image={`linear-gradient(to right, hsl(var(--nf)) 0%, hsl(var(--nf)) ${item.percentDone}%, hsl(var(--n)) ${item.percentDone}%, hsl(var(--n)) 100%)`}
            >
              {#if $userConfig.uiMode > 0}
                <div
                  class="w-18 h-18 radial-progress font-mono text-sm"
                  style:--value={(item.elapsed / item.duration) * 100}
                  style:--thickness={item.elapsed === 0 ? "0" : "0.4rem"}
                >
                  {prettyDuration(item.remaining)}
                </div>
              {/if}
              <div class="flex flex-1 flex-col text-xl font-bold">
                <div class:italic={item.overtime}>
                  Wait{item.overtime ? "ed" : ""} for {humanDuration(item.duration)}{item.overtime ? "!" : ""}
                </div>
                {#if item.overtime}
                  <div class="animate-pulse" class:text-success={!item.overdue} class:text-error={item.overdue}>
                    Play next {$config.STOPSET_ENTITY_NAME} now!
                  </div>
                {/if}
              </div>
              <div class="flex flex-col self-start font-mono text-sm">
                <div class="self-start font-mono text-sm">
                  {#if $userConfig.uiMode >= 1}
                    {prettyDuration(item.elapsed, item.duration)} /
                  {:else}
                    Length:
                  {/if}
                  {prettyDuration(item.duration)}
                </div>
                {#if item.overtime}
                  <div class="animate-pulse font-bold text-error">{prettyDuration(item.overtimeElapsed)} overdue</div>
                {/if}
              </div>
            </div>
          </div>
        {/if}
      </div>
    {:else}
      <div class="font-error italic text-lg">No items in playlist!</div>
    {/each}
    <div class="flex flex-col items-center">Add more</div>
  </div>
</div>
