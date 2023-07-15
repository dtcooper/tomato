<script>
  import dayjs from "dayjs"
  import { logout, address, online } from "./stores/connection"
  import { sync, syncing, generateStopset, assets, progress } from "./stores/store"
  import { colors } from "../../server/constants.json"

  export let generated
  const generateStopsetWithAudioFiles = () => {
    let stopset = generateStopset()
    generated = {
      ...stopset,
      loaded: false,
      duration: 0.0,
      assets: stopset.assets.map(({ asset, rotator }, i) => {
        // TODO what if asset if empty?
        const audio = new Audio(
          asset.file.localUrl + (Math.floor(stopset.assets.length * Math.random()) === 0 ? "-bad" : "")
        )
        const entry = {
          asset,
          rotator,
          audio,
          loaded: false,
          progress: null,
          error: false
        }
        audio.addEventListener("canplaythrough", () => {
          entry.loaded = true
          if (generated.assets.filter(({ loaded, error }) => loaded || error).length === generated.assets.length) {
            generated.loaded = true
          }
        })
        audio.addEventListener("error", () => {
          entry.error = true
          if (generated.assets.filter(({ loaded, error }) => loaded || error).length === generated.assets.length) {
            generated.loaded = true
          }
          generated = generated
        })
        return entry
      })
    }
  }

  generateStopsetWithAudioFiles()
  export const getColor = (name, value = "value") => colors.find((color) => color.name === name)[value]

  export const isHour = (d) => d.asSeconds() >= 3600
  export const formatDuration = (d) =>
    isHour(d) ? `${Math.floor(d.asHours())}:${d.format("mm:ss")}` : d.format("m:ss")
  export let playing = -1

  export const play = () => {
    playing += 1

    if (generated.assets.length > playing) {
      const entry = generated.assets[playing]
      if (entry.error) {
        play()
      } else {
        entry.audio.currentTime = 0 // for testing, should just refresh
        entry.audio.play()
        //entry.audio.currentTime = entry.audio.duration - 5  //for testing
        entry.audio.addEventListener("error", () => {
          entry.error = true
          generated = v
          play()
        })
        entry.audio.addEventListener("ended", play)
        entry.audio.addEventListener("timeupdate", () => {
          entry.progress = Math.ceil(entry.audio.currentTime)
          generated = generated
        })
      }
    } else {
      playing = -1
    }
  }

  export const next = () => {
    const entry = generated.assets[playing]
    if (!entry.error) {
      entry.audio.pause()
    }
    play()
  }

  export const refresh = () => window.location.reload()
</script>

<div class="flex h-screen max-h-screen w-full max-w-full flex-col items-center space-y-1">
  <div class="btn-group mt-2 p-2">
    <button on:click={logout} class="btn btn-warning">Logout</button>
    <button on:click={sync} class="btn btn-primary" disabled={$syncing}>Sync</button>
    <button on:click={refresh} class="btn btn-secondary">Generate Stopset</button>
    {#if playing > -1}
      <button on:click={next} class="btn btn-error">Next</button>
    {:else}
      <button on:click={play} class="btn btn-success" disabled={!generated.loaded}>Play</button>
    {/if}
  </div>

  <span>{$address} ({$online ? "online" : "offline"})</span>
  {#if generated}
    {@const { assets, stopset, duration } = generated}
    <!-- todo compontent for stopset -->
    <div class="w-full max-w-full grow overflow-y-auto p-2 font-sans">
      <div class="flex w-full flex-col space-y-1 sm:w-2/3 lg:w-1/2">
        <div class="divider !my-3 font-mono text-xl font-bold italic before:bg-secondary after:bg-secondary">
          {stopset.name} [{formatDuration(dayjs.duration(duration, "seconds"))}]
        </div>
        {#each assets as { asset, rotator, loaded, audio, error, progress }, index}
          <div
            class="rounded-l-xl border-l-4 pl-2 sm:border-l-[6px] lg:border-l-8"
            class:border-error={error}
            class:border-content-base={!error && playing < index}
            class:border-green-A400={!error && playing === index}
            class:border-gray-500={!error && playing > index}
          >
            <div
              class="grid grid-cols-[min-content_1fr_min-content] gap-2 rounded-xl p-2"
              style:background-color={getColor(rotator.color)}
              style:color={getColor(rotator.color, "content")}
              class:!text-error-content={error}
              class:!bg-error={error}
            >
              {#if error}
                <div class="flex h-20 w-20 items-center justify-center font-bold text-error-content">ERROR</div>
              {:else}
                <div
                  class="flex h-20 w-20 items-center justify-center font-mono"
                  class:radial-progress={progress !== null}
                  class:text-sm={isHour(asset.duration)}
                  style:--value={progress === null ? 0 : (progress / Math.ceil(audio.duration)) * 100}
                >
                  {formatDuration(
                    progress === null ? asset.duration : dayjs.duration(Math.ceil(audio.duration) - progress, "seconds")
                  )}
                </div>
              {/if}
              <div class="flex flex-col">
                <h3 class="font-bold">{asset.name}</h3>
                <h4>{rotator.name}</h4>
              </div>
              <div>
                {#if asset}
                  <span class="font-mono">
                    {formatDuration(asset.duration)}
                  </span>
                {:else}
                  No asset in this rotator
                {/if}
              </div>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {:else}
    <span>No stopset generated!</span>
  {/if}
</div>
