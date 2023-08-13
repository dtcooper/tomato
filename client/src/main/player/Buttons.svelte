<script>
  import playCircleOutlineIcon from "@iconify/icons-mdi/play-circle-outline"
  import pauseCircleOutlineIcon from "@iconify/icons-mdi/pause-circle-outline"
  import skipNextCircleOutline from "@iconify/icons-mdi/skip-next-circle-outline"
  import skipForwardOutlineIcon from "@iconify/icons-mdi/skip-forward-outline"
  import reloadIcon from "@iconify/icons-mdi/reload"

  import { userConfig } from "../../stores/config"

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
</script>

<svelte:window
  on:keydown={(event) => {
    if (!playDisabled && event.code === "Space") {
      play()
      event.preventDefault()
    }
  }}
/>

<div class="flex items-center justify-center gap-3">
  <button
    class="btn btn-success btn-lg pl-3 font-mono italic"
    disabled={!items.some((item) => item.type === "stopset") || (firstItem.type === "stopset" && firstItem.playing)}
    on:click={play}
    class:tomato-pulse={(firstItem.type === "wait" && firstItem.overtime) ||
      (firstItem.type === "stopset" && !firstItem.playing)}
    style:--pulse-color="var(--su)"
  >
    <Icon icon={playCircleOutlineIcon} class="h-12 w-12" /> Play
  </button>
  {#if $userConfig.uiMode >= 1}
    <button class="btn btn-warning btn-lg pl-3" disabled={pauseDisabled} on:click={pause}>
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
      >
        <Icon icon={skipNextCircleOutline} class="h-12 w-12" /> Skip
      </button>
    </div>
  {/if}
  {#if $userConfig.uiMode >= 2}
    <div class="flex flex-col gap-2">
      <div class="divider my-0 text-sm italic">Stopset Control</div>
      <div class="flex justify-center gap-2">
        <div
          class={firstItem.type === "stopset" && "tooltip tooltip-error tooltip-bottom"}
          data-tip="Warning: this action will be logged!"
        >
          <button
            class="btn btn-error btn-sm pl-0.5"
            disabled={firstItem.type !== "stopset"}
            on:click={skipCurrentStopset}
          >
            <Icon icon={skipForwardOutlineIcon} class="h-6 w-6" /> Skip Current
          </button>
        </div>
        <button class="btn btn-warning btn-sm pl-0.5" on:click={regenerateNextStopset}>
          <Icon icon={reloadIcon} class="h-6 w-6" /> Regenerate Next
        </button>
      </div>
    </div>
  {/if}
</div>
