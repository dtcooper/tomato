<script>
  import dayjs from "dayjs"
  import { tick } from "svelte"
  import PlayBar from "./player/Bar.svelte"
  import PlayButtons from "./player/Buttons.svelte"
  import PlayList from "./player/List.svelte"
  import SinglePlayRotators from "./player/SinglePlayRotators.svelte"

  import { IS_DEV } from "../utils"
  import { reloadPlaylistCallback } from "../stores/connection"
  import { config, userConfig } from "../stores/config"
  import { singlePlayRotators, stop as stopSinglePlayRotator } from "../stores/single-play-rotators"
  import { db } from "../stores/db"
  import { log } from "../stores/client-logs"
  import { Wait } from "../stores/player"
  import { setLED, LED_OFF } from "../stores/midi"

  // Object automatically updates on change
  let items = []

  // Medium ignored assets (everything at exists on the screen right now in items list)
  let mediumIgnoreIds = new Set()

  const updateUI = () => {
    mediumIgnoreIds = new Set(
      items
        .filter((i) => i.type === "stopset")
        .map((s) => s.items.map((a) => a.id))
        .flat(1)
    )
    items = items // Callback for force re-render
  }

  // These numbers set arbitrarily to fit use case
  const numStopsetsToPreloadAudioFor = 3
  const numExtraStopsetsToDisableAddMoreAt = 3

  export let overdue
  $: overdue = items.length > 0 && items[0].type === "wait" && items[0].overdue
  $: overtime = items.length > 0 && items[0].type === "wait" && items[0].overtime

  $: if (items.length === 0) {
    setLED(LED_OFF)
  }

  const doneWaiting = () => {
    // return true = keep waiting and do overtime stuff
    if ($userConfig.autoplay || items.length < 2 || items[1].type !== "stopset") {
      // Continue processing, if autoplay is on, if next time doesn't exist or isn't a stopset
      processItem()
      return false
    } else {
      return true
    }
  }

  const scrollToTopOfPlaylist = async () => {
    await tick()
    document.getElementById("playlist").scroll({ top: 0, behavior: "smooth" })
  }

  const generateStopsetHelper = (likelyPlayTime, generatedId) => {
    return $db.generateStopset(
      likelyPlayTime,
      mediumIgnoreIds,
      $config.END_DATE_PRIORITY_WEIGHT_MULTIPLIER,
      processItem,
      updateUI,
      generatedId
    )
  }

  const addStopset = () => {
    // Prepend a full wait interval IF:
    // There's nothing in the items list, or the previous item is a stopset
    // Happens on app start, and when a wait interval is skipped or enabled (having previously been 0)
    const prependWait = $config.WAIT_INTERVAL > 0 && (items.length === 0 || items[items.length - 1].type === "stopset")

    const secondsUntilPlay = items.reduce((s, item) => s + item.remaining, 0)
    const likelyPlayTime = dayjs().add(secondsUntilPlay, "seconds")
    let generatedStopset = generateStopsetHelper(likelyPlayTime)

    if (generatedStopset) {
      if (prependWait) {
        items.push(new Wait($config.WAIT_INTERVAL, doneWaiting, updateUI))
      }
      // Always add a stopset AND THEN a wait interval
      items.push(generatedStopset)
      if ($config.WAIT_INTERVAL > 0) {
        let duration = $config.WAIT_INTERVAL
        if ($config.WAIT_INTERVAL_SUBTRACTS_FROM_STOPSET_PLAYTIME) {
          duration = Math.max(
            duration - generatedStopset.duration,
            $config.WAIT_INTERVAL_SUBTRACTS_FROM_STOPSET_PLAYTIME_MIN_LENGTH
          )
        }
        if (duration > 0) {
          items.push(new Wait(duration, doneWaiting, updateUI))
        }
      }
    } else {
      console.warn("Couldn't generate a stopset!")
    }
    updateUI()
  }

  const reloadPlaylist = () => {
    while (items.length > 1) {
      const item = items.pop()
      // Skip all callbacks and logging
      item.done(true, true)
    }
    updateUI()

    // Regenerate stopsets
    let numStopsetsToAdd = Math.max($config.STOPSET_PRELOAD_COUNT, 1)
    // If current item is a stopset
    if (items.length === 1 && items[0].type === "stopset") {
      const item = items[0]
      // If it's playing, generate one less than needed
      if (item.startedPlaying) {
        numStopsetsToAdd--
      } else {
        // If it's not playing, remove it
        items.pop()
        item.done(true, true)
      }
    }

    while (numStopsetsToAdd-- > 0) {
      addStopset()
    }
  }

  $reloadPlaylistCallback = reloadPlaylist

  const regenerateNextStopset = () => {
    let nextStopset
    for (nextStopset = 0; nextStopset < items.length; nextStopset++) {
      // Find the first non-playing stopset
      if (items[nextStopset].type === "stopset" && !items[nextStopset].startedPlaying) {
        break
      }
    }

    if (nextStopset === items.length) {
      console.log("No next stopset found. Adding one instead")
      addStopset()
    } else {
      // swap it out, maintaining generatedId so UI doesn't trigger a transition
      const secondsUntilPlay = items.slice(0, nextStopset).reduce((s, item) => s + item.remaining, 0)
      const likelyPlayTime = dayjs().add(secondsUntilPlay, "seconds")
      let generatedStopset = generateStopsetHelper(likelyPlayTime, items[nextStopset].generatedId)
      if (generatedStopset) {
        generatedStopset.loadAudio()
        items[nextStopset].done(true, true) // Mark swap out one as done and don't log
        items[nextStopset] = generatedStopset
        updateUI()
      }
    }
  }

  const regenerateStopsetItem = (window.regen = (index, subindex) => {
    const stopset = items[index]
    if (stopset.type === "stopset") {
      const secondsUntilPlay = items.slice(0, index).reduce((s, item) => s + item.remaining, 0)
      const likelyPlayTime = dayjs().add(secondsUntilPlay, "seconds")
      stopset.regenerateItem(subindex, likelyPlayTime, mediumIgnoreIds, $config.END_DATE_PRIORITY_WEIGHT_MULTIPLIER)
    } else {
      console.warn(`Item at index ${index} is not a stopset. Can't regenerate!`)
    }
    updateUI()
  })

  const skipCurrentStopset = () => {
    items[0].didSkip = true
    processItem()
  }

  const processItem = async (index = 1, play = false, subindex = null) => {
    await tick() // Wait one tick for finished assets / waits to go black

    // TODO:  = null is for advanced mode, playing an asset inside a stopset
    if (index > items.length) {
      console.warn(`Index ${index} out of band while processing items`)
      return
    }
    for (let i = index; i >= 1; i--) {
      // skip callback (first arg) AND skip logs except for first one (second arg)
      // third arg == consider it a "skipped" stopset
      items.shift().done(true, i !== index, true)
    }

    scrollToTopOfPlaylist()

    let numStopsetsToAdd =
      Math.max($config.STOPSET_PRELOAD_COUNT, 1) - items.filter((item) => item.type === "stopset").length
    while (numStopsetsToAdd-- > 0) {
      addStopset()
    }

    if (items.length === 0) {
      console.warn("No items to process")
      return
    }

    // Preload first few
    items
      .filter((item) => item.type === "stopset")
      .slice(0, numStopsetsToPreloadAudioFor)
      .forEach((item) => item.loadAudio())

    const nextItem = items[0]
    if (nextItem.type === "wait") {
      nextItem.run()
    } else if (nextItem.type === "stopset" && (play || (IS_DEV && $userConfig.autoplay))) {
      stopSinglePlayRotator()
      nextItem.play(subindex)
    }
  }

  const play = () => {
    const firstStopsetIndex = items.findIndex((item) => item.type === "stopset")
    if (firstStopsetIndex === -1) {
      throw new Error("play() SHOULD have found a first stopset")
    }
    processItem(firstStopsetIndex, true)
  }

  const pause = () => {
    scrollToTopOfPlaylist()
    items[0].pause()
  }

  const skip = () => {
    scrollToTopOfPlaylist()
    stopSinglePlayRotator()
    items[0].skip()
  }

  db.subscribe(() => {
    // Runs on first load as well
    if (items.length === 0) {
      // When we get new data from server, if items is empty, regenerate stopset
      processItem(0)
    }
  })
</script>

<div class="col-span-2 mb-5 mt-7 flex flex-col gap-5">
  {#if items.length > 0}
    {@const item = items[0]}

    <PlayButtons
      {items}
      {pause}
      {play}
      {skip}
      {regenerateNextStopset}
      {reloadPlaylist}
      {skipCurrentStopset}
      {overdue}
      {overtime}
    />
    <PlayBar {item} />
  {:else}
    <div class="mt-3 text-center text-xl italic text-error">
      Can't generate a stopset. You're sure the server has data that's set to air now?
    </div>
  {/if}
</div>

<PlayList
  {items}
  numStopsetsToDisableAddMoreAt={$config.STOPSET_PRELOAD_COUNT + numExtraStopsetsToDisableAddMoreAt}
  {addStopset}
  {processItem}
  {regenerateStopsetItem}
  {pause}
  {skip}
/>

{#if $singlePlayRotators.enabled}
  <SinglePlayRotators playlistItems={items} {mediumIgnoreIds} />
{/if}
