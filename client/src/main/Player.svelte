<script>
  import { tick } from "svelte"
  import PlayBar from "./player/Bar.svelte"
  import PlayButtons from "./player/Buttons.svelte"
  import PlayList from "./player/List.svelte"

  import { config, userConfig } from "../stores/config"
  import { db } from "../stores/db"
  import { Wait } from "../stores/player"

  // Object automatically updates on change
  let items = []

  const updateUI = () => (items = items) // Callback for force re-render
  const numStopsetsToPreloadAudioFor = 2

  const doneWaiting = () => {
    // true = keep waiting and do overtime stuff
    if ($userConfig.autoplay) {
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

  const addStopset = () => {
    // If previous item is not a wait interval
    let shouldPrependWait = $config.WAIT_INTERVAL > 0 && items.length > 0 && items[items.length - 1].type !== "wait"

    let generatedStopset = $db.generateStopset(null, processItem, updateUI)

    if (generatedStopset) {
      if (shouldPrependWait) {
        items.push(new Wait(doneWaiting, updateUI))
      }
      items.push(generatedStopset)
      if ($config.WAIT_INTERVAL > 0) {
        items.push(new Wait(doneWaiting, updateUI))
      }
    } else {
      console.warn("Couldn't generate a stopset!")
    }
    updateUI()
  }

  const regenerateNextStopset = () => {
    let nextStopset
    for (nextStopset = 1; nextStopset < items.length; nextStopset++) {
      if (items[nextStopset].type === "stopset") {
        break
      }
    }

    if (nextStopset === items.length) {
      console.log("No next stopset found. Adding one instead")
      addStopset()
    } else {
      // swap it out, maintaining generatedId so UI doesn't trigger a transition
      let generatedStopset = $db.generateStopset(null, processItem, updateUI, items[nextStopset].generatedId)
      if (generatedStopset) {
        items[nextStopset].done(true) // Mark swap out one as done
        items[nextStopset] = generatedStopset
        updateUI()
      }
    }
  }

  const skipCurrentStopset = () => {
    items[0].didSkip = true
    processItem()
  }

  const processItem = (index = 1, play = false, subindex) => {
    // TODO: subindex is for advanced mode, playing an asset inside a stopset
    if (index > items.length) {
      console.warn(`Index ${index} out of band while processing items`)
      return
    }
    while (index-- > 0) {
      items.shift().done(true)
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
      console.log("processItem(): playing first stopset")
      nextItem.play()
    }
  }

  const play = (window.play = () => {
    const firstStopsetIndex = items.findIndex((item) => item.type === "stopset")
    if (firstStopsetIndex === -1) {
      throw new Error("play() SHOULD have found a first stopset")
    }
    processItem(firstStopsetIndex, true)
  })

  const pause = () => {
    scrollToTopOfPlaylist()
    items[0].pause()
  }

  const skip = () => {
    scrollToTopOfPlaylist()
    items[0].skip()
  }

  if ($config.WAIT_INTERVAL) {
    items.push(new Wait(doneWaiting, updateUI))
  }

  processItem(0)

  db.subscribe(() => {
    if (items.length === 0) {
      // When we get new data from server, if items is empty, regenerate stopset
      processItem(0)
    }
  })
</script>

<div class="col-span-2 my-8 flex flex-col gap-5">
  {#if items.length > 0}
    {@const item = items[0]}

    <PlayButtons {items} {pause} {play} {skip} {regenerateNextStopset} {skipCurrentStopset} />
    <PlayBar {item} />
  {:else}
    <div class="mt-3 text-center text-3xl italic text-error">
      Can't generate a stopset. You're sure the server has data?
    </div>
  {/if}
</div>

<PlayList {items} />
