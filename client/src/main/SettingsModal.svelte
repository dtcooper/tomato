<script>
  import cogOutline from "../../assets/icons/mdi-cog-outline.svg"

  import { userConfig } from "../stores/config"

  export let show = true

  const close = () => show = false
</script>

{#if show}
  <dialog
    class="modal bg-black bg-opacity-50"
    open
  >
    <form
      method="dialog"
      class="modal-box max-w-3xl flex flex-col items-center justify-center gap-y-4"
    >
      <button class="btn btn-circle btn-ghost btn-sm absolute right-2 top-2" on:click|preventDefault={close}>✕</button>
      <div class="flex items-center gap-x-3">
        {@html cogOutline}
        <h2 class="text-3xl">Settings</h2>
      </div>
      <div class="grid grid-cols-[max-content_1fr] w-full gap-3">
        <div class="text-right text-lg font-bold flex items-center">User Interface mode:</div>
        <select class="select select-lg select-bordered" on:change={(e) => $userConfig.uiMode = e.target.value} >
          {#each ["Simple", "Standard", "Advanced"] as uiMode, index}
            <option value={index} selected={index === $userConfig.uiMode}>
              {uiMode}
            </option>
          {/each}
        </select>

        <div class="text-right">Label:</div>
        <div class="bg-red-200">asdf<br>asdf<br>asdf</div>
      </div>
    </form>
    <form method="dialog" class="modal-backdrop">
      <button on:click|preventDefault={close}>close</button>
    </form>
  </dialog>
{/if}
