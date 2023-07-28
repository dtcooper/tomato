import ReconnectingWebSocket from "reconnecting-websocket"
import { persisted } from "svelte-local-storage-store"
import { derived, get, readonly } from "svelte/store"
import { protocol_version } from "../../../server/constants.json"

const auth = persisted("auth", {
  username: "",
  password: "",
  host: "",
  authenticated: false,
  connecting: false,
  connected: false,
  didFirstSync: false
})
const readonlyAuth = readonly(auth)

export { readonlyAuth as auth }
export const authenticated = derived(auth, ($auth) => $auth.authenticated)
export const connecting = derived(auth, ($auth) => $auth.connecting)
export const connected = derived(auth, ($auth) => $auth.connected)
export const ready = derived(auth, ($auth) => $auth.authenticated && $auth.didFirstSync)

let ws = null

export const logout = () => {
  auth.update(($auth) => {
    return { ...$auth, authenticated: false, connected: false, connecting: false, didFirstSync: false }
  })
  if (ws) {
    ws.close()
  }
}

const handleMessages = {
  data: (data) => {
    console.log("Got data message:", data)
  }
}

export const login = (username, password, host) => {
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
        reject({ type: "host", message: "Invalid server address. Please try another." })
        return
      }

      url.pathname = `${url.pathname}api/`
      host = url.toString()
    } else {
      // Called with no args = logging back in on first load
      ;({ username, password, host } = get(auth))
    }

    ws = new ReconnectingWebSocket(host, undefined, {
      maxEnqueuedMessages: 0,
      reconnectionDelayGrowFactor: 1
    })
    auth.update(($auth) => {
      return { ...$auth, connecting: true }
    })
    ws.onerror = (e) => {
      console.error("Websocket error", e)
      // If we've never been authenticated before
      if (!get(auth).authenticated) {
        reject({ type: "host", message: "Failed to shake hands with server. Are this address is correct?" })
        logout()
      }
    }
    ws.onclose = () => {
      if (get(auth).authenticated) {
        // If we have authenticated, just update connection status
        auth.update(($auth) => {
          return { ...$auth, connected: false }
        })
      } else {
        // If we've never been authenticated before, completely close connection
        logout()
      }
    }

    ws.onmessage = (e) => {
      const message = JSON.parse(e.data)
      if (!gotAuthResponse) {
        gotAuthResponse = true
        if (message.success) {
          auth.update(($auth) => {
            return { ...$auth, authenticated: true, connecting: false, connected: true, username, password, host }
          })
          clearTimeout(connTimeout)
          console.log("Succesfully authenticated!")
          resolve()
        } else {
          logout()
          reject({ type: message.field || "host", message: message.error })
        }
      } else if (get(auth).authenticated) {
        const func = handleMessages[message.type]
        if (func) {
          func(message.data)
        } else {
          console.log(`Unrecognized message type: ${message.type}`)
        }
      }
    }
    ws.onopen = () => {
      gotAuthResponse = false

      auth.update(($auth) => {
        return { ...$auth, connected: false, connecting: true }
      })

      ws.send(JSON.stringify({ username, password, protocol_version }))

      connTimeout = setTimeout(() => {
        ws.close()
        reject({ type: "host", message: "Connection to server timed out. Try again." })
      }, 25000)
    }
  })
}
