dayjs.extend(dayjs_plugin_duration)

const DATA = JSON.parse(document.getElementById("tomato-configure-live-clients-data").textContent)
const db = DATA.serialized_data

const prettyDuration = (item, max) => {
  item = dayjs.duration(Math.round(item), "seconds")
  max = max ? dayjs.duration(Math.round(max), "seconds") : item
  if (max.hours() > 0) {
    return `${item.hours()}:${item.format("mm:ss")}`
  } else if (max.minutes() >= 10) {
    return item.format("mm:ss")
  } else {
    return item.format("m:ss")
  }
}

document.addEventListener("alpine:init", () => {
  let ws = null

  Alpine.data("tomato", () => ({
    connected: false,
    error: null,
    connections: [],
    logs: [],
    notifyMsg: "",
    notifyLevel: "info",
    subscribed: null,
    asset: null,
    rotator: null,
    items: [],

    send(msgType, data) {
      if (ws) {
        console.log("Sending:", { type: msgType, data })
        ws.send(JSON.stringify({ type: msgType, data }))
      }
    },

    assetNameShort() {
      if (this.asset) {
        return this.asset.name.length > 20 ? this.asset.name.substring(0, 19) + "\u2026" : this.asset.name
      } else {
        return "Select from above"
      }
    },

    swapAsset(action, generated_id, subindex) {
      if (this.asset && this.subscribed) {
        this.send("swap", {
          action,
          asset_id: this.asset.id,
          rotator_id: this.rotator.id,
          connection_id: this.subscribed,
          generated_id,
          subindex
        })
      }
    },

    deleteAsset(generated_id, subindex) {
      console.log(generated_id, subindex)
      if (this.subscribed) {
        this.send("swap", {
          action: "delete",
          connection_id: this.subscribed,
          generated_id,
          subindex
        })
      }
    },

    log(message, connection_id = null) {
      let s = `[${dayjs().format("MMM D YYYY HH:mm:ss.SSS")}]`
      if (connection_id) {
        s += ` [user=${this.getConn(connection_id)?.username || "unknown"}]`
      } else {
        s += " [global]"
      }
      this.logs.unshift(`${s} ${message}`)
    },

    getConn(connection_id) {
      return connection_id && this.connections.find((c) => c.connection_id === connection_id)
    },

    init() {
      this.log("Attempting to connect to server websocket.")
      ws = new ReconnectingWebSocket(
        DATA.debug && !DATA.is_secure
          ? "ws://localhost:8001/api"
          : `${document.location.protocol.replace("http", "ws")}//${document.location.host}/api`
      )
      ws.onopen = () => {
        ws.send(
          JSON.stringify({
            method: "session",
            tomato: "radio-automation",
            protocol_version: DATA.protocol_version,
            admin_mode: true
          })
        )
      }

      ws.onmessage = (e) => {
        const msg = JSON.parse(e.data)
        if (this.connected) {
          const { type, data } = msg
          if (type === "user-connections") {
            this.connections = data
            // User no longer connected
            if (this.subscribed && !this.getConn(this.subscribed)) {
              this.log("User no longer connected! Unsubscribing.")
              this.subscribed = null
              this.items = []
            }
          } else if (type === "ack-action") {
            this.log(data.msg, data.connection_id)
          } else if (type === "client-data") {
            if (this.subscribed === null) {
              this.log("Successfully subscribed to client!", data.connection_id)
            }
            this.subscribed = data.connection_id
            this.items = data.items
          } else if (type === "unsubscribe") {
            if (this.subscribed === data.connection_id) {
              this.log("Got unsubscribe from user. Disconnecting.")
              this.subscribed = null
              this.items = []
            } else {
              console.warn(`Got unsubscribe from ${data.connection_id}, but we weren't subscribed`)
            }
          } else {
            console.log(`Unrecognized ${type} msg`, data)
          }
        } else if (msg.success) {
          this.log("Successfully connected!")
          this.connected = true
        } else {
          this.log(`An error occurred: ${msg.error}`)
        }
      }

      ws.onclose = () => {
        if (this.connected) {
          this.log("Disconnected!")
          this.connected = false
          this.subscribed = null
          this.items = []
        }
      }
      ws.onerror = () => {
        this.log(`An error with the websocket occurred!`)
      }
    }
  }))
})
