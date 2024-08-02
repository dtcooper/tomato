<script>
  import { noop } from "svelte/internal"
  import Icon from "../../components/Icon.svelte"
  import Modal from "../../components/Modal.svelte"

  import musicIcon from "@iconify/icons-mdi/music"
  import { prettyDuration } from "../../utils"

  export let show = false
  export let rotator = null
  export let close = noop

  $: assets = rotator?.assets.sort((a, b) => a.name.toLowerCase().localeCompare(b.name.toLowerCase()))

  $: if (!show) {
    close()
  }
</script>

<Modal bind:show class="max-w-6xl" title="Play Asset">
  <svelte:fragment slot="icon">
    <Icon icon={musicIcon} class="h-8 w-8 md:h-12 md:w-12" />
  </svelte:fragment>
  <svelte:fragment slot="title"><slot name="title" /></svelte:fragment>
  <div slot="content" class="flex h-0 w-full flex-1 flex-col gap-2">
    <div><slot name="description" /></div>
    <div class="min-h-[340px] flex-1 overflow-y-auto">
      <div class="relative grid grid-cols-[max-content,max-content,auto,max-content,max-content] rounded">
        <div class="sticky top-0 bg-base-100 p-2 font-bold"><slot name="action-name" /></div>
        <div class="sticky top-0 bg-base-100 p-2 font-bold">Length</div>
        <div class="sticky top-0 bg-base-100 p-2 font-bold">Name</div>
        <div class="sticky top-0 bg-base-100 p-2 font-bold">Is Airing?</div>
        <div class="sticky top-0 bg-base-100 p-2 font-bold">Alternates?</div>

        {#each assets as asset, i}
          {@const oddRow = i % 2 == 1}
          <div class:bg-base-200={oddRow} class="flex items-center border-b border-base-content p-1.5">
            <slot name="action" {asset} />
          </div>
          <div
            class:bg-base-200={oddRow}
            class="flex items-center justify-end border-b border-base-content p-1.5 font-mono font-bold"
          >
            {prettyDuration(asset.duration)}
          </div>
          <div
            class:bg-base-200={oddRow}
            class="flex select-text items-center overflow-x-hidden border-b border-base-content p-1.5"
          >
            <span class="select-text truncate">{asset.name}</span>
          </div>
          <div class:bg-base-200={oddRow} class="flex items-center border-b border-base-content p-1.5">
            {#if asset.isAiring()}
              <span class="badge badge-success">Airing</span>
            {:else}
              <span class="badge badge-error">Not airing</span>
            {/if}
          </div>
          <div class:bg-base-200={oddRow} class="flex items-center border-b border-base-content p-1.5">
            {#if asset.alternates.length > 0}
              <span class="badge badge-info">{asset.alternates.length} alternates</span>
            {:else}
              <em>None</em>
            {/if}
          </div>
        {/each}
      </div>
    </div>
  </div>
</Modal>
