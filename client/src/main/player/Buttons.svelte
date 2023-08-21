<script>
  import { ipcRenderer } from "electron"

  import pauseCircleOutlineIcon from "@iconify/icons-mdi/pause-circle-outline"
  import playCircleOutlineIcon from "@iconify/icons-mdi/play-circle-outline"
  import reloadIcon from "@iconify/icons-mdi/reload"
  import skipForwardOutlineIcon from "@iconify/icons-mdi/skip-forward-outline"
  import skipNextCircleOutline from "@iconify/icons-mdi/skip-next-circle-outline"
  import stopCircleOutline from "@iconify/icons-mdi/stop-circle-outline"

  import { userConfig } from "../../stores/config"
  import { blockSpacebarPlay } from "../../stores/player"
  import { singlePlayRotators, stop as stopSinglePlayRotator } from "../../stores/single-play-rotators"

  import Icon from "../../components/Icon.svelte"

  export let items
  let firstItem

  export let play
  export let pause
  export let skip
  export let skipCurrentStopset
  export let regenerateNextStopset

  $: firstItem = items[0]
  $: playDisabled =
    !items.some((item) => item.type === "stopset") || (firstItem.type === "stopset" && firstItem.playing)
  $: pauseDisabled = firstItem.type !== "stopset" || !firstItem.playing

  ipcRenderer.on("play-server-cmd-play", (...args) => {
    if (playDisabled) {
      console.log("Got command from play server, but currently not eligible to play!")
    } else {
      console.log("Calling play() based on command from play server")
      play()
    }
  })
</script>

<svelte:window
  on:keydown={(event) => {
    if (!playDisabled && !$blockSpacebarPlay && event.code === "Space") {
      play()
      event.preventDefault()
    }
  }}
/>

<div class="flex items-center justify-center gap-2">
  <div class="flex flex-col gap-2">
    {#if $userConfig.uiMode > 0}
      <div class="divider my-0 w-full text-sm italic">Playlist control</div>
    {/if}
    <div class="flex justify-center gap-2">
      <button
        class="btn btn-success btn-lg pl-3 font-mono italic"
        disabled={!items.some((item) => item.type === "stopset") || (firstItem.type === "stopset" && firstItem.playing)}
        on:click={play}
        class:tomato-pulse={(firstItem.type === "wait" && firstItem.overtime) ||
          (firstItem.type === "stopset" && !firstItem.playing)}
        tabindex="-1"
      >
        <Icon icon={playCircleOutlineIcon} class="h-12 w-12" /> Play
      </button>
      {#if $userConfig.uiMode >= 1}
        <button class="btn btn-warning btn-lg pl-3" disabled={pauseDisabled} on:click={pause} tabindex="-1">
          <Icon icon={pauseCircleOutlineIcon} class="h-12 w-12" /> Pause
        </button>
        <div
          class={firstItem.type === "stopset" && "tooltip tooltip-error tooltip-bottom"}
          data-tip="Warning: this action will be logged!"
        >
          <button
            class="btn btn-error btn-lg pl-3"
            disabled={firstItem.type !== "stopset" || !firstItem.startedPlaying}
            on:click={skip}
            tabindex="-1"
          >
            <Icon icon={skipNextCircleOutline} class="h-12 w-12" /> Skip
          </button>
        </div>
      {/if}
    </div>
  </div>
  {#if $userConfig.uiMode >= 2 || $singlePlayRotators.enabled}
    <div class="flex flex-col gap-2">
      {#if $userConfig.uiMode >= 2}
        <div class="divider my-0 text-sm italic">Stop set control</div>
        <div class="flex justify-center gap-2">
          <div
            class={firstItem.type === "stopset" && "tooltip tooltip-error tooltip-bottom"}
            data-tip="Warning: this action will be logged!"
          >
            <button
              class="btn btn-error btn-sm"
              disabled={firstItem.type !== "stopset"}
              on:click={skipCurrentStopset}
              tabindex="-1"
            >
              <Icon icon={skipForwardOutlineIcon} class="h-6 w-6" /> Skip current
            </button>
          </div>
          <button class="btn btn-warning btn-sm" on:click={regenerateNextStopset} tabindex="-1">
            <Icon icon={reloadIcon} class="h-6 w-6" /> Regenerate next
          </button>
        </div>
      {/if}
      {#if $singlePlayRotators.enabled}
        <div class="divider my-0 text-sm italic">Single play control</div>
        <div class="flex justify-center gap-2">
          <button
            class="btn btn-error"
            class:btn-sm={$userConfig.uiMode === 2}
            class:btn-lg={$userConfig.uiMode === 1}
            class:pl-4={$userConfig.uiMode === 1}
            on:click={() => stopSinglePlayRotator()}
            tabindex="-1"
            disabled={!$singlePlayRotators.isPlaying}
          >
            <Icon icon={stopCircleOutline} class={$userConfig.uiMode === 2 ? "h-6 w-6" : "h-12 w-12"} /> Stop
          </button>
        </div>
      {/if}
    </div>
  {/if}
</div>
