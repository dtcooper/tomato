<script>
  import { tick } from 'svelte'

  import Modal from "./components/Modal.svelte"

  import cogOutline from "../../assets/icons/mdi-cog-outline.svg"
  import { themeOrder as daisyThemes } from "daisyui/src/theming/themeDefaults"
  import { logout } from "../stores/connection"

  import { config, userConfig } from "../stores/config"

  export let show = true
  let showLogout = false
  let logoutStationName
  let showLogoutError

  const confirmLogout = () => {
    show = showLogoutError = false
    showLogout = true
    logoutStationName = ''
  }

  const focus = async (el) => {
    await tick()
    el.focus()
  }

  const verifyLogout = () => {
    const stationName = logoutStationName.trim().toLowerCase()
    if (stationName) {
      if ($config.STATION_NAME.trim().toLowerCase() === stationName) {
        logout()
      } else {
        logoutStationName = ''
        showLogoutError = true
        document.getElementById('logout-confirm-input').focus()
      }
    }
  }
</script>

<Modal bind:show class="max-w-3xl">
  <svelte:fragment slot="icon">{@html cogOutline}</svelte:fragment>
  <svelte:fragment slot="title">Settings</svelte:fragment>
  <svelte:fragment slot="close-text">Close settings</svelte:fragment>
  <svelte:fragment slot="content">
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
      <button type="button" class="btn btn-error" on:click|preventDefault={confirmLogout}>DANGER: Log out of server</button>
    </div>
  </svelte:fragment>
</Modal>

<Modal bind:show={showLogout} class="max-w-xl">
  <svelte:fragment slot="title"><span class="text-error font-bold">DANGER:</span> Logging out</svelte:fragment>
  <svelte:fragment slot="close-text">Cancel &amp; remain logged in</svelte:fragment>
  <div slot="content" class="flex flex-col gap-2">
    <p>
      Are you <span class="font-bold">100% sure</span> you want to
      <span class="font-bold underline text-error">COMPLETELY LOG OUT</span>
      of the server <span class="italic">"{$config.STATION_NAME}?"</span>
    </p>
    <p>
      If you are, please enter the name of the station exactly as it appears here:
    </p>
    <p class="ml-8 my-2">
      <span class="text-base-100 bg-base-content font-mono p-2">{$config.STATION_NAME}</span>
    </p>
    <p class="mb-5">...and then press the logout button below.</p>
    {#if showLogoutError}
      <div class="text-right text-sm text-error">Wrong station name. Try again.</div>
    {/if}
    <input
      use:focus
      id="logout-confirm-input"
      bind:value={logoutStationName}
      on:input={() => showLogoutError = false}
      type="text"
      placeholder="Enter station name"
      class:input-error={showLogoutError}
      class="input input-bordered input-lg w-full font-mono"
    />
  </div>
  <svelte:fragment slot="extra-buttons">
    <div class="tooltip tooltip-error" data-tip="Are you SURE that you're SURE?!">
      <button type="button" class="btn btn-error" on:click={verifyLogout}>Log out</button>
    </div>
  </svelte:fragment>
</Modal>
