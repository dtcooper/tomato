import { persisted } from "svelte-local-storage-store"
import { readonly } from "svelte/store"

const config = persisted("config", {})
const readonlyConfig = readonly(config)

export const setServerConfig = ({ _numeric: numeric, ...newConfig }) => {
  if (numeric) {
    for (const key of numeric) {
      newConfig[key] = +newConfig[key] // Convert to numeric
    }
  }
  console.log("Got new config", newConfig)
  config.set(newConfig)
}

export { readonlyConfig as config }
