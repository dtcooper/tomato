<script>

  import { slide } from 'svelte/transition';
  import playCircleOutlineIcon from '@iconify/icons-mdi/play-circle-outline'
  import pauseCircleOutlineIcon from '@iconify/icons-mdi/pause-circle-outline'
  import skipForwardOutlineIcon from '@iconify/icons-mdi/skip-forward-outline'
  import reloadIcon from '@iconify/icons-mdi/reload'

  import Icon from "../components/Icon.svelte"
  import PlayBar from "./player/PlayBar.svelte"

  import { config, userConfig } from "../stores/config"
  import { db, restoreAssetsDBFromLocalStorage } from "../stores/db"
  import { Wait } from "../stores/player"
  import { prettyDuration, humanDuration } from "../utils"

  // Object automatically updates on change
  let items = []
  const firstItem = () => items.length > 0 ? items[0] : null
  const updateUI = () => (items = items) // Callback for force re-render

  const hasOneStopset = () => items.some((item) => item.type === "stopset")
  const addStopset = () => {
    // If previous item is not a wait interval
    let shouldPrependWait = $config.WAIT_INTERVAL > 0 && items.length > 0 && items[items.length - 1].type !== "wait"

    let generatedStopset = $db.generateStopset(null, processItem, updateUI)

    if (generatedStopset) {
      if (!hasOneStopset()) {
        generatedStopset.loadAudio() // Preload audio
      }
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
    while (index-- > 0)
      items.shift().done(true)  // skip callback (would be recursive)
    if (items.length === 0 || !hasOneStopset())
      addStopset()
    if (items.length === 0) {
      console.warn("No items to process")
      return
    }

    const nextItem = items[0]
    if (nextItem.type === "wait") {
      nextItem.run()
    } else if (nextItem.type === "stopset" && (play || (IS_DEV && $userConfig.autoplay))) {
      nextItem.play()
    }
  }

  const play = () => {
    const firstStopsetIndex = items.findIndex(item => item.type === "stopset")
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

<div class="col-span-2">
  {#if items.length > 0}
    <PlayBar item={items[0]} />

    <div class="mt-4 flex items-center justify-center gap-3">
      <button
        class="btn btn-lg btn-success pl-3"
        disabled={!hasOneStopset() || (items[0].type === "stopset" && items[0].playing)}
        on:click={play}
      >
        <Icon icon={playCircleOutlineIcon} class="w-12 h-12" /> Play
      </button>
      {#if $userConfig.uiMode >= 1}
        <button
          class="btn btn-lg btn-warning"
          disabled={items[0].type !== "stopset" || !items[0].playing} on:click={pause}
        >
          <Icon icon={pauseCircleOutlineIcon} class="w-12 h-12" /> Pause
        </button>
      {/if}
      {#if $userConfig.uiMode >= 2}
        <div class={items[0].type === "stopset" && 'tooltip tooltip-bottom tooltip-error'} data-tip="Warning: this action will be logged!">
          <button
            class="btn btn-error"
            disabled={items[0].type !== "stopset"}
          >
            <Icon icon={skipForwardOutlineIcon} class="w-8 h-8" /> Skip stopset
          </button>
        </div>
        <button class="btn btn-warning">
          <Icon icon={reloadIcon} class="w-8 h-8" /> Regenerate next stopset
        </button>
      {/if}
    </div>
  {:else}
    <div class="text-full mt-3 text-center text-3xl italic text-error">
      Can't generate a stopset. You're sure the server has data?
    </div>
  {/if}
</div>

<!-- col-span-2 until we have a single play rotator player -->
<div class="border-base-content min-h-full h-0 flex flex-col col-span-2 gap-2">
  <div class="font-bold text-sm my-0 divider text-primary">Playlist</div>
  <div class="flex-1 overflow-y-auto flex flex-col gap-1.5" id="playlist" transition:slide|global>
    {#each items as item, index}
      <div class="my-0 divider italic" class:text-secondary={item.type === "stopset"} class:text-accent={item.type === "wait"}>{item.name}</div>
        {#if item.type === "stopset"}
          {#each item.items as asset}
            <div class="pl-2 border-l-4 border-base-content">
              <div
                class="rounded-xl items-center flex overflow-hidden px-3 py-1 gap-3 bg-clip-text"
                style:background={`linear-gradient(to right, ${asset.color.dark} 0%, ${asset.color.dark} ${asset.percentDone}%, ${asset.color.value} ${asset.percentDone}%, ${asset.color.value} 100%)`}
                style:color={asset.color.content}
              >
                <div
                  class="radial-progress font-mono text-sm h-20 w-20"
                  style:--value={asset.elapsed / asset.duration * 100}
                  style:--thickness={asset.elapsed === 0 ? '0' : '0.4rem'}
                >
                  {prettyDuration(asset.remaining)}
                </div>
                <div class="flex-1 truncate flex flex-col">
                  <div class="text-xl">{asset.name}</div>
                  <div class="font-bold font-mono font-sm">{asset.rotator.name}</div>
                </div>
                <div>timer</div>
              </div>
            </div>
          {/each}
        {:else if item.type === "wait"}
          <div class="pl-2 border-l-4" class:border-base-content={index !== 0} class:border-success={index === 0}>
            <div
              class="rounded-xl items-center flex overflow-hidden px-3 py-1 gap-3"
              style:background-image={`linear-gradient(to right, hsl(var(--b3)) 0%, hsl(var(--b3)) ${item.percentDone}%, hsl(var(--b2)) ${item.percentDone}%, hsl(var(--b2)) 100%)`}
            >
              <div
                class="radial-progress font-mono text-sm h-20 w-20"
                style:--value={item.elapsed / item.duration * 100}
                style:--thickness={item.elapsed === 0 ? '0' : '0.4rem'}
              >
                {prettyDuration(item.remaining)}
              </div>
              <div class="font-bold text-2xl flex-1">Wait for {humanDuration(item.duration)}</div>
              <div class="font-mono text-sm self-start">{prettyDuration(item.elapsed, item.duration)} / {prettyDuration(item.duration)}</div>
            </div>
          </div>
        {/if}
      {/each}
    <div class="flex flex-col items-center">
      Add more
    </div>
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
