<script>
  import { tick } from "svelte"
  import { prettyDuration } from "../../utils"

  export let item

  let remaining
  $: if (item.type === "wait") {
    remaining = item.duration - item.elapsed
  } else if (item.type === "stopset") {
    remaining = item.stopset.duration - item.stopset.elapsed
  }

  const hideDurationIfSmall = async (el) => {
    await tick()
    console.log('width:', el.clientWidth)
  }
</script>

<div class="my-3 flex justify-center">
  <div class="text-xl font-bold">
    <span class="font-mono">{prettyDuration(remaining)}</span>
    remaining
    {#if item.type === "wait"}
      to wait
    {:else if item.type === "stopset"}
      in {item.stopset.name}
    {/if}
  </div>
</div>

{#if item.type === "wait"}
  <div class="flex items-center gap-2">
    <div class="font-mono">{prettyDuration(item.elapsed, item.duration)}</div>
    <progress class="progress h-6 flex-1" value={item.elapsed} max={item.duration} />
    <div class="font-mono">{prettyDuration(item.duration)}</div>
  </div>
{:else if item.type === "stopset"}
  <div
    class="relative grid h-8 gap-2 overflow-hidden rounded-xl border-4 border-base-300 bg-base-300"
    style:grid-template-columns={item.stopset.playableNonErrorItems.map((item) => `${item.durationFull}fr`).join(" ")}
  >
    {#each item.stopset.playableNonErrorItems as asset}
      <div
        class="flex flex-col items-center justify-center font-mono text-xs leading-none"
        use:hideDurationIfSmall
        style:background-color={asset.rotator.color.value}
        style:color={asset.rotator.color.content}
      >
        {prettyDuration(asset.duration)}
      </div>
    {/each}
    <div
      class="absolute h-full w-[5px] bg-base-content"
      style:left={`calc(${(item.stopset.elapsedFull / item.stopset.durationFull) * 100}% - 2.5px)`}
    />
  </div>
{/if}
<!-- {if item.type === "remaining"
<div
  class="w-full rounded-xl bg-base-300 h-3 grid gap-2 overflow-hidden"
  style:grid-template-columns={columns.join(' ')}
>
  {#each columns as column}
    <div class="h-full" class:bg-base-300={item.type === "wait"} />
  {/each}
</div> -->
