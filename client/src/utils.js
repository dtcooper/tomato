import dayjs from "dayjs"

export const urlParams = Object.fromEntries(new URLSearchParams(window.location.search).entries())
export const IS_DEV = urlParams.dev === "1"
export const progressBarAnimationFramerate = 30

export const prettyDuration = (item, max) => {
  item = dayjs.duration(Math.round(item), "seconds")
  max = max ? dayjs.duration(Math.round(max), "seconds") : item
  if (max.hours() > 0) {
    return `${item.hours()}:${item.format("mm:ss")}`
  } else if (max.minutes() >= 10) {
    return item.format("mm:ss")
  } else {
    return item.format("m:ss")
  }
}

export const humanDuration = (item) => {
  const seconds = Math.floor(item) % 60
  const minutes = Math.floor(item / 60) % 60
  const hours = Math.floor(item / 3600)

  const items = []
  if (hours) items.push(`${hours} hour${hours === 1 ? "" : "s"}`)
  if (minutes) items.push(`${minutes} minute${minutes === 1 ? "" : "s"}`)
  if (seconds) items.push(`${seconds} second${seconds === 1 ? "" : "s"}`)
  return items.join(", ")
}

export const prettyDatetime = (datetime) => datetime.format("MMM D, YYYY @ h:mm:ssa")

export const upperCaseFirst = (s) => `${s.charAt(0).toUpperCase()}${s.substr(1)}`

export const tomatoIcon = {
  body: '<path d="m10 0h2m-3 1h2m-3 1h2m-3 1h4m-1 1h2" stroke="#046736"/><path d="m5 1h2m-2 1h3m2 0h1m-5 1h1m0 1h2m-2 1h3m-1 1h1" stroke="#40904c"/><path d="m3 2h2m6 0h1m-10 1h2m7 0h2m-12 1h4m4 0h1m2 0h1m-12 1h3m2 0h1m3 0h4m-14 1h5m1 0h3m1 0h4m-14 1h14m-14 1h14m-14 1h13m-13 1h13m-12 1h12m-12 1h12m-11 1h10m-9 1h8m-7 1h1" stroke="#db0201"/><path d="m12 2h1m0 1h1m-1 1h2m-1 1h1m-1 1h2m-2 1h2m-2 1h2m-3 1h3m-3 1h3m-3 1h2m-2 1h2m-3 1h2m-3 1h2m-8 1h7" stroke="#a00"/><path d="m4 3h2m-1 1h2m-3 1h2m-1 1h1" stroke="#9dc14b"/>'
}

// Tweak setInterval for tracking / debugging
if (IS_DEV) {
  const originalSetInterval = setInterval
  const originalClearInterval = clearInterval
  const intervals = (window._activeIntervals = new Set())
  window.setInterval = (...args) => {
    const id = originalSetInterval(...args)
    intervals.add(id)
    if (intervals.size > 5) {
      console.warning("More than 5 active intervals exist. Something may be very wrong.")
    }
    return id
  }
  window.clearInterval = (id) => {
    originalClearInterval(id)
    intervals.delete(id)
  }
}
