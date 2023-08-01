import ReconnectingWebSocket from "reconnecting-websocket"
import { persisted } from "svelte-local-storage-store"
import { derived, get, writable } from "svelte/store"
import { protocol_version } from "../../../server/constants.json"
import { syncData } from "./assets.js"
import { setServerConfig } from "./config.js"

// TODO this is a mess, connecting + connected SHOULD NOT be persisted, they are ephemeral
const conn = persisted("conn", {
  username: "",
  password: "",
  host: "",
  authenticated: false,  // Got at least one successful auth since login. Stays true on disconnect
  didFirstSync: false  // Completed one whole sync
})
const connecting = writable(false)  // Before successful auth
const connected = writable(false)  // Whether socket is "online" state or not (after successful auth)

const connCombined = derived(
  [conn, connected, connecting],
  ([$conn, $connected, $connecting]) => ({
    ...$conn,
    connecting: $connecting,
    connected: $connected,
    ready: $conn.authenticated && $conn.didFirstSync // App ready to run, whether online or not
  })
)

const updateConn = ({connected: $connected, connecting: $connecting, ...$connUpdates}) => {
  if ($connected !== undefined) {
    connected.set($connected)
  }
  if ($connecting !== undefined) {
    connecting.set($connecting)
  }
  if (Object.keys($connUpdates).length > 0) {
    conn.update($conn => ({ ...$conn, ...$connUpdates}))
  }
}

export { connCombined as conn }

let ws = null

export const logout = () => {
  const hardRefresh = get(connCombined).ready  // hard refresh if app was in "ready" state
  updateConn({authenticated: false, connected: false, connecting: false, didFirstSync: false })
  setServerConfig({})

  if (ws) {
    ws.close()
  }

  if (hardRefresh) {
    window.location.reload()
  }
}

const handleMessages = {
  data: async (data) => {
    const { config, ...jsonData } = data
    setServerConfig(config)
    await syncData(jsonData)
    console.log(get(conn))
    updateConn({didFirstSync: true})
    console.log(get(conn))
  }
}

export const login = (username, password, host) => {
  if (get(conn).connecting) {
    console.error("Called login twice.")
    return
  }

  updateConn({connecting: true})
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
        updateConn({connecting: false})
        reject({ type: "host", message: "Invalid server address. Please try another." })
        return
      }

      url.pathname = `${url.pathname}api/`
      host = url.toString()
    } else {
      // Called with no args = logging back in on first load
      ;({ username, password, host } = get(conn))
    }

    ws = new ReconnectingWebSocket(host, undefined, {
      maxEnqueuedMessages: 0,
      reconnectionDelayGrowFactor: 1
    })

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
        updateConn({connected: false})
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
          updateConn({authenticated: true, connecting: false, connected: true, username, password, host })
          clearTimeout(connTimeout)
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
      updateConn({connected: false, connecting: true })
      ws.send(JSON.stringify({ username, password, protocol_version }))
      connTimeout = setTimeout(() => {
        ws.close()
        reject({ type: "host", message: "Connection to server timed out. Try again." })
      }, 25000)
    }
  })
}
