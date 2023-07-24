import ReconnectingWebSocket from "reconnecting-websocket"
import { persisted } from "svelte-local-storage-store"
import { derived, get } from "svelte/store"
import { protocol_version } from "../../../server/constants.json"

const auth = persisted("auth", { username: "", password: "", host: "", authenticated: false, connecting: false })
export const authenticated = derived(auth, ($auth) => $auth.authenticated)
export const connecting = derived(auth, ($auth) => $auth.connecting)
let ws = null

export const logout = () => {
  if (ws) {
    ws.close()
  }
  auth.update(($auth) => {
    return { ...$auth, authenticated: false }
  })
}

export const login = (username, password, host) => {
  return new Promise(async (resolve, reject) => {
    let sentAuth = false
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
      if (sentAuth) {
        reject({ type: "host", message: "todo" })
      } else {
        reject({ type: "host", message: "Invalid handshake. Are you sure this address is correct?" })
      }
      ws.close()
    }
    ws.onclose = () => {
      auth.update(($auth) => {
        return { ...$auth, connecting: false }
      })
      if (!sentAuth || !gotAuthResponse) {
        ws.close()
      }
    }
    ws.onmessage = (e) => {
      const message = JSON.parse(e.data)
      if (sentAuth && !gotAuthResponse) {
        gotAuthResponse = true
        if (message.success) {
          auth.update(($auth) => {
            return { ...$auth, authenticated: true, connecting: false, username, password, host }
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
      }
    }
    ws.onopen = () => {
      sentAuth = gotAuthResponse = false
      ws.send(JSON.stringify({ username, password, protocol_version }))
      connTimeout = setTimeout(() => {
        ws.close()
        reject({ type: "host", message: "Connection to server timed out. Try again." })
      }, 25000)
      sentAuth = true
    }
  })
}

window.addEventListener("offline", () => {
  online.set(false)
})
window.addEventListener("online", () => {
  online.set(true)
})
