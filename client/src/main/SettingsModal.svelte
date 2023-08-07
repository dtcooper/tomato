<script>
  import cogOutline from "../../assets/icons/mdi-cog-outline.svg"
  import { ipcRenderer } from "electron"
  import { themeOrder as daisyThemes } from "daisyui/src/theming/themeDefaults"
  import { logout } from "../stores/connection"

  import { userConfig } from "../stores/config"

  export let show = true

  const close = () => (show = false)

  const confirmLogout = () => {
    // TODO confirm this
    logout()
  }
</script>

{#if show}
  <dialog class="modal bg-black bg-opacity-50" open>
    <form method="dialog" class="modal-box flex max-w-3xl flex-col items-center justify-center gap-y-4">
      <button class="btn btn-circle btn-ghost btn-sm absolute right-2 top-2 text-xl" on:click|preventDefault={close}
        >✕</button
      >
      <div class="flex items-center gap-x-3">
        {@html cogOutline}
        <h2 class="text-3xl">Settings</h2>
      </div>
      <div class="grid w-full grid-cols-[max-content_1fr] gap-3">
        <div class="flex items-center text-right text-lg font-bold">User Interface mode:</div>
        <select class="select select-bordered select-lg" on:change={(e) => ($userConfig.uiMode = e.target.value)}>
          {#each ["Simple", "Standard", "Advanced"] as uiMode, index}
            <option value={index} selected={index === $userConfig.uiMode}>
              {uiMode}
            </option>
          {/each}
        </select>

        <div class="flex items-center text-right text-lg font-bold">Theme:</div>
        <select class="select select-bordered select-lg" on:change={(e) => ($userConfig.theme = e.target.value)}>
          {#each daisyThemes as theme}
            <option value={theme} selected={$userConfig.theme === theme}>
              {theme.charAt(0).toUpperCase()}{theme.slice(1)}
            </option>
          {/each}
        </select>
      </div>

      <div class="col-span-2">
        <button class="btn btn-error" on:click|preventDefault={confirmLogout}>DANGER: Log out of server</button>
      </div>

      <div class="w-full text-right">
        <button class="btn btn-primary btn-lg" on:click|preventDefault={close}>Close settings</button>
      </div>
    </form>
    <form method="dialog" class="modal-backdrop">
      <button on:click|preventDefault={close}>close</button>
    </form>
  </dialog>
{/if}
