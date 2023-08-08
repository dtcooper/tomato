<script>
  import { tick } from "svelte"
  import { prettyDuration } from "../../utils"

  export let item

  const hideDurationIfSmall = async (el) => {
    await tick()
    if (el.clientWidth - el.firstChild.clientWidth - 10 < 0) {
      el.firstChild.remove()
      console.log("too big!")
    }
  }
</script>

<div class="my-3 flex justify-center">
  <div class="text-2xl font-bold">
    <span class="font-mono">{prettyDuration(item.remaining)}</span>
    remaining
    {#if item.type === "wait"}
      to wait
    {:else if item.type === "stopset"}
      in {item.name}
    {/if}
  </div>
</div>

<div class="flex items-center gap-2">
  <div class="font-mono">{prettyDuration(item.elapsed, item.duration)}</div>
    {#if item.type === "wait"}
      <progress class="progress h-8 flex-1" value={item.elapsed} max={item.duration} />
    {:else if item.type === "stopset"}
      <div class="flex flex-1 relative">
        <div
          class="flex-1 relative grid h-8 gap-2 overflow-hidden bg-base-300 rounded-xl"
          style:grid-template-columns={item.playableNonErrorItems.map((item) => `${item.duration}fr`).join(" ")}
        >
          {#each item.playableNonErrorItems as asset}
            <div
              class="flex flex-col items-center justify-center font-mono text-xs leading-none overflow-hidden"
              use:hideDurationIfSmall
              style:background-color={asset.rotator.color.value}
              style:color={asset.rotator.color.content}
            >
              <span>{prettyDuration(asset.duration)}</span>
            </div>
          {/each}
          <div
            class="absolute h-full w-[5px] z-10 bg-error"
            class:animate-pulse={!item.playing}
            style:left={`calc(${(item.elapsed / item.duration) * 100}% - 2.5px)`}
          />
        </div>
      </div>
    {/if}
  <div class="font-mono">{prettyDuration(item.duration)}</div>
</div>
