import dayjs from "dayjs"
import { get } from "svelte/store"
import { v4 as uuid } from "uuid"

import { client_log_entry_types } from "../../../server/constants.json"
import { IS_DEV } from "../utils"
import { conn, messageServer } from "./connection"

let pendingLogs = new Map()
try {
  pendingLogs = new Map(JSON.parse(window.localStorage.getItem("pending-logs")) || [])
} catch (e) {
  console.warn("Error loading pendingLog:", e)
}

const savePendingLogs = () =>
  window.localStorage.setItem("pending-logs", JSON.stringify(Array.from(pendingLogs.entries()), null, ""))

export const log = (window.log = (type = "unspecified", description = "") => {
  if (!client_log_entry_types.includes(type)) {
    console.error(`Invalid log type: ${type} - using unspecified`)
    type = "unspecified"
  }

  pendingLogs.set(uuid(), { created_at: dayjs().toISOString(), type, description })
  savePendingLogs()
})

export const sendPendingLogs = (forceClear = false) => {
  const entries = Array.from(pendingLogs.entries())
  if (entries.length) {
    const { authenticated, connected } = get(conn)
    if (authenticated && connected) {
      for (const [id, data] of entries) {
        messageServer("log", { id, ...data })
        console.log("Sending log:", { id, ...data })
      }
    }
  }
  if (forceClear) {
    pendingLogs = {}
    savePendingLogs()
  }
}

export const acknowledgeLog = (id) => {
  pendingLogs.delete(id)
  savePendingLogs()
}

setInterval(() => sendPendingLogs(), IS_DEV ? 2500 : 30000) // Run every 30 seconds

// Rudimentary handling of uncaught exceptions / promise rejections (debounced)
let errorDebounce
window.addEventListener("error", (event) => {
  clearTimeout(errorDebounce)
  errorDebounce = setTimeout(() => log("internal_error", `Error: ${event.error}`), 2500)
})

window.addEventListener("unhandledrejection", (event) => {
  clearTimeout(errorDebounce)
  errorDebounce = setTimeout(() => log("internal_error", `Unhandled rejection: ${event.error}`), 2500)
})
