<script>
  import { blockSpacebarPlay } from "../stores/player"

  export let canDismiss = true
  export let show = true

  const close = () => {
    show = false
  }

  // Block spacebar play when any modal is active
  $: $blockSpacebarPlay = show
</script>

{#if show}
  <dialog
    class="modal h-screen max-h-screen bg-black bg-opacity-50 !outline-0"
    tabindex="-1"
    open
    on:submit|preventDefault={() => false}
  >
    <form
      method="dialog"
      class="{$$props.class || 'max-w-xl'} modal-box flex max-h-[calc(100vh-2rem)] flex-col overflow-y-visible"
    >
      {#if canDismiss}
        <button
          type="button"
          class="btn btn-circle btn-neutral btn-sm fixed right-2 top-2 z-50 text-xl"
          tabindex="-1"
          on:click|preventDefault={close}>✕</button
        >
      {/if}
      <div class="flex h-0 flex-1 flex-col items-center justify-center gap-y-4">
        <div class="flex items-center gap-x-5">
          <slot name="icon" />
          <h2 class="font-mono text-2xl font-bold italic md:text-3xl"><slot name="title" /></h2>
        </div>
        <slot name="content" />
        {#if canDismiss || $$slots["extra-buttons"]}
          <div class="mt-3 flex w-full justify-end gap-x-2">
            <slot name="extra-buttons" />
            {#if canDismiss}
              <button type="button" class="btn btn-info" on:click|preventDefault={close}>
                <slot name="close-text">Close</slot>
              </button>
            {/if}
          </div>
        {/if}
      </div>
    </form>
    {#if canDismiss}
      <form method="dialog" class="modal-backdrop">
        <button type="button" on:click|preventDefault={close} tabindex="-1" />
      </form>
    {/if}
  </dialog>
{/if}
