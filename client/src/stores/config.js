import { persisted } from "svelte-local-storage-store"
import { readonly } from "svelte/store"

const config = persisted("config", {})
const readonlyConfig = readonly(config)

// May have setting the DB happens first so may have reference bad rotators for split second
export const setServerConfig = (newConfig) => {
  config.set(newConfig)
}

export { readonlyConfig as config }
