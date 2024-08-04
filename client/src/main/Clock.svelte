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
      "min-[1500px]:bottom-0 min-[1500px]:right-0 min-[1500px]:rounded-tl-lg min-[1500px]:flex-col min-[1500px]:rounded-bl-none min-[1500px]:pt-3 min-[1500px]:px-3 min-[1500px]:pb-1"
  } else {
    classes =
      "min-[1125px]:bottom-0 min-[1125px]:right-0 min-[1125px]:rounded-tl-lg min-[1125px]:flex-col min-[1125px]:rounded-bl-none min-[1125px]:pt-3 min-[1125px]:px-3 min-[1125px]:pb-1"
  }
</script>

{#if $userConfig.clock}
  <div class="relative h-0">
    <div
      class="fixed right-0 flex w-max items-end gap-1 rounded-bl-lg bg-base-200 p-2 font-mono leading-none {classes}"
    >
      <div class="hidden {isWide ? 'min-[1500px]:block' : 'min-[1125px]:block'}">{date}</div>
      <div class="text-lg font-bold {isWide ? 'min-[1500px]:text-2xl' : 'min-[1125px]:text-2xl'}">{time}</div>
    </div>
  </div>
{/if}
