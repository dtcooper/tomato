<script>
  import { prettyDuration } from "../../utils"

  export let item

  let remaining
  $: if (item.type === "wait") {
    remaining = item.duration - item.elapsed
  } else if (item.type === "stopset") {
    remaining = item.stopset.duration - item.stopset.elapsed
  }

  $: console.log('item', item)

</script>


<div class="flex justify-center my-3">
  <div class="font-bold text-xl">
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
    <progress class="progress flex-1 h-6" value={item.elapsed} max={item.duration}></progress>
    <div class="font-mono">{prettyDuration(item.duration)}</div>
  </div>
{:else if item.type === "stopset"}
  <div
    class="grid h-6 bg-base-300 rounded-xl gap-2 overflow-hidden relative"
    style:grid-template-columns={
      item.stopset.playableItems.map(item => `${item.durationFull}fr`).join(' ')
    }
  >
    {#each item.stopset.playableItems as asset}
      <div
        class="flex flex-col items-center justify-center font-mono text-xs leading-none"
        style:background-color={asset.rotator.color.value}
        style:color={asset.rotator.color.content}
      >
        {prettyDuration(asset.duration)}
      </div>
    {/each}
    <div
      class="absolute h-full w-[0.3rem] bg-black" style:left={`calc(${item.stopset.elapsedFull / item.stopset.durationFull * 100}% - 0.15rem)`}
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
