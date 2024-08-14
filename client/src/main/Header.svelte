<script>
  import Icon from "../components/Icon.svelte"

  import { tomatoIcon } from "../utils"
  import lanConnect from "@iconify/icons-mdi/lan-connect"
  import lanDisconnect from "@iconify/icons-mdi/lan-disconnect"
  import autorenew from "@iconify/icons-mdi/autorenew"
  import cogOutline from "@iconify/icons-mdi/cog-outline"
  import fullscreenExit from "@iconify/icons-mdi/fullscreen-exit"
  import fullscreenIcon from "@iconify/icons-mdi/fullscreen"
  import tooltipRemoveOutline from "@iconify/icons-mdi/tooltip-remove-outline"
  import tooltipCheckOutline from "@iconify/icons-mdi/tooltip-check-outline"
  import seedIcon from "@iconify/icons-mdi/seed-outline"
  import { conn } from "../stores/connection"
  import { config, userConfig, isFullscreen, setFullscreen, uiModeInfo } from "../stores/config"
  import { syncProgress } from "../stores/db"

  export let showSyncModal = false
  export let showSettingsModal = false

  let nextUiMode = 0

  $: {
    let nextIndex = $config.UI_MODES.indexOf($userConfig.uiMode)
    if (nextIndex > -1) {
      nextIndex = (nextIndex + 1) % $config.UI_MODES.length
      nextUiMode = $config.UI_MODES[nextIndex]
    }
  }
</script>

<div class="col-span-3 flex flex-col gap-6">
  <div class="flex items-center justify-between bg-base-200 px-5 py-2">
    <div class="mr-2 flex flex-1 items-center gap-3 font-mono text-2xl italic md:text-3xl">
      <Icon icon={tomatoIcon} class="h-10 w-10 md:h-12 md:w-12" shape-rendering="crispEdges" viewBox="0 -.5 16 16" />
      <div class="w-0 flex-1 truncate">
        {$config.STATION_NAME}
      </div>
    </div>
    <div class="flex items-center gap-2 md:gap-3">
      {#if $config.UI_MODES.includes(0) && $userConfig.uiMode >= 1}
        <button class="btn btn-accent gap-0" on:click={() => ($userConfig.uiMode = 0)} tabindex="-1">
          &ShortLeftArrow; Back to <Icon icon={seedIcon} class="ml-1 mr-0.5 h-6 w-6" /> simple view
        </button>
      {/if}
      <div
        class="tooltip tooltip-bottom tooltip-info flex"
        data-tip={`${$isFullscreen ? "Exit" : "Enter"} fullscreen mode`}
      >
        <button class="btn btn-circle btn-ghost" on:click={() => setFullscreen(!$isFullscreen)} tabindex="-1">
          <Icon icon={$isFullscreen ? fullscreenExit : fullscreenIcon} class="h-8 w-8" />
        </button>
      </div>
      {#if $userConfig.uiMode === 2}
        <div
          class="tooltip tooltip-bottom tooltip-info flex"
          data-tip={`${$userConfig.tooltips ? "Disable" : "Enable"} tooltips`}
        >
          <button
            class="btn btn-circle btn-ghost"
            on:click={() => ($userConfig.tooltips = !$userConfig.tooltips)}
            tabindex="-1"
          >
            <Icon icon={$userConfig.tooltips ? tooltipCheckOutline : tooltipRemoveOutline} class="h-8 w-8" />
          </button>
        </div>
      {/if}
      {#if $config.UI_MODES.length > 1}
        <div class="tooltip tooltip-bottom tooltip-info flex" data-tip={`${uiModeInfo[$userConfig.uiMode].name} view`}>
          <button class="btn btn-circle btn-ghost" on:click={() => ($userConfig.uiMode = nextUiMode)} tabindex="-1">
            <Icon icon={uiModeInfo[$userConfig.uiMode].icon} class="h-8 w-8" />
          </button>
        </div>
      {/if}
      <div
        class="tooltip tooltip-bottom tooltip-info flex"
        data-tip={!$conn.connected ? "Disconnected" : $syncProgress.syncing ? "Synchronizing" : "Connected"}
      >
        <button
          class="btn btn-circle btn-ghost flex items-center justify-center overflow-hidden"
          on:click={() => (showSyncModal = true)}
          class:!bg-transparent={$userConfig.uiMode === 0}
          disabled={$userConfig.uiMode === 0}
          tabindex="-1"
        >
          {#if !$conn.connected}
            <Icon icon={lanDisconnect} class="h-8 w-8 text-error" />
          {:else if $syncProgress.syncing}
            <Icon icon={autorenew} class="h-8 w-8 animate-[spin_2s_linear_infinite] text-info" />
          {:else}
            <Icon icon={lanConnect} class="h-8 w-8 text-success" />
          {/if}
        </button>
      </div>
      <div class="tooltip tooltip-bottom tooltip-info flex" data-tip="Settings">
        <button class="btn btn-circle btn-ghost" on:click={() => (showSettingsModal = true)} tabindex="-1">
          <Icon icon={cogOutline} class="h-8 w-8" />
        </button>
      </div>
    </div>
  </div>
</div>
