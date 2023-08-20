<script>
  import { tick } from "svelte"

  import Icon from "../components/Icon.svelte"
  import Modal from "../components/Modal.svelte"

  import cogOutline from "@iconify/icons-mdi/cog-outline"

  import { IS_DEV } from "../utils"
  import { db } from "../stores/db"
  import { logout, protocolVersion, conn } from "../stores/connection"
  import { playStatus, speaker, setSpeaker } from "../stores/player"
  import { config, userConfig } from "../stores/config"

  // TODO: host error seems to show when logging, in particular if you press logout when disconnected

  export let show = true
  let showLogout = false
  let logoutStationName
  let showLogoutError

  const confirmLogout = () => {
    show = showLogoutError = false
    showLogout = true
    logoutStationName = ""
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
        logoutStationName = ""
        showLogoutError = true
        document.getElementById("logout-confirm-input").focus()
      }
    }
  }

  const uiModeStrings = ["Simple", "Standard", "Advanced"]

  $: speakerLocked = show
</script>

<Modal bind:show class="max-w-3xl">
  <svelte:fragment slot="icon"><Icon icon={cogOutline} /></svelte:fragment>
  <svelte:fragment slot="title">Settings</svelte:fragment>
  <svelte:fragment slot="close-text">Close settings</svelte:fragment>
  <svelte:fragment slot="content">
    <div class="grid w-full max-w-full grid-cols-[max-content_auto] items-baseline gap-3">
      <div class="flex items-center justify-end text-lg font-bold">User interface mode:</div>
      <div class="tabs-boxed tabs w-max">
        {#each $config.UI_MODES as uiMode}
          <button
            class="tab"
            class:tab-active={uiMode === $userConfig.uiMode}
            on:click={() => ($userConfig.uiMode = uiMode)}
          >
            {uiModeStrings[uiMode]}
          </button>
        {/each}
      </div>

      <div class="flex justify-end text-lg font-bold">Audio output device:</div>
      <div class="flex flex-col items-end">
        <div
          class:tooltip={speakerLocked}
          class="tooltip-warning tooltip-bottom w-full"
          data-tip="Unlock device by clicking below"
        >
          <select
            class="select select-bordered select-lg w-full"
            on:change={(e) => setSpeaker(e.target.value)}
            disabled={speakerLocked}
          >
            {#each $playStatus.speakers as [id, name]}
              <option value={id} selected={id === $speaker}>{name}</option>
            {/each}
          </select>
        </div>
        <div class="w-max pr-5 pt-1 text-xs">
          <button
            class="link-hover link"
            class:link-primary={!speakerLocked}
            class:link-warning={speakerLocked}
            on:click={() => (speakerLocked = !speakerLocked)}
          >
            {speakerLocked ? "Unl" : "L"}ock output device
          </button>
        </div>
      </div>

      <!-- svelte-ignore missing-declaration -->
      {#if IS_DEV}
        <div class="flex items-center justify-end text-lg font-bold">Autoplay (dev only):</div>
        <div class="flex w-max items-center justify-center gap-4 text-xl font-bold">
          <span class:text-error={!$userConfig.autoplay}>OFF</span>
          <input type="checkbox" class="toggle toggle-success toggle-lg" bind:checked={$userConfig.autoplay} />
          <span class:text-success={$userConfig.autoplay}>ON</span>
        </div>
      {/if}

      <div class="flex items-center justify-end text-lg font-bold">Power save blocker:</div>
      <div
        class="tooltip tooltip-warning tooltip-bottom flex w-max items-center justify-center gap-4 text-xl"
        data-tip="When set to ON, Tomato attempts to suppress your display from going to sleep and your system from suspending"
      >
        <span class="font-bold" class:text-error={!$userConfig.powerSaveBlocker}>OFF</span>
        <input type="checkbox" class="toggle toggle-success toggle-lg" bind:checked={$userConfig.powerSaveBlocker} />
        <span class="font-bold" class:text-success={$userConfig.powerSaveBlocker}>ON</span>
      </div>

      <div class="flex justify-end text-lg font-bold">Connection:</div>
      <div class="w-full truncate">
        <span class="font-mono text-sm">
          {$conn.username} <span class="font-bold text-info">@</span>
          {$conn.prettyHost}
        </span>
      </div>

      <div class="flex justify-end text-lg font-bold">Broadcast compression:</div>
      <div class="w-full text-lg">
        <span
          class="font-bold"
          class:text-error={!$config.BROADCAST_COMPRESSION}
          class:text-success={$config.BROADCAST_COMPRESSION}
        >
          {$config.BROADCAST_COMPRESSION ? "Enabled" : "Disabled"}
        </span>
        (configured on server)
      </div>

      <div class="flex justify-end text-lg font-bold">Station admin site:</div>
      <a class="link-hover link-info link text-lg" href={$db.host}>Open in your web browser</a>

      <div class="flex justify-end text-lg font-bold">Version:</div>
      <!-- svelte-ignore missing-declaration-->
      <div class="text-md w-max">{TOMATO_VERSION} / protocol: {protocolVersion}</div>
    </div>

    <div class="col-span-2">
      <button type="button" class="btn btn-error btn-sm" on:click|preventDefault={confirmLogout} tabindex="-1">
        DANGER: Log out of server
      </button>
    </div>
  </svelte:fragment>
</Modal>

<Modal bind:show={showLogout}>
  <svelte:fragment slot="title"><span class="font-bold text-error">DANGER:</span> Logging out</svelte:fragment>
  <svelte:fragment slot="close-text">Cancel &amp; remain logged in</svelte:fragment>
  <div slot="content" class="flex flex-col gap-2">
    <p>
      Are you <span class="font-bold">100% sure</span> you want to
      <span class="font-bold text-error underline">COMPLETELY LOG OUT</span>
      of the server <span class="italic">"{$config.STATION_NAME}?"</span>
    </p>
    <p>If you are, please enter the name of the station exactly as it appears here:</p>
    <p class="my-2 ml-8">
      <span class="bg-base-content p-2 font-mono text-base-100">{$config.STATION_NAME}</span>
    </p>
    <p class="mb-5">...and then press the logout button below.</p>
    {#if showLogoutError}
      <div class="text-right text-sm text-error">Wrong station name. Try again.</div>
    {/if}
    <input
      use:focus
      id="logout-confirm-input"
      bind:value={logoutStationName}
      on:input={() => (showLogoutError = false)}
      type="text"
      placeholder="Enter station name"
      class:input-error={showLogoutError}
      class="input input-bordered input-lg font-mono"
    />
  </div>
  <svelte:fragment slot="extra-buttons">
    <div class="tooltip tooltip-error" data-tip="Are you SURE that you're SURE?!">
      <button type="button" class="btn btn-error" on:click={verifyLogout}>Log out</button>
    </div>
  </svelte:fragment>
</Modal>
