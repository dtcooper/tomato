<script>
  import SyncModal from "./SyncModal.svelte"
  import Player from "./Player.svelte"
  import Header from "./Header.svelte"

  let showSyncModal = false

</script>

<div class="h-screen w-screen h-max-screen w-max-screen">
  <SyncModal bind:show={showSyncModal} />
  <Header/>
  <Player/>
</div>
