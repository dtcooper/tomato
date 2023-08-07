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

<div class="h-screen w-screen h-max-screen w-max-screen flex flex-col">
  <Header bind:showSyncModal={showSyncModal} bind:showSettingsModal={showSettingsModal}/>
  <Player/>
</div>
