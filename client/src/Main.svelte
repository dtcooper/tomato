<script>
  import dayjs from "dayjs";
  import { logout, address, online } from "./stores/connection";
  import {
    sync,
    syncing,
    generateStopset,
    assets,
    progress,
  } from "./stores/store";
  import { colors } from "../../server/constants.json";

  export let generated;
  const generateStopsetWithAudioFiles = () => {
    let stopset = generateStopset();
    generated = {
      ...stopset,
      loaded: false,
      duration: 0.0,
      assets: stopset.assets.map(({ asset, rotator }, i) => {
        // TODO what if asset if empty?
        const audio = new Audio(
          asset.file.localUrl +
            (Math.floor(stopset.assets.length * Math.random()) === 0
              ? "-bad"
              : "")
        );
        const entry = {
          asset,
          rotator,
          audio,
          loaded: false,
          progress: null,
          error: false,
        };
        audio.addEventListener("canplaythrough", () => {
          entry.loaded = true;
          if (
            generated.assets.filter(({ loaded, error }) => loaded || error)
              .length === generated.assets.length
          ) {
            generated.loaded = true;
          }
        });
        audio.addEventListener("error", () => {
          entry.error = true;
          if (
            generated.assets.filter(({ loaded, error }) => loaded || error)
              .length === generated.assets.length
          ) {
            generated.loaded = true;
          }
          generated = generated;
        });
        return entry;
      }),
    };
  };

  generateStopsetWithAudioFiles();
  export const getColor = (name, value = "value") =>
    colors.find((color) => color.name === name)[value];

  export const isHour = (d) => d.asSeconds() >= 3600;
  export const formatDuration = (d) =>
    isHour(d)
      ? `${Math.floor(d.asHours())}:${d.format("mm:ss")}`
      : d.format("m:ss");
  export let playing = -1;

  export const play = () => {
    playing += 1;

    if (generated.assets.length > playing) {
      const entry = generated.assets[playing];
      if (entry.error) {
        play();
      } else {
        entry.audio.currentTime = 0; // for testing, should just refresh
        entry.audio.play();
        //entry.audio.currentTime = entry.audio.duration - 5  //for testing
        entry.audio.addEventListener("error", () => {
          entry.error = true;
          generated = v;
          play();
        });
        entry.audio.addEventListener("ended", play);
        entry.audio.addEventListener("timeupdate", () => {
          entry.progress = Math.ceil(entry.audio.currentTime);
          generated = generated;
        });
      }
    } else {
      playing = -1;
    }
  };

  export const next = () => {
    const entry = generated.assets[playing];
    if (!entry.error) {
      entry.audio.pause();
    }
    play();
  };

  export const refresh = () => window.location.reload();
</script>

<div
  class="flex flex-col space-y-1 items-center h-screen max-h-screen w-full max-w-full"
>
  <div class="btn-group mt-2 p-2">
    <button on:click="{logout}" class="btn btn-warning">Logout</button>
    <button on:click="{sync}" class="btn btn-primary" disabled="{$syncing}"
      >Sync</button
    >
    <button on:click="{refresh}" class="btn btn-secondary"
      >Generate Stopset</button
    >
    {#if playing > -1}
      <button on:click="{next}" class="btn btn-error">Next</button>
    {:else}
      <button
        on:click="{play}"
        class="btn btn-success"
        disabled="{!generated.loaded}">Play</button
      >
    {/if}
  </div>

  <span>{$address} ({$online ? "online" : "offline"})</span>
  {#if generated}
    {@const { assets, stopset, duration } = generated}
    <!-- todo compontent for stopset -->
    <div class="grow w-full max-w-full overflow-y-auto font-sans p-2">
      <div class="w-full sm:w-2/3 lg:w-1/2 flex flex-col space-y-1">
        <div
          class="divider text-xl font-mono font-bold italic !my-3 before:bg-secondary after:bg-secondary"
        >
          {stopset.name} [{formatDuration(dayjs.duration(duration, "seconds"))}]
        </div>
        {#each assets as { asset, rotator, loaded, audio, error, progress }, index}
          <div
            class="border-l-4 sm:border-l-[6px] lg:border-l-8 rounded-l-xl  pl-2"
            class:border-error="{error}"
            class:border-content-base="{!error && playing < index}"
            class:border-green-A400="{!error && playing === index}"
            class:border-gray-500="{!error && playing > index}"
          >
            <div
              class="p-2 rounded-xl grid gap-2 grid-cols-[min-content_1fr_min-content]"
              style:background-color="{getColor(rotator.color)}"
              style:color="{getColor(rotator.color, "content")}"
              class:!text-error-content="{error}"
              class:!bg-error="{error}"
            >
              {#if error}
                <div
                  class="relative animate-[ping_1.5s_infinite] w-20 h-20 text-error-content font-bold flex items-center justify-center"
                >
                  ERROR
                </div>
                <div
                  class="absolute w-20 h-20 text-error-content font-bold flex items-center justify-center"
                >
                  ERROR
                </div>
              {:else}
                <div
                  class="font-mono w-20 h-20 flex items-center justify-center"
                  class:radial-progress="{progress !== null}"
                  class:text-sm="{isHour(asset.duration)}"
                  style:--value="{progress === null
                    ? 0
                    : (progress / Math.ceil(audio.duration)) * 100}"
                >
                  {formatDuration(
                    progress === null
                      ? asset.duration
                      : dayjs.duration(
                          Math.ceil(audio.duration) - progress,
                          "seconds"
                        )
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
