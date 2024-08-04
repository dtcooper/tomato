import { EventEmitter } from "eventemitter3"
import { WebMidi } from "webmidi"

import { alert } from "./alerts"
import { userConfig } from "./config"

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

window.addEventListener("beforeunload", () => {
  midiSetLED(LED_OFF, true)
})

const enableListeners = () => {
  WebMidi.addListener("connected", ({ port }) => {
    if (port.type === "input") {
      console.log(`Got midi input: ${port.name} (installing press listener)`)
      port.channels[1].addListener("controlchange", (event) => {
        if (event.controller.number === MIDI_BTN_CTRL) {
          midiButtonPresses.emit(event.rawValue === BTN_PRESSED ? "pressed" : "released")
        }
      })
    } else if (port.type === "output") {
      console.log(`Got midi output: ${port.name} (set LED to ${ledStrings[lastLEDValue]})`)
      port.channels[1].sendControlChange(MIDI_LED_CTRL, lastLEDValue)
    }
  })
}

export const midiSetLED = (value, skipSave = false) => {
  if (enabled) {
    console.log(`Set LED to ${ledStrings[value]}`)
    for (const output of WebMidi.outputs) {
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
