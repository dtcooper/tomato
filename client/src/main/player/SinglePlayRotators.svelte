<script>
  import { singlePlayRotators, play } from "../../stores/single-play-rotators"
  import playCircleOutlineIcon from "@iconify/icons-mdi/play-circle-outline"

  import Icon from "../../components/Icon.svelte"

  export let playlistItems

  $: mediumIgnoreIds =
    // Copied from Player.svelte generateStopsetHelper()
    new Set(
      playlistItems
        .filter((i) => i.type === "stopset")
        .map((s) => s.items.map((a) => a.id))
        .flat(1)
    )

  $: playDisabled =
    $singlePlayRotators.isPlaying ||
    (playlistItems.some((item) => item.type === "stopset") &&
      playlistItems[0].type === "stopset" &&
      playlistItems[0].playing)
</script>

<div class="flex h-0 min-h-full w-full flex-col rounded-lg border-base-content bg-base-200 p-1.5 pt-2">
  <div class="divider m-0 mb-2 w-full font-mono text-sm italic text-primary">Play single asset from&hellip;</div>
  <div class="flex flex-1 flex-col gap-2 overflow-y-auto px-2">
    {#each $singlePlayRotators.rotators as rotator, index}
      {@const error = $singlePlayRotators.errors.get(rotator.id)}
      <div
        class="tooltip-error tooltip-bottom tooltip-open flex"
        data-tip={`${error}!`}
        class:tooltip-bottom={index < 4 || index + 1 != $singlePlayRotators.rotators.length}
        class:tooltip-top={index >= 4 && index + 1 == $singlePlayRotators.rotators.length}
        class:tooltip={!!error}
      >
        <button
          class="btn w-0 flex-1 text-left hover:brightness-110"
          class:btn-lg={$singlePlayRotators.rotators.length <= 4}
          style={playDisabled ? "" : `background-color: ${rotator.color.value}; color: ${rotator.color.content}`}
          disabled={playDisabled}
          on:click={() => play(rotator, mediumIgnoreIds)}
          tabindex="-1"
        >
          <Icon icon={playCircleOutlineIcon} class="h-8 w-8" />
          <span class="w-0 flex-1 truncate py-2">{rotator.name}</span>
        </button>
      </div>
    {/each}
  </div>
</div>
