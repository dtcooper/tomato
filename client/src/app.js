import dayjs from "dayjs"
import duration from "dayjs/plugin/duration"
import isSameOrAfter from "dayjs/plugin/isSameOrAfter"
import isSameOrBefore from "dayjs/plugin/isSameOrBefore"

import { IS_DEV } from "./utils"

dayjs.extend(duration)
dayjs.extend(isSameOrAfter)
dayjs.extend(isSameOrBefore)

if (IS_DEV) {
  const originalSetInterval = setInterval
  const originalClearInterval = clearInterval
  const intervals = new Set()
  window.setInterval = (...args) => {
    const id = originalSetInterval(...args)
    intervals.add(id)
    if (intervals.size > 10) {
      console.warning("More than 10 intervals exist. Something may be very wrong.")
    }
    return id
  }
  window.clearInterval = (id) => {
    originalClearInterval(id)
    intervals.delete(id)
  }
}

import App from "./App.svelte"

export default new App({
  target: document.body
})
