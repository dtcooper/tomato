<script>
  import playCircleOutlineIcon from "@iconify/icons-mdi/play-circle-outline"
  import stopCircleOutlineIcon from "@iconify/icons-mdi/stop-circle-outline"
  import playIcon from "@iconify/icons-mdi/play"
  import playlistPlayIcon from "@iconify/icons-mdi/playlist-play"

  import AssetPicker from "../modals/AssetPicker.svelte"
  import Icon from "../../components/Icon.svelte"

  import { singlePlayRotators, playFromRotator, play, stop } from "../../stores/single-play-rotators"
  import { userConfig } from "../../stores/config"

  export let playlistItems
  export let mediumIgnoreIds

  let modalRotator
  let showModal = false

  $: playDisabled =
    $singlePlayRotators.isPlaying ||
    (playlistItems.some((item) => item.type === "stopset") &&
      playlistItems[0].type === "stopset" &&
      playlistItems[0].playing)

  $: if (!showModal) {
    modalRotator = null
  }
</script>

<AssetPicker bind:show={showModal} rotator={modalRotator}>
  <svelte:fragment slot="action-name">Play</svelte:fragment>
  <svelte:fragment slot="title">Play single asset</svelte:fragment>
  <p slot="description">
    Click on a single asset to immediate play from
    <span
      class="badge select-text border-secondary-content font-medium"
      style:background-color={modalRotator.color.value}
      style:color={modalRotator.color.content}>{modalRotator.name}</span
    > below.
  </p>
  <button
    class="btn btn-square btn-success"
    tabindex="-1"
    disabled={playDisabled}
    slot="action"
    let:asset
    on:click={() => {
      play(asset, modalRotator)
      modalRotator = null
      showModal = false
    }}
  >
    <Icon icon={playIcon} class="h-12 w-12" />
  </button>
</AssetPicker>

<div class="flex h-0 min-h-full w-full flex-col rounded-lg border-base-content bg-base-200 p-1.5 pt-2">
  <div class="divider m-0 mb-2 w-full font-mono text-sm italic">Play single asset from&hellip;</div>
  <div class="flex flex-1 flex-col gap-1 overflow-y-auto px-2">
    {#each $singlePlayRotators.rotators as rotator}
      {@const disabled =
        playDisabled && (!$singlePlayRotators.rotator || $singlePlayRotators.rotator.id !== rotator.id)}
      {@const playing =
        $singlePlayRotators.isPlaying && $singlePlayRotators.rotator && $singlePlayRotators.rotator.id === rotator.id}
      <div class="grid grid-cols-[auto,min-content] gap-1">
        <button
          class="btn flex-1 text-left hover:brightness-110"
          class:btn-lg={$singlePlayRotators.rotators.length <= 2}
          class:hover:brightness-110={!disabled}
          class:btn-error={playing}
          style={playDisabled ? "" : `background-color: ${rotator.color.value}; color: ${rotator.color.content}`}
          {disabled}
          on:click={() => (playing ? stop() : playFromRotator(rotator, mediumIgnoreIds))}
          tabindex="-1"
        >
          <Icon icon={playing ? stopCircleOutlineIcon : playCircleOutlineIcon} class="h-10 w-10" />
          <span class="w-0 flex-1 truncate py-2">{rotator.name}</span>
        </button>
        {#if $userConfig.uiMode >= 2}
          <div
            class:tooltip={$userConfig.tooltips}
            class="tooltip-left flex"
            data-tip="Select specific asset from rotator"
          >
            <button
              class="btn btn-square btn-warning h-full"
              on:click={() => {
                modalRotator = rotator
                showModal = true
              }}
              tabindex="-1"
            >
              <Icon icon={playlistPlayIcon} class="h-8 w-8" />
            </button>
          </div>
        {/if}
      </div>
    {/each}
  </div>
</div>
