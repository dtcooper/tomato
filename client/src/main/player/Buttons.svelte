<script>
  import playCircleOutlineIcon from "@iconify/icons-mdi/play-circle-outline"
  import pauseCircleOutlineIcon from "@iconify/icons-mdi/pause-circle-outline"
  import skipNextCircleOutline from "@iconify/icons-mdi/skip-next-circle-outline"
  import skipForwardOutlineIcon from "@iconify/icons-mdi/skip-forward-outline"
  import reloadIcon from "@iconify/icons-mdi/reload"
  import reloadAlertIcon from "@iconify/icons-mdi/reload-alert"

  import { userConfig } from "../../stores/config"
  import { blockSpacebarPlay } from "../../stores/player"
  import { registerMessageHandler, messageServer } from "../../stores/connection"
  import {
    midiSetLED,
    midiButtonPresses,
    LED_OFF,
    LED_ON,
    LED_FLASH,
    LED_PULSATE_SLOW,
    LED_PULSATE_FAST
  } from "../../stores/midi"
  import { debounceFunc } from "../../utils"

  import Icon from "../../components/Icon.svelte"

  export let items
  let firstItem

  export let play
  export let pause
  export let skip
  export let skipCurrentStopset
  export let regenerateNextStopset
  export let reloadPlaylist
  export let overtime
  export let overdue

  $: firstItem = items[0]
  $: playDisabled =
    !items.some((item) => item.type === "stopset") || (firstItem.type === "stopset" && firstItem.playing)
  $: pauseDisabled = firstItem.type !== "stopset" || !firstItem.playing
  $: isPaused = firstItem.type === "stopset" && firstItem.startedPlaying && !firstItem.playing
  $: skipCurrentEnabled = firstItem.type === "stopset" && firstItem.startedPlaying

  let ledState
  $: if (playDisabled) {
    ledState = LED_OFF
  } else if (isPaused) {
    ledState = LED_FLASH
  } else if (overdue) {
    ledState = LED_PULSATE_FAST
  } else if (overtime) {
    ledState = LED_PULSATE_SLOW
  } else {
    ledState = LED_ON
  }

  $: midiSetLED(ledState)
  setTimeout(() => midiSetLED(ledState), 500) // Allow 500ms for midi system to initialize

  // Remove previously installed press listeners (if component was destroyed and re-created)
  midiButtonPresses.removeAllListeners("pressed")

  // Fix weird race condition bug where play() gets called twice in rapid succession when button box
  // is re-initialized
  const playDebounced = debounceFunc(
    () => {
      console.log("Calling play() based on MIDI key press")
      play()
    },
    1,
    250,
    "play"
  )

  midiButtonPresses.addListener("pressed", () => {
    if (playDisabled) {
      console.log("Got MIDI press, but currently not eligible to play!")
    } else {
      playDebounced()
    }
  })

  // registerMessageHandler overwrites previously registered handle when called again (if component re-created)
  registerMessageHandler("play", ({ connection_id }) => {
    if (playDisabled) {
      console.log("Got play message, but currently not eligible to play!")
      messageServer("ack-action", { connection_id, msg: "Got play command, but currently not eligble to play!" })
    } else {
      console.log("Got play command from server")
      messageServer("ack-action", { connection_id, msg: "Successfully started playing!" })
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

<div class="flex items-center justify-center gap-3">
  <button
    class="btn btn-success btn-lg pl-3 font-mono italic"
    disabled={!items.some((item) => item.type === "stopset") || (firstItem.type === "stopset" && firstItem.playing)}
    on:click={play}
    class:animate-pulse={(firstItem.type === "wait" && firstItem.overtime) ||
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
      class:tooltip={firstItem.type === "stopset" && ($userConfig.uiMode <= 1 || $userConfig.tooltips)}
      class="tooltip-bottom tooltip-error flex"
      data-tip="This action will be logged!"
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
  {#if $userConfig.uiMode >= 2}
    <div class="flex flex-col gap-2">
      <div class="divider my-0 text-sm italic">Stop set control</div>
      <div class="grid grid-cols-2 justify-center gap-2 md:flex">
        <div
          class:tooltip={skipCurrentEnabled && $userConfig.tooltips}
          class="tooltip-bottom tooltip-error flex"
          data-tip="This action will be logged!"
        >
          <button
            class="btn btn-error btn-sm w-full pl-1.5"
            disabled={!skipCurrentEnabled}
            on:click={skipCurrentStopset}
            tabindex="-1"
          >
            <Icon icon={skipForwardOutlineIcon} class="h-6 w-6" /> Skip current
          </button>
        </div>
        <button class="btn btn-info btn-sm pl-1.5" on:click={regenerateNextStopset} tabindex="-1">
          <Icon icon={reloadIcon} class="h-6 w-6" /> Regenerate next
        </button>
        <button class="btn btn-warning btn-sm pl-1.5" on:click={reloadPlaylist} tabindex="-1">
          <Icon icon={reloadAlertIcon} class="h-6 w-6" /> Reload playlist
        </button>
      </div>
    </div>
  {/if}
</div>
