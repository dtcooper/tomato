import dayjs from "dayjs"

import { ipcRenderer } from "electron"

import flowerIcon from "@iconify/icons-mdi/flower"
import seedIcon from "@iconify/icons-mdi/seed-outline"
import sproutIcon from "@iconify/icons-mdi/sprout"

import { persisted } from "svelte-local-storage-store"
import { get, readonly, writable } from "svelte/store"

import { darkTheme } from "../utils"

const config = persisted("config", {})
const readonlyConfig = readonly(config)

const defaultUserConfig = {
  uiMode: 0,
  autoplay: false,
  powerSaveBlocker: true,
  enableMIDIButtonBox: true,
  tooltips: true,
  startFullscreen: false,
  showViz: false,
  clock: "12h",
  theme: null
}
export const userConfig = persisted("user-config", defaultUserConfig)
export const resetUserConfig = () => userConfig.set(defaultUserConfig)

const darkMediaQuery = window.matchMedia("(prefers-color-scheme: dark)")
const getDark = () => {
  const { theme } = get(userConfig)
  if (theme) {
    return theme === darkTheme
  } else {
    return darkMediaQuery.matches
  }
}
const isDark = writable(getDark())
darkMediaQuery.addEventListener("change", () => isDark.set(getDark()))
userConfig.subscribe(() => isDark.set(getDark()))
const readonlyIsDark = readonly(isDark)
export { readonlyIsDark as isDark }

export const isFullscreen = writable(true)

export const uiModeInfo = [
  { name: "Simple", icon: seedIcon },
  { name: "Standard", icon: sproutIcon },
  { name: "Advanced", icon: flowerIcon }
]

const resetUIMode = () => {
  userConfig.update(($userConfig) => ({
    ...$userConfig,
    uiMode: Math.min(...get(config).UI_MODES),
    tooltips: true // Renew tooltips
  }))
}

export const setServerConfig = ({ _numeric: numeric, ...newConfig }) => {
  if (numeric) {
    for (const key of numeric) {
      newConfig[key] = +newConfig[key] // Convert to numeric
    }
  }
  console.log("Got new config", newConfig)

  config.set(newConfig)
  if (newConfig.UI_MODES && newConfig.UI_MODES.indexOf(get(userConfig).uiMode) === -1) {
    resetUIMode()
  }
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

if (get(userConfig).startFullscreen) {
  setTimeout(() => setFullscreen(true), 500)
}

export { readonlyConfig as config }
