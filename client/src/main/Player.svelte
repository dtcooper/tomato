<script>
  import dayjs from "dayjs"
  import { config } from "../stores/config"
  import { db } from "../stores/assets"

  let items = []

  const uiUpdate = () => {
    // UI update function
    items = items
  }

  const addStopset = () => {
    let wait = null
    // If there's nothing in list, add a wait
    if (items.length === 0 || items[items.length - 1].type !== "wait") {
      wait = {type: "wait", seconds: $config.WAIT_INTERVAL}
    }

    let generatedStopset = $db.generateStopset(null, uiUpdate)

    if (generatedStopset) {
      // If it's the only stopset, process it
      //if (!items.some(item => item.type === "stopset")) {
        generatedStopset.loadAudio()  // Preload audio
        generatedStopset.play()
      //}
      if (wait) {
        items.push(wait)
      }
      items.push({type: "stopset", stopset: generatedStopset})
    } else {
      items.push({type: "stopset-not-found"})
    }
    uiUpdate()
  }

  // If items were empty, it's because there was nothing in the DB, on a DB refresh, try to add it again
  // db.subscribe(() => {
  //   if (items.length === 0) {
  //     addStopset()
  //   }
  // })

  // assetsDb.subscribe(() => {
  //   // auto update
  //   db = assetsDb
  // })

  addStopset()
</script>


<div class="pt-5 pl-5">
  {#if items.length > 0}
    <ol>
      {#each items as {type, seconds, stopset}, index}
        {#if type === "wait"}
          <li>{index + 1}. Wait for {dayjs.duration(seconds)}</li>
        {:else if type === "stopset"}
          <li>{index + 1}. Stopset: {stopset.name} Currently playing:{stopset.current}</li>
            {#each stopset.items as asset}
              <div>{asset.name} [{asset.currentTime.format("mm:ss")}/{asset.duration.format("mm:ss")}] finished = {asset.finished}</div>
            {/each}
        {/if}
      {/each}
    </ol>
  {:else}
    No line items!
  {/if}
  <button class="btn" on:click={addStopset}>add</button>
  Length: {$db.assets.length}
</div>
