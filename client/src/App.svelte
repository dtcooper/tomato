<script>
  import { conn, login } from "./stores/connection"
  import { restoreAssetsDBFromLocalStorage } from "./stores/db"

  import Login from "./Login.svelte"
  import Main from "./main/Main.svelte"

  if ($conn.ready) {
    // Restore if app is loaded in "ready" state
    restoreAssetsDBFromLocalStorage()
    login()
  }
</script>

{#if $conn.reloading}
  <div class="flex h-screen w-screen cursor-wait items-center justify-center text-5xl italic">Logging out...</div>
{:else if !$conn.ready}
  <Login />
{:else}
  <Main />
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

  :global(svg) {
    @apply h-16 w-16;
  }

  :root {
    --btn-text-case: normal;
  }

  :global(.tomato-pulse) {
    animation: tomato-pulse 1.5s infinite;
    --pulse-color: var(--su);
    --pulse-size: 15px;
  }

  @keyframes tomato-pulse {
    0% {
      box-shadow: 0 0 0 0 hsl(var(--pulse-color) / 0.85);
    }

    85% {
      box-shadow: 0 0 0 var(--pulse-size) hsl(var(--pulse-color) / 0);
    }

    100% {
      box-shadow: 0 0 0 0 hsl(var(--pulse-color) / 0);
    }
  }

  :global(.tomato-flash-bg) {
    animation: tomato-flash-bg 2s linear infinite;
    --flash-bg-color: var(--er);
  }

  @keyframes tomato-flash-bg {
    0% {
      background-color: unset;
    }
    50% {
      background-color: hsl(var(--flash-bg-color));
    }
    100% {
      background-color: unset;
    }
  }
</style>
