import { persisted } from "svelte-local-storage-store"
import { get, readonly } from "svelte/store"

const config = persisted("config", {})
const readonlyConfig = readonly(config)

const defaultUserConfig = { uiMode: 0, theme: "synthwave" }
export const userConfig = persisted("user-config", defaultUserConfig)
export const resetUserConfig = () => userConfig.set(defaultUserConfig)

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

document.documentElement.setAttribute("data-theme", get(userConfig).theme)
userConfig.subscribe(({ theme }) => document.documentElement.setAttribute("data-theme", theme))

export { readonlyConfig as config }
