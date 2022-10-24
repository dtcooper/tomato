<script>
  import dayjs from 'dayjs'
  import { logout, address, online } from './stores/connection'
  import { sync, syncing, generateStopset, assets, progress } from './stores/store'
  import { colors } from '../../server/constants.json'

  export let generated
  const generateStopsetWithAudioFiles = () => {
    let stopset = generateStopset()
    generated = {...stopset, loaded: false, assets: stopset.assets.map(({asset, rotator}, i) => {
      // TODO what if asset if empty?
      const audio = new Audio(asset.file.localUrl + (Math.floor(stopset.assets.length * 2.5 * Math.random()) === 0 ? '-bad' : ''))
      const entry = { asset, rotator, audio, loaded: false, progress: null, error: false}
      entry.audio.addEventListener('canplaythrough', () => {
        entry.loaded = true
        if (generated.assets.filter(({loaded, error}) => loaded || error).length === generated.assets.length) {
          generated.loaded = true
        }
        generated = generated
      })
      entry.audio.addEventListener('error', () => {
        entry.error = true
        if (generated.assets.filter(({loaded, error}) => loaded || error).length === generated.assets.length) {
          generated.loaded = true
        }
        generated = generated
      })
      return entry
    })}
  }

  generateStopsetWithAudioFiles()
  export const getColor = (name, value = 'value') => colors.find(color => color.name === name)[value]

  export const isHour = d => d.asSeconds() >= 3600
  export const formatDuration = d => isHour(d) ? `${Math.floor(d.asHours())}:${d.format('mm:ss')}` : d.format('m:ss')
  export let playing = -1

  export const play = () => {
    playing += 1

    if (generated.assets.length > playing) {
      const entry = generated.assets[playing]
      if (entry.error) {
        play()
      } else {
        entry.audio.play()
        entry.audio.currentTime = entry.audio.duration - 5  //for testing
        entry.audio.addEventListener('error', () => {
          entry.error = true
          generated = v
          play()
        })
        entry.audio.addEventListener('ended', play)
        entry.audio.addEventListener('timeupdate', () => {
          entry.progress = Math.ceil(entry.audio.currentTime)
          generated = generated
        })
      }
    } else {
      playing = -1
    }
  }

  export const refresh = () => window.location.reload()
</script>

<div class="flex flex-col space-y-1 items-center h-screen max-h-screen w-full max-w-full">
  <div class="btn-group mt-2 p-2">
    <button on:click={logout} class="btn btn-warning">Logout</button>
    <button on:click={sync} class="btn btn-primary" disabled={$syncing}>Sync</button>
    <button on:click={refresh} class="btn btn-secondary">Generate Stopset</button>
    {#if playing > -1}
      <button class="btn btn-error">Pause</button>
    {:else}
      <button on:click={play} class="btn btn-success" disabled={!generated.loaded}>Play</button>
    {/if}
  </div>

  <span>{$address} ({$online ? 'online' : 'offline'})</span>
  {#if generated}
    {@const stopset = generated.stopset}
    {@const assets = generated.assets}
    <!-- todo compontent for stopset -->
    <div class="grow w-full max-w-full overflow-y-auto font-sans p-2">
      <div class="w-full sm:w-2/3 lg:w-1/2 flex flex-col space-y-1">
        <div class="divider text-xl font-mono font-bold italic !my-3 before:bg-secondary after:bg-secondary">
          {stopset.name}
        </div>
        {#each assets as {asset, rotator, loaded, audio, error, progress}, index}
          <div
            class="border-l-4 pl-2"
            class:border-error={error}
            class:border-white={!error && playing < index}
            class:border-green-A400={!error && playing === index}
            class:border-black={!error && playing > index}
          >
            <div
              class="p-2 rounded-xl grid gap-2 grid-cols-[min-content_1fr_min-content]"
              style:background-color={getColor(rotator.color)}
              style:color={getColor(rotator.color, 'content')}
              class:!text-error-content={error}
              class:!bg-error={error}
            >
              <div
                class="radial-progress font-mono"
                class:text-sm={isHour(asset.duration)}
                style:--value={progress === null ? 0 : progress / Math.ceil(audio.duration) * 100}
              >
                {formatDuration(progress === null ? asset.duration : dayjs.duration(Math.ceil(audio.duration) - progress, 'seconds'))}
              </div>
              <div class="flex flex-col">
                <h3 class="font-bold">{asset.name}</h3>
                <h4>{rotator.name} [loaded:{loaded}, error:{error}]</h4>
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
