<script>
  import { fade } from "svelte/transition"
  import { tick } from "svelte"
  import { prettyDuration } from "../../utils"
  import { config } from "../../stores/config"

  export let item

  const hideDurationIfSmall = async (el) => {
    await tick()
    if (el.clientWidth - el.firstChild.clientWidth - 10 < 0) {
      el.firstChild.remove()
      console.log("too big!")
    }
  }
</script>

<div class="flex justify-center">
  <div
    class="font-mono text-2xl font-bold"
    class:tomato-pulse={item.type === "wait" && item.overdue}
    style="--pulse-color: var(--er); --pulse-size: 5px;"
  >
    {#if item.type === "wait" && item.overtime}
      {#if item.overdue}
        <span class="italiv text-error">
          You are <span class="underline">OVERDUE</span> to play a {$config.STOPSET_ENTITY_NAME}. Press play now.
        </span>
      {:else}
        <span class="text-success">Play next {$config.STOPSET_ENTITY_NAME} now</span>
      {/if}
    {:else}
      {prettyDuration(item.remaining)}
      remaining
      {#if item.type === "wait"}
        to wait
      {:else if item.type === "stopset"}
        in {$config.STOPSET_ENTITY_NAME}
      {/if}
    {/if}
  </div>
</div>

<div class="flex items-center gap-2">
  <div class="font-mono">{prettyDuration(item.elapsed, item.duration)}</div>
  {#if item.type === "wait"}
    <progress class="progress h-8 flex-1" value={item.elapsed} max={item.duration} />
  {:else if item.type === "stopset"}
    <div class="relative flex flex-1">
      <div
        class="relative grid h-8 flex-1 gap-1 overflow-hidden rounded-xl bg-base-300"
        style:grid-template-columns={item.playableNonErrorItems.map((item) => `${item.duration}fr`).join(" ")}
      >
        {#each item.playableNonErrorItems as asset}
          <div
            class="flex flex-col items-center justify-center overflow-hidden font-mono text-xs leading-none"
            use:hideDurationIfSmall
            style:background-color={asset.rotator.color.value}
            style:color={asset.rotator.color.content}
          >
            <span>{prettyDuration(asset.duration)}</span>
          </div>
        {/each}
        <div
          class="absolute left-0 z-10 h-full bg-base-100 opacity-40"
          style:width={`${(item.elapsed / item.duration) * 100}%`}
        />
        <div
          class="absolute z-20 h-full w-[6px] border-x-[1px] border-base-100 bg-base-content"
          class:animate-pulse={!item.playing}
          style:left={`calc(${(item.elapsed / item.duration) * 100}% - 3px)`}
        />
      </div>
    </div>
  {/if}
  <div class="font-mono">{prettyDuration(item.duration)}</div>
</div>
