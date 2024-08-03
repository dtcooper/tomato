<script>
  import { tick } from "svelte"
  import dayjs from "dayjs"

  import Icon from "../../components/Icon.svelte"
  import Modal from "../../components/Modal.svelte"

  import cogOutline from "@iconify/icons-mdi/cog-outline"

  import { IS_DEV } from "../../utils"
  import { db } from "../../stores/db"
  import { settings_descriptions } from "../../../../server/constants.json"
  import { logout, protocolVersion, conn } from "../../stores/connection"
  import { playStatus, speaker, setSpeaker } from "../../stores/player"
  import { config, userConfig, uiModeInfo } from "../../stores/config"

  // TODO: host error seems to show when logging, in particular if you press logout when disconnected

  export let show = true
  let showLogout = false
  let showServerSettings = false
  let logoutStationName = ""
  let showLogoutError

  $: serverSettings = Object.entries($config).sort()

  const confirmLogout = () => {
    show = showLogoutError = false
    showLogout = true
    logoutStationName = ""
  }

  const openServerSettings = () => {
    show = false
    showServerSettings = true
  }

  const focus = async (el) => {
    await tick()
    el.focus()
  }

  $: canLogOut = logoutStationName.trim().toLowerCase() === $config.STATION_NAME.trim().toLowerCase()

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

  $: speakerLocked = show
</script>

<Modal bind:show class="max-w-3xl">
  <svelte:fragment slot="icon"><Icon icon={cogOutline} class="h-8 w-8 md:h-12 md:w-12" /></svelte:fragment>
  <svelte:fragment slot="title">Settings</svelte:fragment>
  <svelte:fragment slot="close-text">Close settings</svelte:fragment>
  <svelte:fragment slot="content">
    <div class="grid w-full max-w-full grid-cols-[max-content_auto] items-center gap-x-5 gap-y-2">
      <div class="flex justify-end text-lg font-bold">User interface mode:</div>
      {#if $config.UI_MODES.length > 1}
        <div class="tabs-boxed tabs w-max">
          {#each $config.UI_MODES as uiMode}
            <button
              class="tab gap-2"
              class:tab-active={uiMode === $userConfig.uiMode}
              on:click={() => ($userConfig.uiMode = uiMode)}
            >
              <Icon icon={uiModeInfo[uiMode].icon} class="h-6 w-6" />
              {uiModeInfo[uiMode].name}
            </button>
          {/each}
        </div>
      {:else}
        <div class="text-md flex w-max items-center gap-2">
          <Icon icon={uiModeInfo[$userConfig.uiMode].icon} class="h-6 w-6 text-info" />
          <b class="text-info">{uiModeInfo[$userConfig.uiMode].name}</b>
          <em>(Not configurable)</em>
        </div>
      {/if}
      <hr class="divider col-span-2 m-0 h-0 p-0" />

      <div class="flex justify-end text-lg font-bold">Audio output device:</div>
      <div class="flex flex-col items-end">
        <div
          class:tooltip={speakerLocked && $userConfig.tooltips}
          class="tooltip-bottom tooltip-warning w-full"
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
      <hr class="divider col-span-2 m-0 h-0 p-0" />

      <div class="flex justify-end text-lg font-bold">Button box:</div>
      <div class="flex w-max items-center justify-center gap-4 text-xl font-bold">
        <span class:text-error={!$userConfig.enableMIDIButtonBox}>OFF</span>
        <input type="checkbox" class="toggle toggle-success toggle-lg" bind:checked={$userConfig.enableMIDIButtonBox} />
        <span class:text-success={$userConfig.enableMIDIButtonBox}>ON</span>
      </div>
      <hr class="divider col-span-2 m-0 h-0 p-0" />

      <!-- svelte-ignore missing-declaration -->
      {#if IS_DEV}
        <div class="flex justify-end text-lg font-bold">Autoplay (dev only):</div>
        <div class="flex w-max items-center justify-center gap-4 text-xl font-bold">
          <span class:text-error={!$userConfig.autoplay}>OFF</span>
          <input type="checkbox" class="toggle toggle-success toggle-lg" bind:checked={$userConfig.autoplay} />
          <span class:text-success={$userConfig.autoplay}>ON</span>
        </div>
        <hr class="divider col-span-2 m-0 h-0 p-0" />
      {/if}

      <div class="flex justify-end text-lg font-bold">Power save blocker:</div>
      <div
        class:tooltip={$userConfig.tooltips}
        class="tooltip-bottom tooltip-warning flex w-max items-center justify-center gap-4 text-xl"
        data-tip="When set to ON, Tomato attempts to suppress your display from going to sleep and your system from suspending"
      >
        <span class="font-bold" class:text-error={!$userConfig.powerSaveBlocker}>OFF</span>
        <input type="checkbox" class="toggle toggle-success toggle-lg" bind:checked={$userConfig.powerSaveBlocker} />
        <span class="font-bold" class:text-success={$userConfig.powerSaveBlocker}>ON</span>
      </div>
      <hr class="divider col-span-2 m-0 h-0 p-0" />

      <div class="flex justify-end text-lg font-bold">Connection:</div>
      <div class="w-full truncate">
        <span class="select-text font-mono text-sm">
          {$conn.username} <span class="select-text font-bold text-info">@</span>
          {$conn.prettyHost}
        </span>
      </div>
      <hr class="divider col-span-2 m-0 h-0 p-0" />

      <div class="flex justify-end text-lg font-bold">Server settings:</div>
      <div>
        <button class="link-hover link link-info text-lg" on:click|preventDefault={openServerSettings}>
          Click to view settings from server
        </button>
      </div>
      <hr class="divider col-span-2 m-0 h-0 p-0" />

      <div class="flex justify-end text-lg font-bold">Station admin site:</div>
      <div><a class="link-hover link link-info text-lg" href={$db.host}>Click to open in web browser</a></div>
      <hr class="divider col-span-2 m-0 h-0 p-0" />

      <div class="flex justify-end text-lg font-bold">Version:</div>
      <!-- svelte-ignore missing-declaration-->
      <div class="text-md w-max">{TOMATO_VERSION} / protocol: {protocolVersion}</div>
      <hr class="divider col-span-2 m-0 h-0 p-0" />

      <div class="col-span-2 flex justify-center">
        <button type="button" class="btn btn-error btn-sm" on:click|preventDefault={confirmLogout} tabindex="-1">
          Click here to <strong class="underline">COMPLETELY LOG OUT</strong> of server
        </button>
      </div>
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
      <span class="select-text bg-base-content p-2 font-mono text-base-100">{$config.STATION_NAME}</span>
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
      class="input input-lg input-bordered font-mono"
    />
  </div>
  <svelte:fragment slot="extra-buttons">
    <div class:tooltip={canLogOut} class="tooltip-error" data-tip="Are you SURE that you're SURE?!">
      <button disabled={!canLogOut} type="button" class="btn btn-error" on:click={() => logout()}>Log out</button>
    </div>
  </svelte:fragment>
</Modal>

<Modal bind:show={showServerSettings} class="w-[64rem] max-w-[calc(100vw-2rem)]">
  <svelte:fragment slot="icon"><Icon icon={cogOutline} class="h-8 w-8 md:h-12 md:w-12" /></svelte:fragment>
  <svelte:fragment slot="title">Server Settings</svelte:fragment>
  <svelte:fragment slot="content">
    <div
      class="flex max-h-full w-full max-w-full flex-col items-baseline gap-3 overflow-y-auto p-2 text-sm md:text-base"
    >
      {#each serverSettings as [key, value], i}
        <div class="flex gap-3">
          <span class="font-bold"><span class="select-text font-mono">{key}</span>:</span>
          <span class="select-text font-mono" class:text-success={value === true} class:text-error={value === false}>
            {#if key === "UI_MODES"}
              {value.map((mode) => ["simple", "standard", "advanced"][mode]).join(", ")}
            {:else if key === "UI_MODE_RESET_TIMES"}
              {value.map(([hour, minute]) => dayjs(`${hour}:${minute}`, "H:m").format("h:mma")).join(", ")}
            {:else}
              {value}{#if value === 0}<span class="text-error">&nbsp;(disabled)</span>{/if}
            {/if}
          </span>
        </div>
        {#if settings_descriptions[key]}
          <div class="text-sm">{settings_descriptions[key]}</div>
        {/if}
        {#if i < serverSettings.length - 1}
          <div class="divider my-1"></div>
        {/if}
      {/each}
    </div>
  </svelte:fragment>
</Modal>
