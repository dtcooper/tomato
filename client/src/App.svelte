<script>
  import { authenticated, logout, login, auth } from "./stores/connection"

  import Login from "./Login.svelte"

  if ($authenticated) {
    login()
  }
</script>

<pre class="absolute pl-4 pt-2 text-sm">{JSON.stringify($auth, Object.keys($auth).sort(), 2)}</pre>
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
