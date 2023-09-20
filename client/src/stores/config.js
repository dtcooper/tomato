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

const msToNextHour = () => {
  // 15 seconds before the next hour
  const nextHour = dayjs()
    .add("1", "hour")
    .set("minute", 0)
    .set("second", 0)
    .set("millsecond", 0)
    .subtract(15, "seconds")
  const diff = nextHour.diff(dayjs())
  console.log(`Next hour happens in ${Math.round(diff / 60 / 1000)} minutes`)
  return diff
}

const doResetUIModeTimer = () => {
  const resetHours = get(config).UI_MODE_RESET_HOURS || 0
  if (resetHours > 0) {
    const hour = dayjs().get("hour")
    if (hour % resetHours === 0) {
      console.log(`Resetting UI moded! hour=${hour} % resetHours=${resetHours} === 0`)
      resetUIMode()
    } else {
      console.log(`Not resetting UI mode due to hour=${hour} % resetHours=${resetHours} != 0`)
    }
  } else {
    console.log("Not resetting UI mode due to config")
  }
  resetUIMode()
  setTimeout(() => doResetUIModeTimer(), msToNextHour())
}

setTimeout(() => doResetUIModeTimer(), msToNextHour())

export { readonlyConfig as config }
