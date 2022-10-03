import { openDevice } from '@elgato-stream-deck/webhid'
import { VENDOR_ID, DEVICE_MODELS } from '@elgato-stream-deck/core'

const randInt = (max) => Math.floor(Math.random() * max)

const validProductIds = new Set(DEVICE_MODELS.map((spec) => spec.productId))
const isStreamDeck = (device) => {
  return device.vendorId === VENDOR_ID && validProductIds.has(device.productId)
}

const setupStreamDeck = async () => {
  const streamDecks = (await navigator.hid.getDevices()).filter(device => isStreamDeck(device))
  if (streamDecks.length === 0) {
    return null
  }

  const streamDeck = await openDevice(streamDecks[0])
  for (let i = 0; i < streamDeck.NUM_KEYS; i++) {
    await streamDeck.fillKeyColor(i, 0, 0, 0xFF)
  }
  await streamDeck.setBrightness(100)

  streamDeck.on('down', async (keyIndex) => {
    await streamDeck.fillKeyColor(keyIndex, 0xFF, 0, 0)
    console.log('key %d down', keyIndex)
  })

  streamDeck.on('up', async (keyIndex) => {
    await streamDeck.fillKeyColor(keyIndex, 0, 0, 0xFF)
    console.log('key %d up', keyIndex)
  })

  streamDeck.on('error', (error) => {
    console.error(error)
  })

  return streamDeck
}

document.addEventListener('alpine:init', async () => {
  let streamDeck = await setupStreamDeck()

  navigator.hid.addEventListener('connect', async (event) => {
    if (!streamDeck) {
      streamDeck = await setupStreamDeck()
    }
  })

  navigator.hid.addEventListener('disconnect', async (event) => {
    if (streamDeck?.device?.device?.device === event.device) {
      await streamDeck.close()
      streamDeck = null
    }
  })
})
