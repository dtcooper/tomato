<script>
  import tomatoIcon from './../assets/icons/tomato.svg'
</script>

<div class="hero min-h-screen">
  <div class="hero-content p-0 flex-col w-full">
    <div class="flex w-full">
      <div class="grow flex items-center justify-center tomato-svg">{@html tomatoIcon}</div>
      <div class="flex flex-col items-center">
        <h1 class="text-3xl font-bold font-mono">
          <span>Tomato</span>
        </h1>
        <h2 class="text-2xl py-1 font-bold font-mono italic pt-1">
          Radio Automation
        </h2>
      </div>
      <div class="grow flex items-center justify-center tomato-svg">{@html tomatoIcon}</div>
    </div>
  </div>
</div>

<style lang="postcss">
  .tomato-svg > :global(svg) {
    @apply w-20 h-20;
  }
</style>
