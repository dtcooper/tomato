<script>
  import { fade } from "svelte/transition"
  import { prettyDuration, humanDuration } from "../../utils"

  export let items
</script>

<!-- col-span-2 until we have a single play rotator player -->
<div class="col-span-2 flex h-0 min-h-full flex-col gap-2 border-base-content">
  <div class="divider my-0 text-sm font-bold text-primary">Playlist</div>
  <div class="flex flex-1 flex-col overflow-y-auto" id="playlist">
    {#each items as item, index (item.generatedId)}
      {@const isFirstItem = index === 0}
      <div class="flex flex-col gap-2 px-2" out:fade={{ duration: 250 }}>
        <div
          class="divider mb-0 mt-2 italic"
          class:text-secondary={item.type === "stopset"}
          class:text-accent={item.type === "wait"}
        >
          {item.name} ({item.generatedId})
        </div>
        {#if item.type === "stopset"}
          {#each item.items as asset}
            {@const rightColor = asset.color.value}
            {@const leftColor = asset.color.dark}
            <div
              class="border-l-4 pl-2"
              class:border-base-300={asset.finished}
              class:border-success={isFirstItem && asset.active}
              class:border-base-content={!isFirstItem || (!asset.finished && !asset.active)}
            >
              <div
                class="flex items-center gap-3 overflow-hidden bg-clip-text px-3 py-1"
                style={asset.finished
                  ? ""
                  : `color: ${asset.color.content}; background: linear-gradient(to right, ${leftColor} 0%, ${leftColor} ${asset.percentDone}%, ${rightColor} ${asset.percentDone}%, ${rightColor} 100%);`}
                class:bg-base-300={asset.finished}
                class:text-base-content={asset.finished}
              >
                <div
                  class="radial-progress h-20 w-20 font-mono text-sm"
                  style:--value={(asset.elapsed / asset.duration) * 100}
                  style:--thickness={asset.elapsed === 0 ? "0" : "0.4rem"}
                >
                  {prettyDuration(asset.remaining)}
                </div>
                <div class="flex flex-1 flex-col overflow-hidden">
                  <div class="truncate text-xl">{asset.name}</div>
                  <div class="font-sm truncate font-mono font-bold">{asset.rotator.name}</div>
                </div>
                <div class="self-start font-mono text-sm">
                  {prettyDuration(asset.elapsed, asset.duration)} / {prettyDuration(asset.duration)}
                </div>
              </div>
            </div>
          {/each}
        {:else if item.type === "wait"}
          <!-- wonky because items being identical? -->
          <div class="border-l-4 pl-2" class:border-base-content={!isFirstItem} class:border-success={isFirstItem}>
            <div
              class="flex items-center gap-3 overflow-hidden px-3 py-1"
              style:background-image={`linear-gradient(to right, hsl(var(--b3)) 0%, hsl(var(--b3)) ${item.percentDone}%, hsl(var(--b2)) ${item.percentDone}%, hsl(var(--b2)) 100%)`}
            >
              <div
                class="radial-progress h-20 w-20 font-mono text-sm"
                style:--value={(item.elapsed / item.duration) * 100}
                style:--thickness={item.elapsed === 0 ? "0" : "0.4rem"}
              >
                {prettyDuration(item.remaining)}
              </div>
              <div class="flex flex-1 flex-col text-xl font-bold">
                <div class:italic={item.overtime}>
                  Wait{item.overtime ? "ed" : ""} for {humanDuration(item.duration)}{item.overtime ? "!" : ""}
                </div>
                {#if item.overtime}
                  <div class="animate-pulse text-success">Play next stop set now!</div>
                {/if}
              </div>
              <div class="flex flex-col self-start font-mono text-sm">
                <div>{prettyDuration(item.elapsed, item.duration)} / {prettyDuration(item.duration)}</div>
                {#if item.overtime}
                  <div class="animate-pulse font-bold text-error">{prettyDuration(item.overtimeElapsed)} overdue</div>
                  {item.overdue}
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
