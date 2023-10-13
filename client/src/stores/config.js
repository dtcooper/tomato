import dayjs from "dayjs"

import { ipcRenderer } from "electron"

import { persisted } from "svelte-local-storage-store"
import { get, readonly, writable } from "svelte/store"

const config = persisted("config", {})
const readonlyConfig = readonly(config)

const defaultUserConfig = { uiMode: 0, autoplay: false, powerSaveBlocker: true }
export const userConfig = persisted("user-config", defaultUserConfig)
export const resetUserConfig = () => userConfig.set(defaultUserConfig)
export const isFullscreen = writable(true)

const resetUIMode = () => {
  userConfig.update(($userConfig) => {
    return { ...$userConfig, uiMode: Math.min(...get(config).UI_MODES) }
  })
}

export const setServerConfig = ({ _numeric: numeric, ...newConfig }) => {
  if (numeric) {
    for (const key of numeric) {
      newConfig[key] = +newConfig[key] // Convert to numeric
    }
  }
  console.log("Got new config", newConfig)

  if (newConfig.UI_MODES && newConfig.UI_MODES.indexOf(get(userConfig).uiMode) === -1) {
    resetUIMode()
  }

  config.set(newConfig)
}

userConfig.subscribe(({ powerSaveBlocker }) => {
  ipcRenderer.invoke("power-save-blocker", powerSaveBlocker)
})

ipcRenderer.invoke("is-fullscreen").then((response) => {
  isFullscreen.set(response)
})

ipcRenderer.on("set-fullscreen", (event, value) => {
  isFullscreen.set(value)
})

export const setFullscreen = (value) => {
  ipcRenderer.invoke("set-fullscreen", value)
}

const resetUIModeTimer = () => {
  const now = dayjs()

  const currentHour = now.get("hour")
  const currentMinute = now.get("minute")
  for (const [hour, minute] of get(config).UI_MODE_RESET_TIMES || []) {
    if (currentHour === hour && currentMinute === minute) {
      console.log(`Resetting UI mode due to config (${hour}:${minute}) at ${dayjs().format()}`)
      resetUIMode()
    }
  }

  // Run every minute
  const nextMinute = now.add(1, "minute").set("second", 0).set("millisecond", 0)
  const whenToRunNext = nextMinute.diff(now)
  setTimeout(() => resetUIModeTimer(), whenToRunNext)
}
resetUIModeTimer()

export { readonlyConfig as config }
