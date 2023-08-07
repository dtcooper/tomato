import ReconnectingWebSocket from "reconnecting-websocket"
import { ipcRenderer } from "electron"
import { persisted } from "svelte-local-storage-store"
import { derived, get, writable } from "svelte/store"
import { protocol_version } from "../../../server/constants.json"
import { clearAssetsDB, clearSoftIgnoredAssets, syncAssetsDB } from "./db"
import { acknowledgeLog, log, sendPendingLogs } from "./client-logs"
import { setServerConfig } from "./config"

// TODO this is a mess, connecting + connected SHOULD NOT be persisted, they are ephemeral
const connPersisted = persisted("conn", {
  username: "",
  password: "",
  host: "",
  authenticated: false, // Got at least one successful auth since login. Stays true on disconnect
  didFirstSync: false // Completed one whole sync
})
const connecting = writable(false) // Before successful auth
const connected = writable(false) // Whether socket is "online" state or not (after successful auth)
const reloading = writable(false) // Whether the whole app is in the reloading process

export const conn = derived(
  [connPersisted, connected, connecting, reloading],
  ([$connPersisted, $connected, $connecting, $reloading]) => ({
    ...$connPersisted,
    connecting: $connecting,
    connected: $connected,
    ready: $connPersisted.authenticated && $connPersisted.didFirstSync, // App ready to run, whether online or not
    reloading: $reloading
  })
)

const updateConn = ({ connected: $connected, connecting: $connecting, ...$conn }) => {
  if ($connected !== undefined) {
    connected.set($connected)
  }
  if ($connecting !== undefined) {
    connecting.set($connecting)
  }
  if (Object.keys($conn).length > 0) {
    connPersisted.update(($connPersisted) => ({ ...$connPersisted, ...$conn }))
  }
}

let ws = window.ws = null

export const logout = (error) => {
  const wasInReadyState = get(conn).ready // hard refresh if app was in "ready" state

  // Send off pending logs before logout
  log("logout")
  sendPendingLogs(true)
  updateConn({ authenticated: false, connected: false, connecting: false, didFirstSync: false })
  clearAssetsDB()
  clearSoftIgnoredAssets()  // Do I want this cleared?
  setServerConfig({})

  if (wasInReadyState) {
    reloading.set(true)
    // Give some time for purge of pending logs to take effect
    setTimeout(() => ipcRenderer.invoke("refresh", error), 1500)
  } else {
    ipcRenderer.invoke("refresh", error)
  }
}

// Functions defined for various message types we get from server after authentication
const handleMessages = {
  data: async (data) => {
    const { config, ...jsonData } = data
    setServerConfig(config)
    await syncAssetsDB(jsonData)
    updateConn({ didFirstSync: true })
  },
  log: (data) => {
    const { success, id } = data
    if (success) {
      console.log(`Acknowledged log ${id}`)
      acknowledgeLog(id)
    }
  }
}

export const messageServer = (type, data) => {
  if (ws) {
    try {
      ws.send(JSON.stringify({ type, data }, null, ""))
      return true
    } catch (e) {
      console.error(`Error sending ${type} message to websocket`)
      return false
    }
  } else {
    console.error("Tried to send a message when websocket wasn't created")
    return false
  }
}

export const login = (username, password, host) => {
  return new Promise(async (resolve, reject) => {
    let gotAuthResponse = false
    let connTimeout
    let url

    if (ws && ws.readyState !== ReconnectingWebSocket.CLOSED) {
      console.error(
        `Rejecting call to login(). Called with websocket in readyState = ${ws.readyState}, expected closed (${ReconnectingWebSocket.CLOSED}`
      )
      reject({ type: "host", message: "A connection was in progress." })
    }

    updateConn({ connecting: true })
    if (username !== undefined) {
      // Convert http[s]:// to ws[s]://
      if (["http", "https"].some((proto) => host.toLowerCase().startsWith(`${proto}://`))) {
        host = host.replace(/^http/i, "ws")
        // If not prefixed with ws[s]://, prefix it
      } else if (["ws", "wss"].every((proto) => !host.toLowerCase().startsWith(`${proto}://`))) {
        host = `wss://${host}`
      }

      try {
        url = new URL(host)
      } catch {
        updateConn({ connecting: false })
        reject({ type: "host", message: "Invalid server address. Please try another." })
        return
      }

      url.pathname = `${url.pathname}api/`
      host = url.toString()
    } else {
      // Called with no args = logging back in on first load
      ;({ username, password, host } = get(conn))
    }

    if (!username || !password) {
      updateConn({ connecting: false })
      reject({ type: "userpass", message: "You must specify a username and password."})
      return
    }

    ws = window.ws = new ReconnectingWebSocket(host)
    ws.onerror = (e) => {
      console.error("Websocket error", e)
      const { ready, authenticated } = get(conn)
      // If we've never been authenticated before
      if (ready) {
        updateConn({ connected: false })
      } else if (authenticated) {
        logout({ type: "host", message: "A connect error occurred with the server. Please try again."})
      } else {
        logout({ type: "host", message: "Failed to shake hands with server. You're sure this address is correct?" })
      }
    }

    ws.onclose = () => {
      const { ready } = get(conn)
      if (ready) {
        // If we are in ready state, just update connection status, this is intermittent downtime
        updateConn({ connected: false })
      } else  {
        // If we've not in ready state, reload application (clean login)
        logout({ type: "host", message: "A connect error occurred with the server. Please try again."})
      }
    }

    ws.onmessage = async (e) => {
      const message = JSON.parse(e.data)
      if (!gotAuthResponse) {
        gotAuthResponse = true
        if (message.success) {
          updateConn({ authenticated: true, connecting: false, connected: true, username, password, host })
          clearTimeout(connTimeout)
          log("login")
          console.log("Succesfully authenticated!")
          resolve()
        } else {
          logout({ type: message.field || "host", message: message.error })
        }
      } else if (get(conn).authenticated) {
        const func = handleMessages[message.type]
        if (func) {
          await func(message.data)
        } else {
          console.log(`Unrecognized message type: ${message.type}`)
        }
      }
    }
    ws.onopen = () => {
      gotAuthResponse = false
      updateConn({ connected: false, connecting: true })
      ws.send(JSON.stringify({ username, password, protocol_version }))
      connTimeout = setTimeout(() => ws.close(), 15000)
    }
  })
}
