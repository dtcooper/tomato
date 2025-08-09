<script>
  import playIcon from "@iconify/icons-mdi/play"
  import pauseIcon from "@iconify/icons-mdi/pause"
  import skipIcon from "@iconify/icons-mdi/skip-next"
  import reloadIcon from "@iconify/icons-mdi/reload"
  import reloadAlertIcon from "@iconify/icons-mdi/reload-alert"

  import Icon from "../../components/Icon.svelte"

  import { fade } from "svelte/transition"
  import { prettyDuration, humanDuration } from "../../utils"
  import { config, userConfig } from "../../stores/config"
  import { singlePlayRotators } from "../../stores/single-play-rotators"

  export let items
  export let addStopset
  export let processItem
  export let pause
  export let skip
  export let regenerateStopsetAsset
  export let showSwapUI
  export let rebalanceWaits

  export let numStopsetsToDisableAddMoreAt

  $: numStopsets = items.reduce((s, item) => s + (item.type === "stopset" ? 1 : 0), 0)
</script>

<!-- col-span-2 until we have a single play rotator player -->
<div
  class="flex h-0 min-h-full flex-col rounded-lg border-base-content bg-base-200 p-1.5 pt-2"
  class:col-span-2={!$singlePlayRotators.enabled}
>
  {#if $singlePlayRotators.enabled}
    <div class="divider m-0 mb-2 font-mono text-sm italic">Playlist</div>
  {/if}
  <div class="flex flex-1 flex-col gap-2 overflow-y-auto" id="playlist" tabindex="-1">
    {#each items as item, index (item.generatedId)}
      {@const isFirstItem = index === 0}
      {@const firstStopsetIndex = items.findIndex((item) => item.type === "stopset")}
      <div class="flex flex-col gap-2 px-2" out:fade={{ duration: 650 }}>
        <div
          class="divider m-0"
          class:text-secondary={item.type === "stopset"}
          class:text-accent={item.type === "wait"}
        >
          <span>
            {item.name}{#if item.duration > 0}<span class="font-mono">[{prettyDuration(item.duration)}]</span>{/if}
          </span>
        </div>
        {#if item.type === "stopset"}
          {#each item.items as asset, subindex}
            {#if asset.playable || $config.WARN_ON_EMPTY_ROTATORS}
              <div
                class="border-l-4 pl-2"
                class:border-error={asset.error || (asset.playable && asset.queueForSkip)}
                class:border-warning={!asset.playable}
                class:border-base-300={asset.playable && !asset.error && asset.finished && !asset.queueForSkip}
                class:border-success={asset.playable && isFirstItem && asset.active}
                class:border-base-content={!isFirstItem ||
                  (asset.playable && !asset.error && !asset.finished && !asset.active)}
              >
                <div
                  class="flex min-h-[4.75rem] items-center gap-3 overflow-hidden px-3 py-1"
                  style={asset.playable && !asset.error && !asset.finished && !asset.queueForSkip
                    ? `background: linear-gradient(to right, color-mix(in oklab, oklch(var(--s)) 90%, black) 0%, color-mix(in oklab, oklch(var(--s)) 90%, black) ${asset.percentDone}%, oklch(var(--s)) ${asset.percentDone}%, oklch(var(--s)) 100%);`
                    : ""}
                  class:text-secondary-content={asset.playable &&
                    !asset.error &&
                    !asset.finished &&
                    !asset.queueForSkip}
                  class:text-error-content={asset.error && !asset.finished}
                  class:bg-error={asset.error && !asset.finished}
                  class:text-warning-content={!asset.playable && !asset.finished}
                  class:bg-warning={!asset.playable && !asset.finished}
                  class:bg-base-300={asset.finished || asset.queueForSkip}
                  class:text-base-content={asset.finished || asset.queueForSkip}
                >
                  {#if $userConfig.uiMode >= 2}
                    <div class="flex items-center">
                      {#if isFirstItem && asset.active && asset.playing}
                        <button class="btn btn-square btn-warning btn-lg" on:click={() => pause()} tabindex="-1">
                          <Icon icon={pauseIcon} class="h-16 w-16" />
                        </button>
                      {:else}
                        <div
                          class:tooltip={(firstStopsetIndex !== index && items[firstStopsetIndex].startedPlaying) ||
                            (asset.afterActive && $userConfig.tooltips && !asset.queueForSkip)}
                          class="tooltip-right tooltip-error flex"
                          data-tip="This action will be logged!"
                        >
                          <button
                            class="btn btn-square btn-success btn-lg"
                            on:click={() => processItem(index, true, subindex)}
                            disabled={!(
                              asset.playable &&
                              !asset.error &&
                              !asset.queueForSkip &&
                              (!isFirstItem || (isFirstItem && (asset.afterActive || (asset.active && !asset.playing))))
                            )}
                            tabindex="-1"
                          >
                            <Icon icon={playIcon} class="h-16 w-16" />
                          </button>
                        </div>
                      {/if}
                    </div>
                  {/if}
                  {#if $userConfig.uiMode > 0}
                    <div
                      class="flex h-[4.75rem] w-[4.75rem] items-center justify-center font-mono text-sm"
                      style="--size: 4.72rem"
                      class:radial-progress={!asset.error &&
                        asset.playable &&
                        item.startedPlaying &&
                        !asset.afterActive}
                      class:italic={asset.error || !asset.playable}
                      class:font-bold={asset.error || !asset.playable}
                      style:--value={(asset.elapsed / asset.duration) * 100}
                      style:--thickness="0.3rem"
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
                  <div class="flex w-0 flex-1 flex-col">
                    <div class="font-sm truncate">
                      <span
                        class="badge select-text border-secondary-content font-medium"
                        style:background-color={asset.color.value}
                        style:color={asset.color.content}
                      >
                        {asset.rotator.name}
                      </span>
                      {#if asset.isAlternate()}
                        <span class="badge badge-warning border-secondary-content font-medium">
                          Alt #{asset.alternateNumber}
                        </span>
                      {/if}
                      {#if asset.isSwapped}
                        <span class="badge badge-warning border-secondary-content font-medium">Swapped</span>
                      {/if}
                      {#if asset.hasEndDateMultiplier}
                        <span class="badge badge-success border-secondary-content font-medium italic tracking-tight">
                          Ends in 24 hours!
                        </span>
                      {/if}
                    </div>
                    <div class="truncate text-xl">
                      {#if asset.playable}
                        {#if asset.error}
                          <span class="font-bold">Error loading:</span>
                        {/if}
                        <span class="select-text">{asset.name}</span>
                      {:else}
                        <span class="text-medium text-base italic">
                          {#if asset.rotator.enabled}
                            Rotator has no eligible assets to chose from! This may be intentional.
                          {:else}
                            Rotator has been disabled.
                          {/if}
                        </span>
                      {/if}
                    </div>
                  </div>
                  {#if !asset.error && asset.playable}
                    <div class="flex flex-col items-end gap-1 self-stretch">
                      <div class="font-mono text-sm">
                        {#if $userConfig.uiMode >= 1}
                          {prettyDuration(asset.elapsed, asset.duration)} /
                        {:else}
                          Length:
                        {/if}
                        <span class="select-text">{prettyDuration(asset.duration)}</span>
                      </div>
                      {#if $userConfig.uiMode >= 2}
                        {@const canRegenerateOrSwap = !(
                          asset.queueForSkip ||
                          (asset.active && asset.playing) ||
                          (isFirstItem && !asset.afterActive && item.startedPlaying)
                        )}
                        <button
                          class="btn btn-info btn-xs gap-0.5 pl-0.5 pr-1.5"
                          disabled={!canRegenerateOrSwap}
                          on:click={() => regenerateStopsetAsset(index, subindex)}
                          tabindex="-1"
                        >
                          <Icon icon={reloadIcon} class="h-4 w-4" />
                          Regenerate
                        </button>

                        <div class="flex gap-1">
                          <button
                            disabled={!canRegenerateOrSwap}
                            class="btn btn-warning btn-xs gap-0.5 pl-0.5 pr-1.5"
                            tabindex="-1"
                            on:click={() => showSwapUI(index, subindex)}
                            ><Icon icon={reloadAlertIcon} class="h-4 w-4" />Swap</button
                          >
                          <div
                            class:tooltip={!asset.queueForSkip &&
                              !(item.startedPlaying && !asset.active && !asset.afterActive) &&
                              $userConfig.tooltips}
                            class="tooltip-left tooltip-error flex"
                            data-tip="This action will be logged!"
                          >
                            <button
                              class="btn btn-xs {asset.queueForSkip
                                ? 'btn-neutral'
                                : 'btn-error'} gap-0.5 pl-0.5 pr-1.5"
                              disabled={item.startedPlaying && !asset.active && !asset.afterActive}
                              tabindex="-1"
                              on:click={() => {
                                if (item.startedPlaying && asset.active) {
                                  skip() // Skip as usual if item is active
                                } else {
                                  asset.queueForSkip = !asset.queueForSkip
                                  rebalanceWaits()
                                }
                              }}
                              ><Icon
                                icon={asset.queueForSkip ? playIcon : skipIcon}
                                class="h-4 w-4"
                              />{asset.queueForSkip ? "Queue" : "Skip"}</button
                            >
                          </div>
                        </div>
                      {/if}
                    </div>
                  {/if}
                </div>
              </div>
            {/if}
          {/each}
          {#if item.items.length === 0 || (!$config.WARN_ON_EMPTY_ROTATORS && item.items.every((asset) => !asset.playable))}
            <div class="border-l-4 border-warning pl-2">
              <div
                class="flex min-h-[4.75rem] items-center gap-3 overflow-hidden bg-warning px-3 py-1 text-warning-content"
              >
                <!-- in the place of the radial -->
                {#if $userConfig.uiMode >= 1}
                  <div
                    class="flex h-[4.75rem] w-[4.75rem] items-center justify-center font-mono text-sm font-bold italic"
                  >
                    Warning!
                  </div>
                {/if}
                <div class="flex flex-1 flex-col overflow-x-hidden">
                  <span class="font-medium italic">
                    Stop set {item.name} was generated but has no eligible assets.</span
                  >
                </div>
              </div>
            </div>
          {/if}
        {:else if item.type === "wait"}
          <div class="border-l-4 pl-2" class:border-base-content={!isFirstItem} class:border-success={isFirstItem}>
            <div
              class="flex min-h-[4.75rem] items-center gap-3 overflow-hidden px-3 py-1 text-neutral-content"
              style:background-image={`linear-gradient(to right, color-mix(in oklab, oklch(var(--n)) 90%, black) 0%, color-mix(in oklab, oklch(var(--n)) 90%, black) ${item.percentDone}%, oklch(var(--n)) ${item.percentDone}%, oklch(var(--n)) 100%)`}
            >
              {#if $userConfig.uiMode >= 2}
                <div class="flex items-center">
                  <div
                    class:tooltip={$userConfig.tooltips}
                    class="tooltip-right tooltip-error flex"
                    data-tip="This action will be logged!"
                  >
                    <button
                      class="btn btn-square btn-success btn-lg"
                      disabled={isFirstItem}
                      on:click={() => processItem(index)}
                      tabindex="-1"
                    >
                      <Icon icon={playIcon} class="h-16 w-16" />
                    </button>
                  </div>
                </div>
              {/if}
              {#if $userConfig.uiMode > 0}
                <div
                  class="radial-progress h-[4.75rem] w-[4.75rem] font-mono text-sm"
                  style="--size: 4.72rem"
                  style:--value={(item.elapsed / item.duration) * 100}
                  style:--thickness={item.elapsed === 0 ? "0" : "0.3rem"}
                >
                  {prettyDuration(item.remaining)}
                </div>
              {/if}
              <div class="flex flex-1 flex-col text-xl font-bold">
                <div class:italic={item.overtime}>
                  Wait{item.overtime ? "ed" : ""} for
                  {humanDuration(item.overtime ? item.duration : item.remaining)}{#if isFirstItem}{item.overtime
                      ? "!"
                      : " more..."}{/if}
                </div>
                {#if item.overtime}
                  <div class={item.overdue ? "text-error" : "text-success"}>Play next stop set now!</div>
                {/if}
              </div>
              <div class="flex flex-col items-end self-stretch">
                <div class="font-mono text-sm">
                  {#if $userConfig.uiMode >= 1}
                    {prettyDuration(item.elapsed, item.duration)} /
                  {:else}
                    Length:
                  {/if}
                  {prettyDuration(item.duration)}
                </div>
                {#if item.overtime}
                  <div
                    class:animate-pulse={item.overdue}
                    class="font-mono font-bold text-error"
                    style="--pulse-color: var(--er)"
                  >
                    {prettyDuration(item.overtimeElapsed)} overdue
                  </div>
                {/if}
              </div>
            </div>
          </div>
        {/if}
      </div>
    {:else}
      <div class="border-l-4 border-error pl-2">
        <div class="flex min-h-[4.75rem] items-center gap-3 overflow-hidden bg-error px-3 py-1 text-error-content">
          <!-- in the place of the radial -->
          {#if $userConfig.uiMode >= 1}
            <div class="flex h-[4.75rem] w-[4.75rem] items-center justify-center font-mono text-sm font-bold italic">
              Error!
            </div>
          {/if}
          <div class="flex flex-1 flex-col overflow-x-hidden">
            <span class="font-medium italic">Playlist has no items.</span>
          </div>
        </div>
      </div>
    {/each}
    <div class="flex justify-center pb-1">
      <button
        disabled={numStopsets >= numStopsetsToDisableAddMoreAt}
        class="btn btn-neutral"
        on:click={addStopset}
        tabindex="-1"
      >
        Load another stop set...
      </button>
    </div>
  </div>
</div>
