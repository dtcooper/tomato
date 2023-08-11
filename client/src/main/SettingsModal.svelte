<script>
  import { tick } from "svelte"

  import Icon from "../components/Icon.svelte"
  import Modal from "../components/Modal.svelte"

  import cogOutline from "@iconify/icons-mdi/cog-outline"

  import { db } from "../stores/db"
  import { logout, protocolVersion } from "../stores/connection"
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
</script>

<Modal bind:show class="max-w-3xl">
  <svelte:fragment slot="icon"><Icon icon={cogOutline} /></svelte:fragment>
  <svelte:fragment slot="title">Settings</svelte:fragment>
  <svelte:fragment slot="close-text">Close settings</svelte:fragment>
  <svelte:fragment slot="content">
    <div class="grid grid-cols-[max-content_1fr] items-baseline gap-3">
      <div class="flex items-center justify-end text-lg font-bold">User Interface mode:</div>
      <div class="tabs-boxed tabs w-max">
        {#each ["Simple", "Standard", "Advanced"] as uiMode, index}
          {#if $config.UI_MODES.indexOf(index) !== -1}
            <button
              class="tab"
              class:tab-active={index === $userConfig.uiMode}
              on:click={() => ($userConfig.uiMode = index)}>{uiMode}</button
            >
          {/if}
        {/each}
      </div>

      <div class="flex justify-end text-lg font-bold">Audio Output Device:</div>
      <select class="select select-bordered select-lg" on:change={(e) => setSpeaker(e.target.value)}>
        {#each $playStatus.speakers as [id, name]}
          <option value={id} selected={id === $speaker}>{name}</option>
        {/each}
      </select>

      <!-- svelte-ignore missing-declaration -->
      {#if IS_DEV}
        <div class="flex justify-end text-lg font-bold">Autoplay (dev only):</div>
        <div class="flex w-max items-center justify-center gap-4 font-mono text-xl font-bold">
          <span class:text-error={!$userConfig.autoplay}>OFF</span>
          <input type="checkbox" class="toggle toggle-success toggle-lg" bind:checked={$userConfig.autoplay} />
          <span class:text-success={$userConfig.autoplay}>ON</span>
        </div>
      {/if}

      <div class="flex justify-end text-lg font-bold">Broadcast Compression:</div>
      <div
        class="w-max text-lg"
        class:text-error={!$config.BROADCAST_COMPRESSION}
        class:text-success={$config.BROADCAST_COMPRESSION}
      >
        {$config.BROADCAST_COMPRESSION ? "Enabled" : "Disabled"}
      </div>

      <div class="flex justify-end text-lg font-bold">Station Admin:</div>
      <a class="link-hover link-primary link text-lg" href={$db.host}>Open in your web browser</a>

      <div class="flex justify-end text-lg font-bold">Version:</div>
      <!-- svelte-ignore missing-declaration-->
      <div class="text-md w-max">{TOMATO_VERSION} / protocol: {protocolVersion}</div>
    </div>

    <div class="col-span-2">
      <button type="button" class="btn btn-error" on:click|preventDefault={confirmLogout}>
        DANGER: Log out of server</button
      >
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
