<script>
  import { tick } from "svelte"
  import dayjs from "dayjs"

  import Icon from "../../components/Icon.svelte"
  import Modal from "../../components/Modal.svelte"

  import cogOutline from "@iconify/icons-mdi/cog-outline"
  import moonAndStars from "@iconify/icons-mdi/moon-and-stars"
  import whiteBalanceSunny from "@iconify/icons-mdi/white-balance-sunny"
  import themeLightDark from "@iconify/icons-mdi/theme-light-dark"

  import { IS_DEV, lightTheme, darkTheme } from "../../utils"
  import { db } from "../../stores/db"
  import { settings_descriptions } from "../../../../server/constants.json"
  import { logout, protocolVersion, conn } from "../../stores/connection"
  import { playStatus, speaker, setSpeaker } from "../../stores/player"
  import { config, userConfig, uiModeInfo, isDark } from "../../stores/config"
  import { buttonBoxDetected, buttonBoxVersion, resetButtonBox } from "../../stores/midi"

  export let show = true
  let showLogout = false
  let showServerSettings = false
  let logoutStationName = ""
  let resettingButtonBox = false
  let hardLogout = false
  export let showSyncModal

  $: serverSettings = Object.entries($config).sort()

  const confirmLogout = () => {
    show = hardLogout = false
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

  const themes = [
    ["System default", null, themeLightDark],
    ["Light", lightTheme, whiteBalanceSunny],
    ["Dark", darkTheme, moonAndStars]
  ]

  $: canLogOut = logoutStationName.trim().toLowerCase() === $config.STATION_NAME.trim().toLowerCase()
  $: speakerLocked = show
</script>

<Modal bind:show class="max-w-[52rem] {$isDark ? 'bg-base-100' : 'bg-base-300'}">
  <svelte:fragment slot="icon"><Icon icon={cogOutline} class="h-8 w-8 md:h-12 md:w-12" /></svelte:fragment>
  <svelte:fragment slot="title">Settings</svelte:fragment>
  <svelte:fragment slot="close-text">Close settings</svelte:fragment>
  <div
    class="grid h-0 w-full max-w-full flex-1 grid-cols-[max-content_auto] items-center gap-x-5 gap-y-1.5 overflow-y-auto rounded-xl p-2 {$isDark
      ? 'bg-base-300'
      : 'bg-base-100'}"
    slot="content"
  >
    <div class="flex justify-end text-lg font-bold">User interface mode:</div>
    {#if $config.UI_MODES.length > 1}
      <div class="flex w-max flex-col gap-0.5">
        <div class="tabs-boxed tabs">
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
        {#if $config.UI_MODE_RESET_TIMES && $config.UI_MODE_RESET_TIMES.length > 0}
          <div class="text-center text-xs">
            <strong>NOTE:</strong>
            resets to {uiModeInfo[Math.min(...$config.UI_MODES)]?.name?.toLowerCase()} mode periodically.
          </div>
        {/if}
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
          class="select select-bordered w-full"
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

    <div class="flex justify-end text-lg font-bold">Theme:</div>
    <div class="tabs-boxed tabs w-max">
      {#each themes as [name, theme, icon]}
        <button
          class="tab gap-2"
          class:tab-active={$userConfig.theme === theme}
          on:click={() => ($userConfig.theme = theme)}
        >
          <Icon {icon} class="h-6 w-6" />
          {name}
        </button>
      {/each}
    </div>
    <hr class="divider col-span-2 m-0 h-0 p-0" />

    <div class="flex justify-end text-lg font-bold">Visualize audio:</div>
    <div class="flex w-max items-center justify-center gap-3 text-xl font-bold">
      <span class:text-error={!$userConfig.showViz}>OFF</span>
      <input type="checkbox" class="toggle toggle-success" bind:checked={$userConfig.showViz} />
      <span class:text-success={$userConfig.showViz}>ON</span>
    </div>
    <hr class="divider col-span-2 m-0 h-0 p-0" />

    <div class="flex justify-end text-lg font-bold">MIDI Button box:</div>
    <div class="flex w-max items-center justify-center gap-3 text-xl font-bold">
      <span class:text-error={!$userConfig.enableMIDIButtonBox}>OFF</span>
      <input type="checkbox" class="toggle toggle-success" bind:checked={$userConfig.enableMIDIButtonBox} />
      <span class:text-success={$userConfig.enableMIDIButtonBox}>ON</span>
      {#if $userConfig.enableMIDIButtonBox}
        <span class="text-base font-normal">
          (Button box
          {#if $buttonBoxDetected}
            {#if $buttonBoxVersion}
              <span class="select-text font-mono text-sm tracking-tighter">{$buttonBoxVersion}</span>
            {/if}
            <span class="font-bold text-success">detected</span>!)
            {#if !resettingButtonBox}
              [<button
                class="link-hover link link-primary link-info contents"
                on:click={() => {
                  resettingButtonBox = true
                  resetButtonBox()
                  setTimeout(() => (resettingButtonBox = false), 1500)
                }}>Reset</button
              >]
            {/if}
          {:else}
            <span class="text-error">not detected</span>.)
          {/if}
        </span>
      {/if}
    </div>
    <hr class="divider col-span-2 m-0 h-0 p-0" />

    <div class="flex justify-end text-lg font-bold">Start fullscreen:</div>
    <div class="flex w-max items-center justify-center gap-3 text-xl font-bold">
      <span class:text-error={!$userConfig.startFullscreen}>OFF</span>
      <input type="checkbox" class="toggle toggle-success" bind:checked={$userConfig.startFullscreen} />
      <span class:text-success={$userConfig.startFullscreen}>ON</span>
    </div>
    <hr class="divider col-span-2 m-0 h-0 p-0" />

    {#if IS_DEV}
      <div class="flex justify-end text-lg font-bold">Autoplay (dev only):</div>
      <div class="flex w-max items-center justify-center gap-3 text-xl font-bold">
        <span class:text-error={!$userConfig.autoplay}>OFF</span>
        <input type="checkbox" class="toggle toggle-success" bind:checked={$userConfig.autoplay} />
        <span class:text-success={$userConfig.autoplay}>ON</span>
      </div>
      <hr class="divider col-span-2 m-0 h-0 p-0" />
    {/if}

    <div class="flex justify-end text-lg font-bold">Power save blocker:</div>
    <div
      class:tooltip={$userConfig.tooltips}
      class="tooltip-bottom tooltip-warning flex w-max items-center justify-center gap-3 text-xl"
      data-tip="When set to ON, Tomato attempts to suppress your display from going to sleep and your system from suspending"
    >
      <span class="font-bold" class:text-error={!$userConfig.powerSaveBlocker}>OFF</span>
      <input type="checkbox" class="toggle toggle-success" bind:checked={$userConfig.powerSaveBlocker} />
      <span class="font-bold" class:text-success={$userConfig.powerSaveBlocker}>ON</span>
    </div>
    <hr class="divider col-span-2 m-0 h-0 p-0" />

    <div class="flex justify-end text-lg font-bold">Connection:</div>
    <div class="flex w-full items-baseline gap-1">
      <div class="break-all">
        <span class="select-text font-mono tracking-tight">
          {$conn.username} <span class="select-text font-bold text-info">@</span>
          {$conn.prettyHost}
        </span>
      </div>
      <div class="w-max text-left">
        [<button
          class="link-hover link link-info contents text-left"
          on:click={() => {
            show = false
            showSyncModal = true
          }}>Status</button
        >]
      </div>
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
    <div class="text-md w-max">
      <span class="select-text font-mono tracking-tighter">{TOMATO_VERSION}</span>
      &mdash; protocol: <span class="select-text font-mono tracking-tighter">{protocolVersion}</span>
    </div>
    <hr class="divider col-span-2 m-0 h-0 p-0" />

    <div class="col-span-2 mt-1 flex justify-center">
      <button type="button" class="btn btn-error btn-sm" on:click|preventDefault={confirmLogout} tabindex="-1">
        Click here to <strong class="underline">COMPLETELY LOG OUT</strong> of server
      </button>
    </div>
  </div>
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
    <input
      use:focus
      bind:value={logoutStationName}
      type="text"
      placeholder="Enter station name"
      class="input input-lg input-bordered font-mono"
    />
    <div class="form-control mt-2">
      <label class="label w-max cursor-pointer gap-3 italic" class:text-error={hardLogout} class:font-bold={hardLogout}>
        <input class="checkbox-error checkbox" type="checkbox" bind:checked={hardLogout} />
        <span>
          {#if hardLogout}
            <span class="underline">CAUTION</span>:
          {/if}
          <em>{hardLogout ? "Will" : "Check this box to"} remove all data after logging out{hardLogout ? "!" : "."}</em>
        </span>
      </label>
    </div>
  </div>
  <svelte:fragment slot="extra-buttons">
    <div
      class:tooltip-error={canLogOut}
      class="tooltip"
      data-tip={canLogOut ? "Are you SURE that you're SURE?!" : `Enter "${$config.STATION_NAME}" above!`}
    >
      <button disabled={!canLogOut} type="button" class="btn btn-error" on:click={() => logout(null, hardLogout)}
        >Log out</button
      >
    </div>
  </svelte:fragment>
</Modal>

<Modal bind:show={showServerSettings} class="w-[64rem] max-w-[calc(100vw-2rem)]">
  <svelte:fragment slot="icon"><Icon icon={cogOutline} class="h-8 w-8 md:h-12 md:w-12" /></svelte:fragment>
  <svelte:fragment slot="title">Server settings</svelte:fragment>
  <div
    class="flex max-h-full w-full max-w-full flex-col items-baseline gap-3 overflow-y-auto p-2 text-sm md:text-base"
    slot="content"
  >
    {#each serverSettings as [key, value], i}
      <div class="flex gap-3">
        <span class="font-bold"><span class="select-text font-mono">{key}</span>:</span>
        <span class="select-text font-mono" class:text-success={value === true} class:text-error={value === false}>
          {#if key === "UI_MODES"}
            {value.map((mode) => ["simple", "standard", "advanced"][mode]).join(", ")}
          {:else if key === "UI_MODE_RESET_TIMES"}
            {#if value.length > 0}
              {value.map(([hour, minute]) => dayjs(`${hour}:${minute}`, "H:m").format("h:mma")).join(", ")}
            {:else}
              <em class="text-error">none</em>
            {/if}
          {:else if key === "CLOCK"}
            {#if value}
              {value.replace(/h$/, "-hour display")}
            {:else}
              <span class="text-error">off</span>
            {/if}
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
</Modal>
