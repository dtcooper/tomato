<script>
  import { conn, logout, login } from "./stores/connection"
  import { restoreAssetsDBFromLocalStorage } from "./stores/assets"
  import { config } from "./stores/config"

  import Login from "./Login.svelte"
  import Player from "./Player.svelte"
  import SyncModal from "./SyncModal.svelte"

  if ($conn.ready) {
    // Restore if app is loaded in "ready" state
    restoreAssetsDBFromLocalStorage()
    login()
  }

</script>

{#if $conn.reloading}
  <div class="h-screen w-screen flex items-center justify-center text-5xl italic">Logging out...</div>
{:else}
  {#if !$conn.ready}
    <Login />
  {:else}
    <Player />
  {/if}
{/if}

<style global lang="postcss">
  @import "./fonts.css";

  @tailwind base;
  @tailwind components;
  @tailwind utilities;

  @layer utilities {
    .btn {
      @apply no-animation;
    }
    .btn-warning:hover,
    .btn-info:hover,
    .btn-success:hover,
    .btn-error:hover {
      filter: brightness(110%);
    }
    .btn:active {
      filter: brightness(97%);
    }
  }

  :root {
    font-size: 0.9em;
  }

  svg {
    @apply h-16 w-16;
  }
</style>
