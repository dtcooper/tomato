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
  connected: false
})
const readonlyAuth = readonly(auth)
export { readonlyAuth as auth }
export const authenticated = derived(auth, ($auth) => $auth.authenticated)
export const connecting = derived(auth, ($auth) => $auth.connecting)
let ws = null

export const logout = () => {
  auth.update(($auth) => {
    return { ...$auth, authenticated: false, connected: false }
  })
  if (ws) {
    ws.close()
  }
}

export const login = (username, password, host) => {
  return new Promise(async (resolve, reject) => {
    let gotAuthResponse = false
    let connTimeout
    let url

    // Didn't pass in any arguments, ie logging back in when app restarted when authenticated = false
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
      ;({ username, password, host } = get(auth))
    }

    ws = new ReconnectingWebSocket(host)
    auth.update(($auth) => {
      return { ...$auth, connecting: true }
    })
    ws.onerror = (e) => {
      console.error("Websocket error", e)
      // If we've never been authenticated before, close connection (otherwise automatica reconnect)
      if (!get(auth).authenticated) {
        reject({ type: "host", message: "Invalid handshake. Are you sure this address is correct?" })
        ws.close()
      }
    }
    ws.onclose = () => {
      auth.update(($auth) => {
        return { ...$auth, connected: false }
      })
      // If we've never been authenticated before, close connection
      if (!get(auth).authenticated) {
        auth.update(($auth) => {
          return { ...$auth, connecting: false }
        })
        if (!sentAuth || !gotAuthResponse) {
          ws.close()
        }
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
          auth.update(($auth) => {
            return { ...$auth, authenticated: false }
          })
          reject({ type: message.field || "host", message: message.error })
          ws.close()
        }
      } else if (get(auth).authenticated) {
        console.log("Authenticated server message:", message)
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

window.addEventListener("offline", () => {
  online.set(false)
})
window.addEventListener("online", () => {
  online.set(true)
})
