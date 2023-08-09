<script>
  import { fade } from "svelte/transition"
  import playCircleOutlineIcon from "@iconify/icons-mdi/play-circle-outline"
  import pauseCircleOutlineIcon from "@iconify/icons-mdi/pause-circle-outline"
  import skipForwardOutlineIcon from "@iconify/icons-mdi/skip-forward-outline"
  import reloadIcon from "@iconify/icons-mdi/reload"

  import Icon from "../components/Icon.svelte"
  import PlayBar from "./player/PlayBar.svelte"

  import { config, userConfig } from "../stores/config"
  import { db } from "../stores/db"
  import { Wait } from "../stores/player"
  import { prettyDuration, humanDuration } from "../utils"

  // Object automatically updates on change
  let items = []

  const updateUI = () => (items = items) // Callback for force re-render
  const PRE_GENERATED_STOPSETS = 3  // TODO: Should be a config option
  const numStopsetsToPreload = 2


  const addStopset = () => {
    // If previous item is not a wait interval
    let shouldPrependWait = $config.WAIT_INTERVAL > 0 && items.length > 0 && items[items.length - 1].type !== "wait"

    let generatedStopset = $db.generateStopset(null, processItem, updateUI)

    if (generatedStopset) {
      if (shouldPrependWait) {
        items.push(new Wait(processItem, updateUI))
      }
      items.push(generatedStopset)
      if ($config.WAIT_INTERVAL > 0) {
        items.push(new Wait(processItem, updateUI))
      }
    } else {
      console.warn("Couldn't generate a stopset!")
    }
    updateUI()
  }

  const processItem = (index = 1, play = false, subindex = 0) => {
    if (index > items.length) {
      console.warn(`Index ${index} out of band while processing items`)
      return
    }
    while (index-- > 0) {
      items.shift().done(true)
    }

    let numStopsetsToAdd = PRE_GENERATED_STOPSETS - items.filter(item => item.type === "stopset").length
    while (numStopsetsToAdd-- > 0) {
      addStopset()
    }

    if (items.length === 0) {
      console.warn("No items to process")
      return
    }

    // Preload first few
    items.filter(item => item.type === "stopset").slice(0, numStopsetsToPreload).forEach(item => item.loadAudio())

    const nextItem = items[0]
    if (nextItem.type === "wait") {
      nextItem.run()
    } else if (nextItem.type === "stopset" && (play || (IS_DEV && $userConfig.autoplay))) {
      console.log("processItem(): playing first stopset")
      nextItem.play()
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
    items[0].pause()
  }

  if ($config.WAIT_INTERVAL) {
    items.push(new Wait(processItem, updateUI))
  }

  processItem(0)

  db.subscribe(() => {
    if (items.length === 0) {
      // When we get new data from server, if items is empty, regenerate stopset
      processItem(0)
    }
  })
</script>

<div class="col-span-2 flex flex-col gap-5 mt-3">
  {#if items.length > 0}
    {@const item = items[0]}
    <div class="flex items-center justify-center gap-3">
      <button
        class="btn btn-success btn-lg pl-3 relative !z-10"
        disabled={!items.some((item) => item.type === "stopset") || (item.type === "stopset" && item.playing)}
        on:click={play}
        class:tomato-pulse={item.type === "wait" && item.overtime}
        style:--pulse-color="var(--su)"
      >
        <Icon icon={playCircleOutlineIcon} class="h-12 w-12" /> Play
      </button>
      {#if $userConfig.uiMode >= 1}
        <button
          class="btn btn-warning btn-lg"
          disabled={item.type !== "stopset" || !item.playing}
          on:click={pause}
        >
          <Icon icon={pauseCircleOutlineIcon} class="h-12 w-12" /> Pause
        </button>
      {/if}
      {#if $userConfig.uiMode >= 2}
        <div
          class={item.type === "stopset" && "tooltip tooltip-error tooltip-bottom"}
          data-tip="Warning: this action will be logged!"
        >
          <button class="btn btn-error" disabled={item.type !== "stopset"}>
            <Icon icon={skipForwardOutlineIcon} class="h-8 w-8" /> Skip stopset
          </button>
        </div>
        <button class="btn btn-warning">
          <Icon icon={reloadIcon} class="h-8 w-8" /> Regenerate next stopset
        </button>
      {/if}
    </div>

    <PlayBar {item} />

  {:else}
    <div class="mt-3 text-center text-3xl italic text-error">
      Can't generate a stopset. You're sure the server has data?
    </div>
  {/if}
</div>

<!-- col-span-2 until we have a single play rotator player -->
<div class="col-span-2 flex h-0 min-h-full flex-col gap-2 border-base-content">
  <div class="divider my-0 text-sm font-bold text-primary">Playlist</div>
  <div class="flex flex-1 flex-col overflow-y-auto" id="playlist">
    {#each items as item, index (item.generatedId)}
      {@const isFirstItem = index === 0}
      <div class="flex flex-1 flex-col gap-2 px-2" out:fade={{duration: 250}}>
        <div
          class="divider mb-0 mt-2 italic"
          class:text-secondary={item.type === "stopset"}
          class:text-accent={item.type === "wait"}
        >
          {item.name} ({item.generatedId})
        </div>
        {#if item.type === "stopset"}
          {#each item.items as asset}
            {@const rightColor = asset.color.value}
            {@const leftColor = asset.color.dark}
            <div
              class="border-l-4 pl-2"
              class:border-base-content={asset.finished}
              class:border-success={isFirstItem && asset.active}
              class:border-base-300={!asset.finished && !asset.active}
            >
              <div
                class="flex items-center gap-3 overflow-hidden bg-clip-text px-3 py-1"
                style:background={`linear-gradient(to right, ${leftColor} 0%, ${leftColor} ${asset.percentDone}%, ${rightColor} ${asset.percentDone}%, ${rightColor} 100%)`}
                style:color={asset.color.content}
              >
                <div
                  class="radial-progress h-20 w-20 font-mono text-sm"
                  style:--value={(asset.elapsed / asset.duration) * 100}
                  style:--thickness={asset.elapsed === 0 ? "0" : "0.4rem"}
                >
                  {prettyDuration(asset.remaining)}
                </div>
                <div class="flex flex-1 flex-col overflow-hidden">
                  <div class="text-xl truncate">{asset.name}</div>
                  <div class="font-sm font-mono font-bold truncate">{asset.rotator.name}</div>
                </div>
                <div>timer</div>
              </div>
            </div>
          {/each}
        {:else if item.type === "wait"}
          <!-- wonky because items being identical? -->
          <div class="border-l-4 pl-2" class:border-base-content={!isFirstItem} class:border-success={isFirstItem}>
            <div
              class="flex items-center gap-3 overflow-hidden rounded-xl px-3 py-1"
              style:background-image={`linear-gradient(to right, hsl(var(--b3)) 0%, hsl(var(--b3)) ${item.percentDone}%, hsl(var(--b2)) ${item.percentDone}%, hsl(var(--b2)) 100%)`}
            >
              <div
                class="radial-progress h-20 w-20 font-mono text-sm"
                style:--value={(item.elapsed / item.duration) * 100}
                style:--thickness={item.elapsed === 0 ? "0" : "0.4rem"}
              >
                {prettyDuration(item.remaining)}
              </div>
              <div class="flex-1 flex flex-col text-xl font-bold">
                <div class:italic={item.overtime}>Wait{item.overtime ? 'ed' : ''} for {humanDuration(item.duration)}{item.overtime ? '!' : ''}</div>
                {#if item.overtime}
                  <div class="text-success animate-pulse">Play next stop set now!</div>
                {/if}
              </div>
              <div class="self-start flex flex-col font-mono text-sm">
                <div>{prettyDuration(item.elapsed, item.duration)} / {prettyDuration(item.duration)}</div>
                {#if item.overtime}
                  <div class="font-bold text-error animate-pulse">{prettyDuration(item.overtimeElapsed)} overdue</div>
                  {item.overdue}
                {/if}
              </div>
            </div>
          </div>
        {/if}
      </div>
      <div class="flex flex-col items-center">Add more</div>
    {:else}
      <div class="font-error italic text-lg">No items in playlist!</div>
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
