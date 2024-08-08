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
      "min-[1525px]:bottom-0 min-[1525px]:right-0 min-[1525px]:rounded-tl-lg min-[1525px]:flex-col min-[1525px]:rounded-bl-none min-[1525px]:pt-3 min-[1525px]:px-3 min-[1525px]:pb-1"
  } else {
    classes =
      "min-[1145px]:bottom-0 min-[1145px]:right-0 min-[1145px]:rounded-tl-lg min-[1145px]:flex-col min-[1145px]:rounded-bl-none min-[1145px]:pt-3 min-[1145px]:px-3 min-[1145px]:pb-1"
  }
</script>

{#if $userConfig.clock}
  <div class="relative h-0">
    <div
      class="fixed right-0 flex w-max items-end gap-1 rounded-bl-lg bg-base-200 px-2 py-1 font-mono leading-none {classes}"
    >
      <div class="hidden {isWide ? 'min-[1525px]:block' : 'min-[1145px]:block'}">{date}</div>
      <div
        class="text-lg font-bold {is24Hour
          ? isWide
            ? 'min-[1525px]:text-3xl'
            : 'min-[1145px]:text-3xl'
          : isWide
            ? 'min-[1525px]:text-2xl'
            : 'min-[1145px]:text-2xl'}"
      >
        {time}
      </div>
    </div>
  </div>
{/if}
