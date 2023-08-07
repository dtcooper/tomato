<script>
  import dayjs from "dayjs"

  import PlayBar from "./player/PlayBar.svelte"

  import { prettyDuration } from "../utils"
  import { config, userConfig } from "../stores/config"
  import { db } from "../stores/db"

  // Object automatically updates on change
  let items = []
  const updateUI = () => (items = items) // Callback for force re-render

  if ($config.WAIT_INTERVAL) {
    items.push({ type: "wait", duration: $config.WAIT_INTERVAL, elapsed: 0, expires: null })
  }

  const hasOneStopset = () => items.some((item) => item.type === "stopset")
  const addStopset = () => {
    let wait = null
    // If previous item is not a wait interval
    if ($config.WAIT_INTERVAL && items.length > 0 && items[items.length - 1].type !== "wait") {
      wait = { type: "wait", duration: $config.WAIT_INTERVAL, elapsed: 0, expires: null }
    }

    let generatedStopset = $db.generateStopset(null, () => console.log("executed done callback!"), updateUI)

    if (generatedStopset) {
      // If it's the only stopset, process it
      if (!hasOneStopset()) {
        generatedStopset.loadAudio() // Preload audio
        //generatedStopset.play()
      }
      if (wait) {
        items.push(wait)
      }
      items.push({ type: "stopset", stopset: generatedStopset })
      console.log(items)
    } else {
      console.warn("Couldn't generate a stopset!")
    }
    updateUI()
  }

  const processNextItem = () => {
    if (items.length === 0) {
      addStopset()
    }

    if (items.length === 0) {
      console.warn("No items to process")
      return
    }

    const item = items[0]

    if (item.type === "wait") {
      console.log("processing wait")
      item.expires = dayjs().add(item.duration, "seconds")
      item.elapsed = 0
      const interval = setInterval(() => {
        const secondsLeft = item.expires.diff(dayjs(), "ms") / 1000
        item.elapsed = item.duration - secondsLeft
        if (secondsLeft < 0) {
          clearInterval(interval)
          items.shift()
          processNextItem()
        }
        updateUI()
      }, 25)
    } else if (item.type === "stopset") {
      item.stopset.play()
    }
  }

  addStopset()
  processNextItem()

  db.subscribe(() => {
    if (items.length === 0) {
      processNextItem()
    }
  })
</script>

<div class="col-span-2">
  {#if items.length > 0}
    <PlayBar item={items[0]} />

    <div class="mt-4 flex justify-center gap-3">
      <button class="btn btn-success" disabled={!hasOneStopset()}>Play</button>
      <button class="btn btn-warning" disabled={!hasOneStopset()}>Pause</button>
      {#if $userConfig.uiMode >= 1}
        <button class="btn btn-error">Skip stop set</button>
      {/if}
    </div>
  {:else}
    <div class="text-full mt-3 text-center text-3xl italic text-error">
      Can't generate a stopset. You're sure the server has data?
    </div>
  {/if}
</div>

<div class="border-base-content min-h-full h-0 flex flex-col">
  <div class="font-bold text-sm text-center mt-0 mb-2 divider">Playlist</div>
  <div class="flex-1 overflow-auto" id="playlist">
    {#each items as item}
      {#if item.type === "stopset"}
        {#each item.stopset.items as asset}
          <div>{asset.rotator.name} - {asset.name}</div>
        {/each}
      {/if}
    {/each}
  </div>
</div>

<!-- <div class="pt-5 pl-5">
  {#if items.length > 0}
    <ol>
      {#each items as item, index}
        {#if item.type === "wait"}
          <li>{index + 1}. Wait for {item.amount}</li>
        {:else if item.type === "stopset"}
          <li>{index + 1}. Stopset: {item.stopset.name} Currently playing:{item.stopset.current}</li>
            {#each item.stopset.items as asset}
              <div>{asset.name} [{asset.elapsed.format("mm:ss")}/{asset.duration.format("mm:ss")}] finished = {asset.finished}</div>
            {/each}
        {/if}
      {/each}
    </ol>
  {:else}
    No line items!
  {/if}
  <button class="btn" on:click={addStopset}>add</button>
  Length: {$db.assets.length}
</div> -->
