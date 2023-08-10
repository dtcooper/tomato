<script>
  import SyncModal from "./SyncModal.svelte"
  import SettingsModal from "./SettingsModal.svelte"
  import Player from "./Player.svelte"
  import Header from "./Header.svelte"

  let showSettingsModal = false
  let showSyncModal = false
  let overdue
</script>

<SyncModal bind:show={showSyncModal} isFromLogin={false} />
<SettingsModal bind:show={showSettingsModal} />

<div class="max-w-screen flex h-screen max-h-screen w-screen flex-col" class:tomato-flash-bg={overdue}>
  <Header bind:showSyncModal bind:showSettingsModal />
  <div
    class="mx-auto grid max-h-fit w-full max-w-4xl flex-1 grid-cols-[3fr,1fr] grid-rows-[max-content,auto] gap-5 bg-base-100 px-2 pt-2"
  >
    <Player bind:overdue />
  </div>
</div>
