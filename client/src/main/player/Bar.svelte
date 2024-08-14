<script>
  import WaveSurfer from "wavesurfer.js"
  import RecordPlugin from "wavesurfer.js/dist/plugins/record.esm.js"
  import { tick } from "svelte"
  import { prettyDuration } from "../../utils"
  import { singlePlayRotators as singlePlay } from "../../stores/single-play-rotators"
  import { userConfig, isDark } from "../../stores/config"
  import { mediaStreamMonitor } from "../../stores/player"

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

  let wavesurfer = null

  const visualize = (el) => {
    wavesurfer = WaveSurfer.create({
      container: el,
      height: "auto",
      cursorWidth: 0,
      normalize: true,
      interact: false,
      barWidth: 4,
      barGap: 3,
      barRadius: 9999,
      barAlign: "bottom"
    })
    let record = wavesurfer.registerPlugin(RecordPlugin.create({ renderRecordedAudio: false }))
    record.renderMicStream(mediaStreamMonitor)
    return {
      destroy() {
        record.stopRecording()
        wavesurfer = record = null
      }
    }
  }
  let defaultWaveColor
  $: {
    $isDark // Color changes on dark mode switch
    defaultWaveColor = `oklch(${getComputedStyle(document.body).getPropertyValue("--bc")})`
  }

  $: if (wavesurfer) {
    let rotator
    if ($singlePlay.playing) {
      rotator = $singlePlay.rotator
    } else if (item.type === "stopset" && item.startedPlaying) {
      rotator = item.items.find((a) => a.active)?.rotator
    }
    wavesurfer.setOptions({ waveColor: rotator?.color?.[$isDark ? "value" : "dark"] ?? defaultWaveColor })
  }
</script>

<div class="flex justify-center">
  <div
    class="truncate font-mono text-2xl font-bold"
    class:animate-pulse={item.overdue}
    style="--pulse-color: var(--er)"
  >
    {#if $singlePlay.playing}
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

<div class="{$userConfig.showViz ? 'mb-3' : 'mb-10'} flex flex-col gap-2">
  <div class="flex items-center gap-2">
    <div class="font-mono">
      {#if $singlePlay.playing}
        {prettyDuration($singlePlay.elapsed, $singlePlay.duration)}
      {:else}
        {prettyDuration(item.elapsed, item.duration)}
      {/if}
    </div>
    {#if item.type === "stopset" || $singlePlay.playing}
      {@const columns = $singlePlay.playing
        ? "1fr"
        : item.playableNonErrorItems.map((item) => `${item.duration}fr`).join(" ")}
      {@const assets = $singlePlay.playing ? [$singlePlay.asset] : item.playableNonErrorItems}
      {@const elapsed = $singlePlay.playing ? $singlePlay.elapsed : item.elapsed}
      {@const duration = $singlePlay.playing ? $singlePlay.duration : item.duration}
      {@const playing = $singlePlay.playing ? true : item.playing}

      <div class="relative flex flex-1">
        <div
          class="relative grid {$userConfig.showViz
            ? 'h-7'
            : 'h-8'} flex-1 gap-1 overflow-hidden rounded-2xl bg-base-300"
          style:grid-template-columns={columns}
        >
          {#each assets as asset}
            {@const rotator = $singlePlay.playing ? $singlePlay.rotator : asset.rotator}
            <div
              class="flex w-full flex-col items-center justify-center overflow-hidden font-mono text-xs leading-none"
              use:hideDurationIfSmall
              style:background-color={rotator.color.value}
              style:color={rotator.color.content}
            >
              {#if !$singlePlay.playing}
                <span>{prettyDuration(asset.duration)}</span>
              {/if}
            </div>
          {/each}
          <div
            class="absolute left-0 z-10 h-full bg-base-100 opacity-40"
            style:width={`${(elapsed / duration) * 100}%`}
          />
          <div
            class="absolute z-20 h-full w-[6px] border-x-[1px] border-base-100 {$isDark
              ? 'bg-white'
              : 'bg-base-content'}"
            class:animate-pulse={!playing}
            style="--pulse-color: var(--bc)"
            style:left={`calc(${(elapsed / duration) * 100}% - 2px)`}
          />
        </div>
      </div>
    {:else if item.type === "wait"}
      <progress
        class="progress {$userConfig.showViz ? 'h-7' : 'h-8'} flex-1"
        value={item.elapsed}
        max={item.duration}
      />
    {/if}
    <div class="font-mono">
      {#if $singlePlay.playing}
        {prettyDuration($singlePlay.duration)}
      {:else}
        {prettyDuration(item.duration)}
      {/if}
    </div>
  </div>

  {#if $userConfig.showViz}
    <div class="mx-5 h-9" use:visualize></div>
  {/if}
</div>
