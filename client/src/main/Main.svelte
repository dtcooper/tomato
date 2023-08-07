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

<div class="h-max-screen w-max-screen flex h-screen w-screen flex-col">
  <Header bind:showSyncModal bind:showSettingsModal />
  <Player />
</div>
