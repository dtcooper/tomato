<script>
  import { tick } from "svelte"
  import { prettyDuration } from "../../utils"
  import { singlePlayRotators as singlePlay } from "../../stores/single-play-rotators"

  export let item

  const hideDurationIfSmall = async (el) => {
    if (el.firstChild) {
      await tick()
      if (el.clientWidth - el.firstChild.clientWidth - 12 < 0) {
        el.firstChild.remove()
        console.log("Duration for element too big! Hiding.")
      }
    }
  }
</script>

<div class="flex justify-center">
  <div
    class="truncate font-mono text-2xl font-bold"
    class:animate-pulse={item.overdue}
    style="--pulse-color: var(--er)"
  >
    {#if $singlePlay.isPlaying}
      {prettyDuration($singlePlay.remaining)} remaining in
      <span class="select-text italic">{$singlePlay.asset.name}</span>
    {:else if item.type === "wait" && item.overtime}
      {#if item.overdue}
        <span class="italic text-error">
          You are <span class="underline">OVERDUE</span> to play a stop set. Press play now!
        </span>
      {:else}
        <span class="text-success">Play next stop set now</span>
      {/if}
    {:else}
      {prettyDuration(item.remaining)}
      remaining
      {#if item.type === "wait"}
        to wait
      {:else if item.type === "stopset"}
        in stop set
      {/if}
    {/if}
  </div>
</div>

<div class="flex items-center gap-2">
  <div class="font-mono">
    {#if $singlePlay.isPlaying}
      {prettyDuration($singlePlay.elapsed, $singlePlay.duration)}
    {:else}
      {prettyDuration(item.elapsed, item.duration)}
    {/if}
  </div>
  {#if item.type === "stopset" || $singlePlay.isPlaying}
    {@const columns = $singlePlay.isPlaying
      ? "1fr"
      : item.playableNonErrorItems.map((item) => `${item.duration}fr`).join(" ")}
    {@const assets = $singlePlay.isPlaying ? [$singlePlay.asset] : item.playableNonErrorItems}
    {@const elapsed = $singlePlay.isPlaying ? $singlePlay.elapsed : item.elapsed}
    {@const duration = $singlePlay.isPlaying ? $singlePlay.duration : item.duration}
    {@const playing = $singlePlay.isPlaying ? true : item.playing}

    <div class="relative flex flex-1">
      <div
        class="relative grid h-8 flex-1 gap-1 overflow-hidden rounded-2xl bg-base-300"
        style:grid-template-columns={columns}
      >
        {#each assets as asset}
          {@const rotator = $singlePlay.isPlaying ? $singlePlay.rotator : asset.rotator}
          <div
            class="flex w-full flex-col items-center justify-center overflow-hidden font-mono text-xs leading-none"
            use:hideDurationIfSmall
            style:background-color={rotator.color.value}
            style:color={rotator.color.content}
          >
            {#if !$singlePlay.isPlaying}
              <span>{prettyDuration(asset.duration)}</span>
            {/if}
          </div>
        {/each}
        <div
          class="absolute left-0 z-10 h-full bg-base-100 opacity-40"
          style:width={`${(elapsed / duration) * 100}%`}
        />
        <div
          class="absolute z-20 h-full w-[6px] border-x-[1px] border-base-100 bg-playhead"
          class:animate-pulse={!playing}
          style="--pulse-color: var(--bc)"
          style:left={`calc(${(elapsed / duration) * 100}% - 2px)`}
        />
      </div>
    </div>
  {:else if item.type === "wait"}
    <progress class="progress h-8 flex-1" value={item.elapsed} max={item.duration} />
  {/if}
  <div class="font-mono">
    {#if $singlePlay.isPlaying}
      {prettyDuration($singlePlay.duration)}
    {:else}
      {prettyDuration(item.duration)}
    {/if}
  </div>
</div>
