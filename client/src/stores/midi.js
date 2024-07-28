import { noop } from "svelte/internal"
import { get } from "svelte/store"
import { userConfig } from "./config"

let midi
let outputs = []
let buttonPressCallback = noop

let lastLEDValue = 0

const updateMidiDevices = (enabled = null) => {
  if (enabled === null) {
    enabled = get(userConfig).enableMIDIButtonBox
  }

  if (!enabled) {
    setLED(0, true)
  }

  outputs = []

  for (const ports of [midi.inputs, midi.outputs]) {
    for (const [, port] of ports) {
      const input = port instanceof MIDIInput
      if (enabled) {
        port.open()
        if (input) {
          port.onmidimessage = ({ data }) => {
            if (data.length === 3 && data[0] === 0xb0 && data[1] === 0x10 && data[2] === 0x7f) {
              buttonPressCallback(data)
            }
          }
        } else {
          port.send([0xb0, 0x11, lastLEDValue])
          outputs.push(port)
        }
      } else {
        port.close()
      }
    }
  }
}

userConfig.subscribe(({ enableMIDIButtonBox }) => {
  if (midi) {
    updateMidiDevices(enableMIDIButtonBox)
  }
})

export let setLED = (value, skipSave = false) => {
  console.log(`Set LED to ${value}`)
  for (const port of outputs) {
    port.send([0xb0, 0x11, value])
  }
  if (!skipSave) {
    lastLEDValue = value
  }
}

export let registerButtonPressCallback = (callback) => (buttonPressCallback = callback)
;(async () => {
  midi = await navigator.requestMIDIAccess({ sysex: true })
  updateMidiDevices()
  midi.onstatechange = () => updateMidiDevices()
})()
