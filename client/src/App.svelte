<script>
  import { authenticated, logout, login, auth, ready } from "./stores/connection"
  import { restoreDBFromLocalStorage } from "./stores/assets"
  import { config } from "./stores/config"

  import Login from "./Login.svelte"

  if ($authenticated) {
    restoreDBFromLocalStorage()
    login()
  }

  if ($ready) {
  }
</script>

<div class="absolute pl-3 pt-2 text-xs">
  <pre>{JSON.stringify($auth, Object.keys($auth).sort(), 2)}</pre>
  <pre>{JSON.stringify($config, Object.keys($config).sort(), 2)}</pre>
</div>
{#if !$authenticated}
  <Login />
{:else}
  <div class="flex h-screen flex-col items-center justify-center">
    <h1 class="p-6 text-xl italic">Logged in!</h1>
    <div><button class="btn btn-primary" on:click={logout}>Logout</button></div>
  </div>
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
</style>
