<script context="module">
  import initializeStreamDeck from "./streamdeck"

  initializeStreamDeck()
</script>

<script>
  import { connected } from "./stores/connection"

  import Login from "./Login.svelte"
  import Main from "./Main.svelte"
</script>

{#if !$connected}
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
</style>
