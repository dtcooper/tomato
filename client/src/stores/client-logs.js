import dayjs from "dayjs"
import { get } from "svelte/store"
import { v4 as uuid } from "uuid"

import { client_log_entry_types } from "../../../server/constants.json"
import { IS_DEV } from "../utils"
import { conn, messageServer } from "./connection"

let pendingLogs = {}
try {
  pendingLogs = JSON.parse(window.localStorage.getItem("pending-logs")) || {}
} catch {}

const savePendingLogs = () => window.localStorage.setItem("pending-logs", JSON.stringify({}, null, ""))

export const log = (window.log = (type = "unspecified", description = "") => {
  if (!client_log_entry_types.includes(type)) {
    console.error(`Invalid log type: ${type} - using unspecified`)
    type = "unspecified"
  }

  pendingLogs[uuid()] = { created_at: dayjs().toISOString(), type, description }
  savePendingLogs()
})

export const sendPendingLogs = (forceClear = false) => {
  const entries = Object.entries(pendingLogs)
  if (entries.length) {
    const { authenticated, connected } = get(conn)
    if (authenticated && connected) {
      for (const [id, data] of entries) {
        messageServer("log", { id, ...data })
        console.log("Sending", { id, ...data })
      }
    }
  }
  if (forceClear) {
    pendingLogs = {}
    savePendingLogs()
  }
}

export const acknowledgeLog = (id) => {
  delete pendingLogs[id]
  savePendingLogs()
}

setInterval(sendPendingLogs, IS_DEV ? 2500 : 30000) // Run every 30 seconds

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
