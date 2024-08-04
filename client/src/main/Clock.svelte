<script>
  import dayjs from "dayjs"

  import { userConfig } from "../stores/config"

  export let isWide = false

  let date
  let time
  let classes
  let interval
  let is12Hour = false

  const update = () => {
    const now = dayjs()
    date = now.format("ddd MMM d, YYYY")
    time = now.format(is12Hour ? "h:mm:ssa" : "HH:mm:ss")
  }

  $: {
    clearInterval(interval)
    is12Hour = $userConfig.clock !== "12h"
    update()
    if ($userConfig.clock) {
      interval = setInterval(() => update(), 250)
    }
  }

  $: if (isWide) {
    classes =
      "min-[1500px]:bottom-0 min-[1500px]:right-0 min-[1500px]:rounded-tl-lg min-[1500px]:flex-col min-[1500px]:rounded-bl-none min-[1500px]:p-3"
  } else {
    classes =
      "min-[1125px]:bottom-0 min-[1125px]:right-0 min-[1125px]:rounded-tl-lg min-[1125px]:flex-col min-[1125px]:rounded-bl-none min-[1125px]:p-3"
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
