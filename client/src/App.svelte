<script>
  import "./styles.css"

  import { conn, login } from "./stores/connection"
  import { restoreAssetsDBFromLocalStorage } from "./stores/db"
  import { userConfig } from "./stores/config"

  import Login from "./Login.svelte"
  import Main from "./main/Main.svelte"

  if ($conn.ready) {
    // Restore if app is loaded in "ready" state
    restoreAssetsDBFromLocalStorage()
    login()
  }
</script>

<div class="h-screen w-screen" data-theme={$userConfig.theme && $userConfig.theme}>
  {#if $conn.reloading}
    <div class="flex h-screen w-screen cursor-wait items-center justify-center text-5xl italic">Logging out...</div>
  {:else if !$conn.ready}
    <Login />
  {:else}
    <Main />
  {/if}
</div>
