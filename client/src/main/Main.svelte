<script>
  import { singlePlayRotators } from "../stores/single-play-rotators"

  import SyncModal from "./modals/Sync.svelte"
  import SettingsModal from "./modals/Settings.svelte"
  import Player from "./Player.svelte"
  import Header from "./Header.svelte"
  import Alerts from "./Alerts.svelte"
  import Clock from "./Clock.svelte"

  let showSettingsModal = false
  let showSyncModal = false
  let overdue

  $: isWide = $singlePlayRotators.enabled
</script>

<SyncModal bind:show={showSyncModal} isFromLogin={false} />
<SettingsModal bind:show={showSettingsModal} bind:showSyncModal />

<Alerts />

<div class="max-w-screen flex h-screen max-h-screen w-screen flex-col" class:tomato-flash-bg={overdue}>
  <Header bind:showSyncModal bind:showSettingsModal />
  <Clock {isWide} />
  <div
    class="mx-auto grid max-h-fit w-full flex-1 grid-cols-[2fr,1fr] grid-rows-[max-content,auto] gap-5 bg-base-100 px-2 pt-2"
    class:max-w-4xl={!isWide}
    class:max-w-7xl={isWide}
  >
    <Player bind:overdue />
  </div>
</div>
