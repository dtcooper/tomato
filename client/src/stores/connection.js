import ReconnectingWebSocket from "reconnecting-websocket"
import { persisted } from "svelte-local-storage-store"
import { derived, get, writable } from "svelte/store"
import { protocol_version } from "../../../server/constants.json"
import { syncData } from "./assets"
import { acknowledgeLog, log, sendPendingLogs } from "./client-logs"
import { setServerConfig } from "./config"

// TODO this is a mess, connecting + connected SHOULD NOT be persisted, they are ephemeral
const conn = persisted("conn", {
  username: "",
  password: "",
  host: "",
  authenticated: false, // Got at least one successful auth since login. Stays true on disconnect
  didFirstSync: false // Completed one whole sync
})
const connecting = writable(false) // Before successful auth
const connected = writable(false) // Whether socket is "online" state or not (after successful auth)
const reloading = writable(false) // Whether the whole app is in the reloading process

const connCombined = derived(
  [conn, connected, connecting, reloading],
  ([$conn, $connected, $connecting, $reloading]) => ({
    ...$conn,
    connecting: $connecting,
    connected: $connected,
    ready: $conn.authenticated && $conn.didFirstSync, // App ready to run, whether online or not
    reloading: $reloading
  })
)

const updateConn = ({ connected: $connected, connecting: $connecting, ...$connUpdates }) => {
  if ($connected !== undefined) {
    connected.set($connected)
  }
  if ($connecting !== undefined) {
    connecting.set($connecting)
  }
  if (Object.keys($connUpdates).length > 0) {
    conn.update(($conn) => ({ ...$conn, ...$connUpdates }))
  }
}

export { connCombined as conn }

let ws = null

export const logout = () => {
  const wasInReadyState = get(connCombined).ready // hard refresh if app was in "ready" state

  // Send off pending logs before logout
  log("logout")
  sendPendingLogs(true)

  updateConn({ authenticated: false, connected: false, connecting: false, didFirstSync: false })
  setServerConfig({})

  if (wasInReadyState) {
    reloading.set(true)
    console.log("Was in ready state. Doing hard refresh in 1.5 seconds to attempt to wait for logs to purge.")
    setTimeout(() => window.location.reload(), 1500)
  } else {
    ws.close()
  }
}

// Functions defined for various message types we get from server after authentication
const handleMessages = {
  data: async (data) => {
    const { config, ...jsonData } = data
    setServerConfig(config)
    await syncData(jsonData)
    console.log(get(conn))
    updateConn({ didFirstSync: true })
    console.log(get(conn))
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
  console.log("readyState:", ws && ws.readyState)
  if (ws && ws.readyState !== ReconnectingWebSocket.CLOSED) {
    console.error(
      `Rejecting call to login(). Called with websocket in readyState = ${ws.readyState}, expected closed (${ReconnectingWebSocket.CLOSED}`
    )
    return
  }

  updateConn({ connecting: true })
  return new Promise(async (resolve, reject) => {
    let gotAuthResponse = false
    let connTimeout
    let url

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

    ws = new ReconnectingWebSocket(host)
    ws.onerror = (e) => {
      console.error("Websocket error", e)
      // If we've never been authenticated before
      if (!get(conn).authenticated) {
        reject({ type: "host", message: "Failed to shake hands with server. Are this address is correct?" })
        logout()
      }
    }

    ws.onclose = () => {
      if (get(conn).authenticated) {
        // If we have authenticated, just update connection status
        updateConn({ connected: false })
      } else {
        // If we've never been authenticated before, completely close connection
        logout()
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
          logout()
          reject({ type: message.field || "host", message: message.error })
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
      connTimeout = setTimeout(() => {
        ws.close()
        reject({ type: "host", message: "Connection to server timed out. Try again." })
      }, 25000)
    }
  })
}
