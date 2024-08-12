<script>
  import AssetPicker from "../modals/AssetPicker.svelte"
  import Icon from "../../components/Icon.svelte"

  import reloadAlertIcon from "@iconify/icons-mdi/reload-alert"

  export let swap = null
  export let doAssetSwap

  $: ({ stopset, asset: swapAsset, subindex } = swap)
</script>

<AssetPicker rotator={swapAsset.rotator} show={true} close={() => (swap = null)}>
  <svelte:fragment slot="action-name">Swap</svelte:fragment>
  <svelte:fragment slot="title">Swap asset in stop set</svelte:fragment>
  <p class="truncate text-wrap" slot="description">
    Choose from below to swap asset <span class="select-text truncate font-mono">{swapAsset.name}</span>
    in rotator
    <span
      class="badge select-text border-secondary-content font-medium"
      style:background-color={swapAsset.rotator.color.value}
      style:color={swapAsset.rotator.color.content}>{swapAsset.rotator.name}</span
    >
    and stop set
    <span class="select-text">{stopset.name}</span>
    (index {subindex + 1}/{stopset.items.length}).
  </p>

  <button
    class="btn btn-warning"
    tabindex="-1"
    disabled={false}
    slot="action"
    let:asset
    on:click={() => {
      doAssetSwap(stopset, subindex, asset, swapAsset)
      swap = null
    }}
  >
    <Icon icon={reloadAlertIcon} class="h-12 w-12" /> Swap
  </button>
</AssetPicker>
