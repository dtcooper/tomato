import { ipcRenderer } from "electron"

import { persisted } from "svelte-local-storage-store"
import { get, readonly, writable } from "svelte/store"

const config = persisted("config", {})
const readonlyConfig = readonly(config)

const defaultUserConfig = { uiMode: 0, autoplay: false, powerSaveBlocker: true }
export const userConfig = persisted("user-config", defaultUserConfig)
export const resetUserConfig = () => userConfig.set(defaultUserConfig)
export const isFullscreen = writable(true)

export const setServerConfig = ({ _numeric: numeric, ...newConfig }) => {
  if (numeric) {
    for (const key of numeric) {
      newConfig[key] = +newConfig[key] // Convert to numeric
    }
  }
  console.log("Got new config", newConfig)

  if (newConfig.UI_MODES && newConfig.UI_MODES.indexOf(get(userConfig).uiMode) === -1) {
    console.log(get(userConfig).uiMode)
    userConfig.update(($userConfig) => {
      return { ...$userConfig, uiMode: Math.min(newConfig.UI_MODES) }
    })
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

export { readonlyConfig as config }
