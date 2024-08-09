<script>
  import dayjs from "dayjs"

  import { tick } from "svelte"
  import AssetSwapper from "./player/AssetSwapper.svelte"
  import PlayBar from "./player/Bar.svelte"
  import PlayButtons from "./player/Buttons.svelte"
  import PlayList from "./player/List.svelte"
  import SinglePlayRotators from "./player/SinglePlayRotators.svelte"

  import { IS_DEV } from "../utils"
  import { registerMessageHandler, messageServer, conn } from "../stores/connection"
  import { config, userConfig } from "../stores/config"
  import { singlePlayRotators, stop as stopSinglePlayRotator } from "../stores/single-play-rotators"
  import { db } from "../stores/db"
  import { log } from "../stores/client-logs"
  import { Wait } from "../stores/player"
  import { midiSetLED, LED_OFF } from "../stores/midi"
  import { alert } from "../stores/alerts"

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
    midiSetLED(LED_OFF)
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

  const rebalanceWaits = () => {
    if ($config.WAIT_INTERVAL_SUBTRACTS_FROM_STOPSET_PLAYTIME) {
      // Avoid active waits and the first wait
      for (let i = 1; i < items.length; i++) {
        const stopset = items[i - 1]
        const wait = items[i]
        if (!wait.active && wait.type === "wait" && stopset.type === "stopset") {
          wait.duration = Math.max(
            $config.WAIT_INTERVAL - stopset.remainingAfterQueuedSkips,
            $config.WAIT_INTERVAL_SUBTRACTS_FROM_STOPSET_PLAYTIME_MIN_LENGTH
          )
          updateUI()
        }
      }
    }
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
        items.push(new Wait($config.WAIT_INTERVAL, doneWaiting, updateUI))
      }
      rebalanceWaits()
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

    // Make sure a wait item is running
    if (items.length >= 1 && items[0].type === "wait") {
      items[0].run()
    }
  }

  let subscriptionConnectionId = null
  let subscriptionInterval

  registerMessageHandler("reload-playlist", ({ notify, connection_id }) => {
    console.warn("Received playlist reload from server")
    if (notify) {
      alert("An administrator forced a playlist refresh!", "info", 4000)
    }
    reloadPlaylist()
    if (connection_id) {
      messageServer("ack-action", { connection_id, msg: "Successfully reloaded playlist!" })
    }
  })

  const unsubscribe = () => {
    if (subscriptionConnectionId) {
      if ($conn.connected) {
        messageServer("unsubscribe")
      }
      console.log(`Admin ${subscriptionConnectionId} unsubscribed`)
      clearInterval(subscriptionInterval)
      subscriptionConnectionId = null
    }
  }

  $: if (subscriptionConnectionId && !$conn.connected) {
    console.log("Disconnected while admin was subscribed. Unsubscribing.")
    unsubscribe()
  }

  const sendClientDataToSubscriber = () => {
    if (subscriptionConnectionId) {
      const serialized = items.map((item) => item.serializeForSubscriber())
      messageServer("client-data", { connection_id: subscriptionConnectionId, items: serialized })
    }
  }

  registerMessageHandler("subscribe", ({ connection_id }) => {
    unsubscribe() // Unsubscribe any existing connections
    console.log(`Admin ${connection_id} subscribed`)
    subscriptionConnectionId = connection_id
    sendClientDataToSubscriber()
    subscriptionInterval = setInterval(sendClientDataToSubscriber, 333) // Update 3 times per sec
  })

  registerMessageHandler("unsubscribe", unsubscribe)

  registerMessageHandler("swap", ({ action, asset_id, rotator_id, generated_id, subindex, connection_id }) => {
    const stopset = items.find((item) => item.type === "stopset" && item.generatedId === generated_id)
    if (!stopset) {
      console.warn("An swap action was requested on a stopset that doesn't exist!")
      messageServer("ack-action", { connection_id, msg: `An action was requested on a stopset that doesn't exist!` })
      return
    }

    let success = false
    if (action === "delete") {
      success = stopset.deleteAsset(subindex)
    } else {
      const asset = $db.assets.find((asset) => asset.id === asset_id)
      const rotator = $db.rotators.get(rotator_id)

      if (!asset || !rotator) {
        console.warn("An swap action was requested on an asset/rotator that doesn't exist!")
        messageServer("ack-action", {
          connection_id,
          msg: `An action was requested on a asset/rotator that doesn't exist!`
        })
        return
      }

      if (action === "swap") {
        success = stopset.swapAsset(subindex, asset, rotator)
      } else {
        success = stopset.insertAsset(subindex, asset, rotator, action === "before")
      }
    }

    if (success) {
      rebalanceWaits()
    }

    updateUI()
    messageServer("ack-action", {
      connection_id,
      msg: `${success ? "Successfully performed" : "FAILED to perform"} action of type: ${action}!`
    })
  })

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
        rebalanceWaits()
        updateUI()
      }
    }
  }

  const regenerateStopsetAsset = (index, subindex) => {
    if (index > items.length) {
      console.warn(`Index ${index} out of band while regenerating item`)
      return
    }

    const stopset = items[index]
    if (stopset.type === "stopset") {
      const secondsUntilPlay = items.slice(0, index).reduce((s, item) => s + item.remaining, 0)
      const likelyPlayTime = dayjs().add(secondsUntilPlay, "seconds")
      stopset.regenerateAsset(subindex, likelyPlayTime, mediumIgnoreIds, $config.END_DATE_PRIORITY_WEIGHT_MULTIPLIER)
    } else {
      console.warn(`Item at index ${index} is not a stopset. Can't regenerate!`)
    }
    rebalanceWaits()
    updateUI()
  }

  const skipCurrentStopset = () => {
    items[0].didSkip = true
    processItem()
  }

  let swap = null

  export const showSwapUI = (index, subindex) => {
    if (index > items.length) {
      console.warn(`Index ${index}:${subindex} out of band while showing swap UI`)
      swap = null
      return
    }

    const stopset = items[index]
    if (stopset.type === "stopset" && subindex < stopset.items.length) {
      const asset = stopset.items[subindex]
      swap = { stopset, asset, subindex }
    } else {
      console.warn(`Item at index ${index}:${subindex} is not a stopset/asset. Won't show swap UI`)
      swap = null
    }
  }

  const doAssetSwap = (stopset, subindex, asset, swapAsset) => {
    if (stopset.destroyed) {
      alert(`Stop set ${stopset.name} no longer active in the playlist. Can't perform swap!`, "warning")
    } else {
      if (stopset.swapAsset(subindex, asset, swapAsset.rotator)) {
        rebalanceWaits()
      } else {
        alert(`Asset in stop set ${stopset.name}'s index ${subindex + 1} can no longer be swapped.`, "warning")
      }
      updateUI()
    }
    swap = null
  }

  const processItem = async (index = 1, play = false, subindex = null) => {
    await tick() // Wait one tick for finished assets / waits to go black

    if (index > items.length) {
      console.warn(`Index ${index} out of band while processing items`)
      return
    }

    // If first item is wait, and we skip to another wait, mark next stopset as skipped
    if (index > 0 && index < items.length) {
      const firstItem = items[0]
      const processItem = items[index]

      if (firstItem.type === "wait" && processItem.type === "wait")
        for (let i = 0; i < index; i++) {
          if (items[i].type === "stopset") {
            log("skipped_stopset", `[Stopset=${items[i].name}]`)
            break
          }
        }
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

{#if swap}
  <AssetSwapper {doAssetSwap} bind:swap />
{/if}

<PlayList
  {items}
  numStopsetsToDisableAddMoreAt={$config.STOPSET_PRELOAD_COUNT + numExtraStopsetsToDisableAddMoreAt}
  {addStopset}
  {processItem}
  {regenerateStopsetAsset}
  {rebalanceWaits}
  {showSwapUI}
  {pause}
  {skip}
/>

{#if $singlePlayRotators.enabled}
  <SinglePlayRotators playlistItems={items} {mediumIgnoreIds} />
{/if}
