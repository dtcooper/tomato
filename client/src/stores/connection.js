import { writable as persistentWritable } from "svelte-local-storage-store"
import { get, writable } from "svelte/store"

export const accessToken = persistentWritable("accessToken", "")
export const address = persistentWritable("address", "")
export const connected = persistentWritable("connected", false)
export const username = persistentWritable("username", "")
export const online = writable(navigator.onLine)
window.addEventListener("offline", () => {
  online.set(false)
})
window.addEventListener("online", () => {
  online.set(true)
})

const ping = async () => {
  let data, response
  const headers = {}

  if (accessToken) {
    headers["X-Access-Token"] = get(accessToken)
  }

  try {
    response = await fetch(`${get(address)}ping/`, { headers })
    data = await response.json()
  } catch (error) {
    console.error(error)
    return { success: false, error: "Invalid handshake. Are you sure this address is correct?" }
  }

  return data
}

const authenticate = async (password) => {
  let response, data

  try {
    response = await fetch(`${get(address)}auth/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: get(username), password })
    })
    data = await response.json()
  } catch (error) {
    console.error(error)
    return { success: false, error: "Server error while logging in" }
  }

  return data
}

export const login = async (password) => {
  let addressUrl

  const error = (error, errorType = "address") => {
    return { success: false, error, errorType }
  }

  try {
    addressUrl = new URL(get(address))
  } catch {
    try {
      addressUrl = new URL(`https://${get(address)}`)
    } catch {
      return error("Invalid server address")
    }
  }

  if (!["https:", "http:"].includes(addressUrl.protocol)) {
    return error("Server must being with http:// or https://")
  }

  if (!addressUrl.pathname.endsWith("/")) {
    addressUrl.pathname += "/"
  }
  address.set(addressUrl.toString())

  const pong = await ping()
  if (!pong.success) {
    return error(pong.error)
  }

  const auth = await authenticate(password)
  if (!auth.success) {
    return error(auth.error, "auth")
  }

  accessToken.set(auth.access_token)
  return { success: true }
}

export const logout = () => {
  connected.set(false)
  accessToken.set("")
  window.location.reload()
}
