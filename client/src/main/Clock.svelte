<script>
  import dayjs from "dayjs"

  import { userConfig } from "../stores/config"

  export let isWide = false

  let date
  let time
  let classes
  let interval
  let is24Hour = false

  const update = () => {
    const now = dayjs()
    date = now.format("ddd MMM D, YYYY")
    time = now.format(is24Hour ? "HH:mm:ss" : "h:mm:ssa")
  }

  $: {
    clearInterval(interval)
    is24Hour = $userConfig.clock === "24h"
    update()
    if ($userConfig.clock) {
      interval = setInterval(() => update(), 250)
    }
  }

  $: if (isWide) {
    classes =
      "clk-wd:bottom-0 clk-wd:right-0 clk-wd:rounded-tl-lg clk-wd:flex-col clk-wd:rounded-bl-none clk-wd:pt-3 clk-wd:px-3 clk-wd:pb-1"
  } else {
    classes =
      "clk-sm:bottom-0 clk-sm:right-0 clk-sm:rounded-tl-lg clk-sm:flex-col clk-sm:rounded-bl-none clk-sm:pt-3 clk-sm:px-3 clk-sm:pb-1"
  }
</script>

{#if $userConfig.clock}
  <div class="relative h-0">
    <div
      class="fixed right-0 flex w-max items-end gap-1 rounded-bl-lg bg-base-200 px-2 py-1 font-mono leading-none {classes}"
    >
      <div class="hidden {isWide ? 'clk-wd:block' : 'clk-sm:block'}">{date}</div>
      <div
        class="text-lg font-bold {is24Hour
          ? isWide
            ? 'clk-wd:text-3xl'
            : 'clk-sm:text-3xl'
          : isWide
            ? 'clk-wd:text-2xl'
            : 'clk-sm:text-2xl'}"
      >
        {time}
      </div>
    </div>
  </div>
{/if}
