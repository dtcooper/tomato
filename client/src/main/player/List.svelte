<script>
  import { fade } from "svelte/transition"
  import { prettyDuration, humanDuration } from "../../utils"
  import { config, userConfig } from "../../stores/config"

  export let items
  export let addStopset

  export let numStopsetsToDisableAddMoreAt

  $: numStopsets = items.reduce((s, item) => s + (item.type === "stopset" ? 1 : 0), 0)
</script>

<!-- col-span-2 until we have a single play rotator player -->
<div class="col-span-2 flex h-0 min-h-full flex-col rounded-lg border-base-content bg-base-200 p-1.5 pt-2">
  <div class="flex flex-1 flex-col gap-2 overflow-y-auto" id="playlist">
    {#each items as item, index (item.generatedId)}
      {@const isFirstItem = index === 0}
      <div class="flex flex-col gap-2 px-2" out:fade={{ duration: 650 }}>
        <div
          class="divider m-0"
          class:text-secondary={item.type === "stopset"}
          class:text-accent={item.type === "wait"}
        >
          <span
            >{item.name}{#if item.duration > 0}
              <span class="font-mono">[{prettyDuration(item.duration)}]</span>{/if}</span
          >
        </div>
        {#if item.type === "stopset"}
          {#each item.items as asset}
            {#if asset.playable || $config.WARN_ON_EMPTY_ROTATORS}
              <div
                class="border-l-4 pl-2"
                class:border-error={asset.error}
                class:border-warning={!asset.playable}
                class:border-base-300={asset.playable && !asset.error && asset.finished}
                class:border-success={asset.playable && isFirstItem && asset.active}
                class:border-base-content={!isFirstItem ||
                  (asset.playable && !asset.error && !asset.finished && !asset.active)}
              >
                <div
                  class="flex min-h-[5rem] items-center gap-3 overflow-hidden px-3 py-1"
                  style={asset.playable && !asset.error && !asset.finished
                    ? `background: linear-gradient(to right, hsl(var(--sf)) 0%, hsl(var(--sf)) ${asset.percentDone}%, hsl(var(--s)) ${asset.percentDone}%, hsl(var(--s)) 100%);`
                    : ""}
                  class:text-secondary-content={asset.playable && !asset.error && !asset.finished}
                  class:text-error-content={asset.error && !asset.finished}
                  class:bg-error={asset.error && !asset.finished}
                  class:text-warning-content={!asset.playable && !asset.finished}
                  class:bg-warning={!asset.playable && !asset.finished}
                  class:bg-base-300={asset.finished}
                  class:text-base-content={asset.finished}
                >
                  {#if $userConfig.uiMode > 0}
                    <div
                      class="flex h-[5rem] w-[5rem] items-center justify-center font-mono text-sm"
                      class:radial-progress={!asset.error &&
                        asset.playable &&
                        item.startedPlaying &&
                        asset.index <= item.current}
                      class:italic={asset.error || !asset.playable}
                      class:font-bold={asset.error || !asset.playable}
                      style:--value={(asset.elapsed / asset.duration) * 100}
                      style:--thickness="0.4rem"
                    >
                      {#if asset.error}
                        Error!
                      {:else if asset.playable}
                        {prettyDuration(asset.remaining)}
                      {:else}
                        Empty!
                      {/if}
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
                    <div class="truncate text-xl">
                      {#if asset.playable}
                        {#if asset.error}
                          <span class="font-bold">Error loading:</span>
                        {/if}
                        {asset.name}
                      {:else}
                        <span class="text-medium text-base italic"
                          >Rotator had no eligible assets to chose from! This may be intentional.</span
                        >
                      {/if}
                    </div>
                  </div>
                  {#if !asset.error && asset.playable}
                    <div class="self-start font-mono text-sm">
                      {#if $userConfig.uiMode >= 1}
                        {prettyDuration(asset.elapsed, asset.duration)} /
                      {:else}
                        Length:
                      {/if}
                      {prettyDuration(asset.duration)}
                    </div>
                  {/if}
                </div>
              </div>
            {/if}
          {/each}
          {#if item.items.length === 0 || (!$config.WARN_ON_EMPTY_ROTATORS && item.items.every((asset) => !asset.playable))}
            <div class="border-l-4 border-warning pl-2">
              <div
                class="flex min-h-[5rem] items-center gap-3 overflow-hidden bg-warning px-3 py-1 text-warning-content"
              >
                <!-- in the place of the radial -->
                {#if $userConfig.uiMode >= 1}
                  <div class="flex h-[5rem] w-[5rem] items-center justify-center font-mono text-sm font-bold italic">
                    Warning!
                  </div>
                {/if}
                <div class="flex flex-1 flex-col overflow-x-hidden">
                  <span class="font-medium italic">
                    {$config.STOPSET_ENTITY_NAME.charAt(0).toUpperCase() + $config.STOPSET_ENTITY_NAME.slice(1)}
                    {item.name} was generated but has no eligible assets.</span
                  >
                </div>
              </div>
            </div>
          {/if}
        {:else if item.type === "wait"}
          <div class="border-l-4 pl-2" class:border-base-content={!isFirstItem} class:border-success={isFirstItem}>
            <div
              class="flex min-h-[5rem] items-center gap-3 overflow-hidden px-3 py-1 text-neutral-content"
              style:background-image={`linear-gradient(to right, hsl(var(--nf)) 0%, hsl(var(--nf)) ${item.percentDone}%, hsl(var(--n)) ${item.percentDone}%, hsl(var(--n)) 100%)`}
            >
              {#if $userConfig.uiMode > 0}
                <div
                  class="radial-progress h-[5rem] w-[5rem] font-mono text-sm"
                  style:--value={(item.elapsed / item.duration) * 100}
                  style:--thickness={item.elapsed === 0 ? "0" : "0.4rem"}
                >
                  {prettyDuration(item.remaining)}
                </div>
              {/if}
              <div class="flex flex-1 flex-col text-xl font-bold">
                <div class:italic={item.overtime}>
                  Wait{item.overtime ? "ed" : ""} for {humanDuration(item.duration)}
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
      <div class="border-l-4 border-error pl-2">
        <div class="flex min-h-[5rem] items-center gap-3 overflow-hidden bg-error px-3 py-1 text-error-content">
          <!-- in the place of the radial -->
          {#if $userConfig.uiMode >= 1}
            <div class="flex h-[5rem] w-[5rem] items-center justify-center font-mono text-sm font-bold italic">
              Error!
            </div>
          {/if}
          <div class="flex flex-1 flex-col overflow-x-hidden">
            <span class="font-medium italic">Playlist has no items.</span>
          </div>
        </div>
      </div>
    {/each}
    <div class="flex justify-center">
      <button disabled={numStopsets >= numStopsetsToDisableAddMoreAt} class="btn btn-neutral" on:click={addStopset}>
        Load another {$config.STOPSET_ENTITY_NAME}...
      </button>
    </div>
  </div>
</div>
