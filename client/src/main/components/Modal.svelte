<script>
  import { trapFocus } from 'trap-focus-svelte'

  export let canDismiss = true
  export let show = true

  const close = () => {
    show = false
  }
</script>

{#if show}
  <dialog class="modal bg-black bg-opacity-50 focus:border-0" tabindex="-1" open use:trapFocus on:submit|preventDefault={() => false}>
      <form method="dialog" class={`${$$props.class || ''} modal-box flex flex-col items-center justify-center gap-y-4`}>
        {#if canDismiss}
          <button type="button" class="btn btn-circle btn-ghost btn-sm absolute right-2 top-2 text-xl" on:click|preventDefault={close}>✕</button>
        {/if}
        <div class="flex items-center gap-x-3">
          <slot name="icon" />
          <h2 class="text-3xl"><slot name="title" /></h2>
        </div>
        <slot name="content" />
        {#if canDismiss || $$slots['extra-buttons']}
          <div class="w-full text-right space-x-2 mt-3">
            <slot name="extra-buttons"/>
            {#if canDismiss}
              <button type="button" class="btn btn-info" on:click|preventDefault={close}>
                <slot name="close-text">Close</slot>
              </button>
            {/if}
          </div>
        {/if}
      </form>
      {#if canDismiss}
        <form method="dialog" class="modal-backdrop">
          <button type="button" on:click|preventDefault={close} tabindex="-1" ></button>
        </form>
      {/if}
  </dialog>
{/if}
