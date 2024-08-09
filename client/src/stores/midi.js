import { decode as msgpackDecode } from "@msgpack/msgpack"
import { EventEmitter } from "eventemitter3"
import { WebMidi } from "webmidi"

import { alert } from "./alerts"
import { userConfig } from "./config"

const SYSEX_PREFIX = "!T~"
const SYSEX_NON_COMMERCIAL = 0x7d
const MIDI_BTN_CTRL = 0x10
const MIDI_LED_CTRL = 0x11
const BTN_PRESSED = 0x7f

export const LED_OFF = 0
export const LED_ON = 1
export const LED_FLASH = 2
export const LED_PULSATE_SLOW = 3
export const LED_PULSATE_FAST = 4
const ledStrings = ["off", "on", "flash", "pulsate/slow", "pulsate/fast"]

export const midiButtonPresses = new EventEmitter()

let lastLEDValue = LED_OFF
let enabled = false

// Filter midi loopback (through port) on Linux
const portUsable = (port) => !IS_LINUX || !port.name.toLowerCase().includes("midi through port")
const filterPorts = (ports) => ports.filter((p) => portUsable(p))

window.addEventListener("beforeunload", () => {
  midiSetLED(LED_OFF, true)
})

const sysexMsgPack7bitDecode = (msg) => {
  // Decode most significant bit of following 7 bytes first as 0b07654321 0b01111111 0b02222222 ... 0b07777777
  // Then use msgpack to decode binary data
  const unpacked = []
  for (let index = 0; index < msg.length; index += 8) {
    const msbByte = msg[index] // Every 8th byte is the most significant bit for the following 7 bytes as above
    const chunk = msg.slice(index + 1, index + 8)
    for (let chunkIndex = 0; chunkIndex < chunk.length; chunkIndex++) {
      const msb = (msbByte << (7 - chunkIndex)) & 0x80
      unpacked.push(chunk[chunkIndex] | msb) // Reassemble chunk byte
    }
  }
  return msgpackDecode(unpacked)
}

const enableListeners = () => {
  WebMidi.addListener("connected", ({ port }) => {
    if (portUsable(port)) {
      if (port.type === "input") {
        console.log(`Got midi input: ${port.name} (installing press listener)`)
        port.channels[1].addListener("controlchange", ({ controller, rawValue: value }) => {
          if (controller.number === MIDI_BTN_CTRL) {
            midiButtonPresses.emit(value === BTN_PRESSED ? "pressed" : "released")
          }
        })
        port.addListener("reset", () => {
          console.log(`Midi input ${port.name} was reset.`)
        })
        port.addListener("sysex", ({ message: { rawDataBytes: message } }) => {
          const prefix = new TextDecoder().decode(message.slice(0, SYSEX_PREFIX.length))
          if (prefix === SYSEX_PREFIX) {
            const encoded = message.slice(SYSEX_PREFIX.length)
            const [type, obj] = sysexMsgPack7bitDecode(encoded)
            console.log(
              `Received ${type} sysex from ${port.name}${obj === null ? "" : ": " + JSON.stringify(obj, undefined, Object.keys(obj).length === 1 ? undefined : 2)}`
            )
          }
        })
      } else if (port.type === "output") {
        console.log(`Got midi output: ${port.name} (set LED to ${ledStrings[lastLEDValue]})`)
        port.channels[1].sendControlChange(MIDI_LED_CTRL, lastLEDValue)
      }
    }
  })
  WebMidi.addListener("disconnected", ({ port }) => {
    if (port.type === "input") {
      port.removeListener() // Uninstall listeners on disconnect
    }
  })
}

export const midiSetLED = (value, skipSave = false) => {
  if (enabled) {
    console.log(`Set LED to ${ledStrings[value]}`)
    for (const output of filterPorts(WebMidi.outputs)) {
      output.channels[1].sendControlChange(MIDI_LED_CTRL, value)
    }
  }
  // Save state, to re-enable if device is plugged in
  if (!skipSave) {
    lastLEDValue = value
  }
}

userConfig.subscribe(({ enableMIDIButtonBox }) => {
  if (enableMIDIButtonBox && !enabled) {
    enableListeners()
    WebMidi.enable({
      sysex: true,
      callback: (error) => {
        if (error) {
          enabled = false
          console.error("Error enabling WebMidi!", error)
          alert("Error enabling MIDI subsystem for button box", "error")
          userConfig.update(($config) => ({ ...$config, enableMIDIButtonBox: false }))
        } else {
          console.log("WebMidi enabled")
          enabled = true
        }
      }
    })
  } else if (!enableMIDIButtonBox && enabled) {
    midiSetLED(LED_OFF, true)
    WebMidi.disable()
    enabled = false
    console.log("WebMidi disabled")
  }
})

window.WebMidi = WebMidi
window.sendButtonBoxSysex = (cmd = "stats") => {
  if (enabled) {
    const data = Array.from(SYSEX_PREFIX + cmd).map((letter) => letter.charCodeAt(0))
    for (const output of filterPorts(WebMidi.outputs)) {
      output.sendSysex(SYSEX_NON_COMMERCIAL, data)
    }
  }
}
