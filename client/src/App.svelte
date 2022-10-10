<script>
  import './streamdeck'
</script>

<main class="font-mono italic text-center text-5xl mt-4 space-y-10">
  <h1>Hello World</h1>
  <span class="btn btn-lg btn-warning">Press me!</span>
</main>

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
