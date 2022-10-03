import { openDevice } from '@elgato-stream-deck/webhid'

const randInt = (max) => Math.floor(Math.random() * max)

// Fill the first button form the left in the first row with a solid red color. This is asynchronous.
document.addEventListener('alpine:init', async () => {
  const hidDevices = await navigator.hid.getDevices()

  if (hidDevices.length > 0) {
    const streamDeck = await openDevice(hidDevices[0])
    for (let i = 0; i < streamDeck.NUM_KEYS; i++) {
      await streamDeck.fillKeyColor(i, 0, 0, 0)
    }

    streamDeck.on('down', (keyIndex) => {
      streamDeck.fillKeyColor(keyIndex, randInt(0xFF), randInt(0xFF), randInt(0xFF))
      console.log('key %d down', keyIndex)
    })

    streamDeck.on('up', (keyIndex) => {
      streamDeck.fillKeyColor(keyIndex, 0, 0, 0)
      console.log('key %d up', keyIndex)
    })

    streamDeck.on('error', (error) => {
      console.error(error)
    })
  }
})
