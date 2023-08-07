<script>
  import SyncModal from "./SyncModal.svelte"
  import SettingsModal from "./SettingsModal.svelte"
  import Player from "./Player.svelte"
  import Header from "./Header.svelte"

  let showSettingsModal = false
  let showSyncModal = false
</script>

<SyncModal bind:show={showSyncModal} />
<SettingsModal bind:show={showSettingsModal} />

<div class="max-h-screen max-w-screen h-screen w-screen flex flex-col gap-2">
  <Header bind:showSyncModal bind:showSettingsModal />
  <div class="w-full max-w-4xl grid mx-auto flex-1 grid-cols-[2fr,1fr] grid-rows-[max-content,auto] gap-2 px-2 max-h-fit">
    <Player />
  </div>
</div>
