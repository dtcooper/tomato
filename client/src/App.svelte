<script context="module">
  import initializeStreamDeck from './streamdeck'

  initializeStreamDeck()
</script>

<script>
  import Login from './Login.svelte'
</script>

<Login/>

<style global lang="postcss">
  @import "./fonts.css";

  @tailwind base;
  @tailwind components;
  @tailwind utilities;

  @layer utilities {
    .btn {
      @apply no-animation;
    }
    .btn-warning:hover, .btn-info:hover, .btn-success:hover, .btn-error:hover {
      filter: brightness(110%);
    }
    .btn:active {
      filter: brightness(97%);
    }
  }
</style>
