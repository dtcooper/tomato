import { openDevice } from '@elgato-stream-deck/webhid'
import { VENDOR_ID, DEVICE_MODELS } from '@elgato-stream-deck/core'

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

  const canvas = document.createElement('canvas')
  canvas.width = canvas.height = streamDeck.ICON_SIZE
  const ctx = canvas.getContext('2d')

  const grd = ctx.createLinearGradient(0, 0, streamDeck.ICON_SIZE, streamDeck.ICON_SIZE)
  grd.addColorStop(0, '#933')
  grd.addColorStop(1, '#111')
  ctx.fillStyle = grd
  ctx.fillRect(0, 0, streamDeck.ICON_SIZE, streamDeck.ICON_SIZE)
  ctx.fill()
  ctx.fillStyle = 'lime'
  ctx.font = '28px Undefined Medium Local'
  ctx.textBaseline = 'middle'
  ctx.textAlign = 'center'
  console.log(ctx.measureText('PLAY').width)
  ctx.scale(1, 2.65)
  ctx.fillText('PLAY', streamDeck.ICON_SIZE / 2 + 1, streamDeck.ICON_SIZE / (2 * 2.65) + 1)
  ctx.restore()

  const invertedCanvas = document.createElement('canvas')
  invertedCanvas.width = invertedCanvas.height = streamDeck.ICON_SIZE
  const invertedCtx = invertedCanvas.getContext('2d')

  invertedCtx.drawImage(canvas, 0, 0)
  invertedCtx.fillStyle = 'white'
  invertedCtx.globalCompositeOperation='difference';
  invertedCtx.globalAlpha = 1;  // alpha 0 = no effect 1 = full effect
  invertedCtx.fillRect(0, 0, streamDeck.ICON_SIZE, streamDeck.ICON_SIZE)
  invertedCtx.fill()

  for (let i = 0; i < streamDeck.NUM_KEYS; i++) {
    await streamDeck.fillKeyCanvas(i, canvas)
  }
  await streamDeck.setBrightness(100)

  streamDeck.on('down', async (keyIndex) => {
    await streamDeck.fillKeyCanvas(keyIndex, invertedCanvas)
    console.log('key %d down', keyIndex)
  })

  streamDeck.on('up', async (keyIndex) => {
    await streamDeck.fillKeyCanvas(keyIndex, canvas)
    console.log('key %d up', keyIndex)
  })

  streamDeck.on('error', async (error) => {
    console.error(error)
  })

  return streamDeck
}

document.addEventListener('alpine:init', async () => {
  let streamDeck = window.streamDeck = await setupStreamDeck()

  navigator.hid.addEventListener('connect', async (event) => {
    if (!streamDeck) {
      streamDeck = window.streamDeck = await setupStreamDeck()
    }
  })

  navigator.hid.addEventListener('disconnect', async (event) => {
    if (streamDeck?.device?.device?.device === event.device) {
      await streamDeck.close()
      streamDeck = window.streamDeck = null
    }
  })

  window.addEventListener('beforeunload', async () => {
    if (streamDeck) {
      await streamDeck.resetToLogo()
    }
  })
})
