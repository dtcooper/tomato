import { ipcRenderer } from "electron"
import ReconnectingWebSocket from "reconnecting-websocket"
import { persisted } from "svelte-local-storage-store"
import { derived, get, writable } from "svelte/store"
import { protocol_version } from "../../../server/constants.json"
import { alert } from "./alerts"
import { acknowledgeLog, log, sendPendingLogs } from "./client-logs"
import { resetUserConfig, setServerConfig } from "./config"
import { clearAssetsDB, clearAssetState, syncAssetsDB } from "./db"

const connPersisted = persisted("conn", {
  username: "",
  password: "",
  host: "",
  authenticated: false, // Got at least one successful auth since login. Stays true on disconnect
  didFirstSync: false // Completed one whole sync
})
const connEphemeral = writable({
  connecting: false, // Before successful auth
  connected: false // Whether socket is "online" state or not (after successful auth)
})
const reloading = writable(false) // Whether the whole app is in the reloading process
let loggingOut = false
export const protocolVersion = protocol_version

export const conn = derived(
  [connPersisted, connEphemeral, reloading],
  ([$connPersisted, $connEphemeral, $reloading]) => {
    let prettyHost = "unknown"
    try {
      prettyHost = new URL($connPersisted.host).host
    } catch {
      /* empty */
    }
    return {
      ...$connPersisted,
      ...$connEphemeral,
      ready: $connPersisted.authenticated && $connPersisted.didFirstSync, // App ready to run, whether online or not
      reloading: $reloading,
      prettyHost
    }
  }
)

const updateConn = ({ connecting, connected, ...restPersisted }) => {
  const restEphemeral = {}
  if (connected !== undefined) {
    restEphemeral.connected = connected
  }
  if (connecting !== undefined) {
    restEphemeral.connecting = connecting
  }
  if (Object.keys(restEphemeral).length > 0) {
    connEphemeral.update(($connEphemeral) => ({ ...$connEphemeral, ...restEphemeral }))
  }
  if (Object.keys(restPersisted).length > 0) {
    connPersisted.update(($connPersisted) => ({ ...$connPersisted, ...restPersisted }))
  }
}

let ws = (window._websocket = null)

export const logout = (error = null, hardLogout = false) => {
  if (loggingOut) return
  loggingOut = true

  const wasInReadyState = get(conn).ready // hard refresh if app was in "ready" state

  // Send off pending logs before logout
  console.log(wasInReadyState)
  if (wasInReadyState) {
    log("logout")
    sendPendingLogs(true)
  }
  updateConn({ authenticated: false, connected: false, connecting: false, didFirstSync: false })
  clearAssetsDB()
  clearAssetState()
  setServerConfig({})
  resetUserConfig()

  const ipcChannel = hardLogout ? "clear-user-data-and-restart" : "refresh"

  if (wasInReadyState) {
    reloading.set(true)
    // Give some time for purge of pending logs to take effect
    setTimeout(() => ipcRenderer.invoke(ipcChannel, error), 2500)
  } else {
    ipcRenderer.invoke(ipcChannel, error)
  }
}

// Functions defined for various message types we get from server after authentication
const handleMessages = {
  data: async ({ config, ...data }) => {
    setServerConfig(config)
    await syncAssetsDB(data, !get(conn).didFirstSync)
    updateConn({ didFirstSync: true })
  },
  "ack-log": ({ success, id }) => {
    if (success) {
      console.log(`Acknowledged log ${id}`)
      acknowledgeLog(id)
    }
  },
  logout: () => {
    console.log("Got logout from server. Logging out.")
    logout({ type: "host", message: "An administrator logged you out." })
  },
  notify: ({ msg, level, timeout, connection_id }) => {
    alert(msg, level, timeout)
    messageServer("ack-action", { connection_id, msg: "Successfully notified user!" })
  }
}

export const registerMessageHandler = (name, handler) => {
  if (Object.hasOwn(handleMessages, name)) {
    console.warn(`Message handler ${name} already registered. Safely re-registering.`)
  }
  handleMessages[name] = handler
}

export const messageServer = (type, data) => {
  const { connected } = get(conn)
  if (ws && connected) {
    try {
      ws.send(JSON.stringify({ type, data }, null, ""))
      return true
    } catch (e) {
      console.error(`Error sending ${type} message to websocket`, e)
      return false
    }
  } else {
    console.error(`Tried to send a ${type} message when websocket wasn't created`)
    return false
  }
}

export const login = (username, password, host) => {
  return new Promise((resolve, reject) => {
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

      url.pathname = `${url.pathname}api`
      host = url.toString()
    } else {
      // Called with no args = logging back in on first load
      ;({ username, password, host } = get(conn)) // eslint-disable-line no-extra-semi
    }

    if (!username || !password) {
      updateConn({ connecting: false })
      reject({ type: "userpass", message: "You must specify a username and password." })
      return
    }

    ws = window._websocket = new ReconnectingWebSocket(host)
    ws.onerror = (e) => {
      console.error("Websocket error", e)
      const { ready, authenticated } = get(conn)
      // If we've never been authenticated before
      if (ready) {
        updateConn({ connected: false })
      } else if (authenticated) {
        logout({ type: "host", message: "A connection error occurred with the server. Please try again." })
      } else {
        logout({ type: "host", message: "Failed to shake hands with server. You're sure this address is correct?" })
      }
    }

    ws.onclose = () => {
      const { ready } = get(conn)
      if (ready) {
        // If we are in ready state, just update connection status, this is intermittent downtime
        updateConn({ connected: false })
      } else {
        // If we've not in ready state, reload application (clean login)
        logout({ type: "host", message: "A connection error occurred with the server. Please try again." })
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
          console.log("Got false auth response. Logging out.")
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
      ws.send(JSON.stringify({ username, password, protocol_version, tomato: "radio-automation" }))
      connTimeout = setTimeout(() => ws.close(), 15000)
    }
  })
}
