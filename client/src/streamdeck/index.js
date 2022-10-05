import Alpine from 'alpinejs'
import { openDevice } from '@elgato-stream-deck/webhid'
import { VENDOR_ID, DEVICE_MODELS } from '@elgato-stream-deck/core'

const validProductIds = new Set(DEVICE_MODELS.map((spec) => spec.productId))
const isStreamDeck = (device) => {
  return device.vendorId === VENDOR_ID && validProductIds.has(device.productId)
}

const [font, fontPath] = ['Undefined Medium Local', 'undefined-medium']
const icons = {}

const initialize = async () => {
  const undefinedMedium = new window.FontFace(font, `url(../assets/fonts/${fontPath}.woff2)`)
  await undefinedMedium.load()
  document.fonts.add(undefinedMedium)

  const iconLoadPromises = []

  for (const iconName of ['tomato', 'mdi-play', 'mdi-pause']) {
    const icon = new window.Image()
    iconLoadPromises.push(new Promise((resolve) => {
      icon.onload = resolve
      icon.src = `../assets/icons/${iconName}.svg`
    }))
    icons[iconName] = icon
  }
  await Promise.all(iconLoadPromises)
}

const renderText = (text, iconSize, verticalPadding = 15, horizontalPadding = 5) => {
  const canvas = new window.OffscreenCanvas(iconSize, iconSize)
  const ctx = canvas.getContext('2d', { willReadFrequently: true })

  ctx.fillStyle = 'black'
  ctx.fillRect(0, 0, iconSize, iconSize)
  ctx.fill()
  ctx.fillStyle = 'white'

  let fontWidth, fontHeight

  for (let fontPx = 80; fontPx >= 8; fontPx--) {
    ctx.font = `${fontPx}px ${font}`
    const measure = ctx.measureText(text)
    fontWidth = measure.width
    fontHeight = measure.actualBoundingBoxAscent + measure.actualBoundingBoxDescent

    if (
      fontWidth <= (iconSize - horizontalPadding * 2) &&
      fontHeight <= (iconSize - verticalPadding * 2)) {
      break
    }
  }

  const desiredHeight = iconSize - verticalPadding * 2
  const stretchFactor = desiredHeight / fontHeight
  ctx.scale(1, stretchFactor)
  ctx.fillText(text, horizontalPadding, fontHeight + verticalPadding / stretchFactor)
  ctx.restore()

  const invertedCanvas = new window.OffscreenCanvas(iconSize, iconSize)
  const invertedCtx = invertedCanvas.getContext('2d', { willReadFrequently: true })

  invertedCtx.drawImage(canvas, 0, 0)
  invertedCtx.fillStyle = 'white'
  invertedCtx.globalCompositeOperation = 'difference'
  invertedCtx.globalAlpha = 1
  invertedCtx.fillRect(0, 0, iconSize, iconSize)
  invertedCtx.fill()

  return { canvas, invertedCanvas }
}

const setupStreamDeck = async (conn) => {
  const streamDecks = (await navigator.hid.getDevices()).filter(device => isStreamDeck(device))
  if (streamDecks.length === 0) {
    return null
  }
  const streamDeck = await openDevice(streamDecks[0])
  await streamDeck.setBrightness(100)
  const { canvas: playCanvas, invertedCanvas: playInvertedCanvas } = renderText('PLAY', streamDeck.ICON_SIZE)
  const { canvas: pauseCanvas, invertedCanvas: pauseInvertedCanvas } = renderText('PAUSE', streamDeck.ICON_SIZE)
  const { canvas: nextCanvas, invertedCanvas: nextInvertedCanvas } = renderText('NEXT', streamDeck.ICON_SIZE)
  const playIconCanvas = new window.OffscreenCanvas(streamDeck.ICON_SIZE, streamDeck.ICON_SIZE)
  let ctx = playIconCanvas.getContext('2d', { willReadFrequently: true })
  ctx.fillStyle = '#36D399'
  ctx.fillRect(0, 0, streamDeck.ICON_SIZE, streamDeck.ICON_SIZE)
  ctx.fill()
  ctx.globalCompositeOperation = 'destination-in'
  ctx.drawImage(icons['mdi-play'], 0, 0, streamDeck.ICON_SIZE, streamDeck.ICON_SIZE)

  const pauseIconCanvas = new window.OffscreenCanvas(streamDeck.ICON_SIZE, streamDeck.ICON_SIZE)
  ctx = pauseIconCanvas.getContext('2d', { willReadFrequently: true })
  ctx.fillStyle = '#FBBD23'
  ctx.fillRect(0, 0, streamDeck.ICON_SIZE, streamDeck.ICON_SIZE)
  ctx.fill()
  ctx.globalCompositeOperation = 'destination-in'
  ctx.drawImage(icons['mdi-pause'], 0, 0, streamDeck.ICON_SIZE, streamDeck.ICON_SIZE)

  const tomatoIconCanvas = new window.OffscreenCanvas(streamDeck.ICON_SIZE, streamDeck.ICON_SIZE)
  ctx = tomatoIconCanvas.getContext('2d', { willReadFrequently: true })
  ctx.fillStyle = '#00000000'
  ctx.fillRect(0, 0, streamDeck.ICON_SIZE, streamDeck.ICON_SIZE)
  ctx.fill()
  ctx.drawImage(icons.tomato, 5, 5, streamDeck.ICON_SIZE - 10, streamDeck.ICON_SIZE - 10)

  const playIndex = 0
  const pauseIndex = streamDeck.KEY_COLUMNS
  const nextIndex = streamDeck.KEY_ROWS * streamDeck.KEY_COLUMNS - 1
  await streamDeck.fillKeyCanvas(playIndex, playCanvas)
  await streamDeck.fillKeyCanvas(1, playIconCanvas)
  await streamDeck.fillKeyCanvas(2, pauseIconCanvas)
  await streamDeck.fillKeyCanvas(pauseIndex, pauseCanvas)
  await streamDeck.fillKeyCanvas(4, tomatoIconCanvas)
  await streamDeck.fillKeyCanvas(nextIndex, nextCanvas)

  streamDeck.on('down', async (keyIndex) => {
    if (keyIndex === playIndex) {
      await streamDeck.fillKeyCanvas(keyIndex, playInvertedCanvas)
    } else if (keyIndex === pauseIndex) {
      await streamDeck.fillKeyCanvas(keyIndex, pauseInvertedCanvas)
    } else if (keyIndex === nextIndex) {
      await streamDeck.fillKeyCanvas(keyIndex, nextInvertedCanvas)
    }
  })

  streamDeck.on('up', async (keyIndex) => {
    if (keyIndex === playIndex) {
      await streamDeck.fillKeyCanvas(keyIndex, playCanvas)
    } else if (keyIndex === pauseIndex) {
      await streamDeck.fillKeyCanvas(keyIndex, pauseCanvas)
    } else if (keyIndex === nextIndex) {
      await streamDeck.fillKeyCanvas(keyIndex, nextCanvas)
    }
  })

  streamDeck.on('error', async (error) => {
    console.error(error)
  })

  return streamDeck
}

document.addEventListener('alpine:init', async () => {
  await initialize()

  const conn = Alpine.store('conn')
  let streamDeck = await setupStreamDeck(conn)

  navigator.hid.addEventListener('connect', async (event) => {
    if (!streamDeck) {
      streamDeck = await setupStreamDeck(conn)
    }
  })

  navigator.hid.addEventListener('disconnect', async (event) => {
    if (streamDeck?.device?.device?.device === event.device) {
      await streamDeck.close()
      streamDeck = null
    }
  })

  // TODO better hooking to force waiting
  window.addEventListener('beforeunload', async () => {
    if (streamDeck) {
      await streamDeck.resetToLogo()
    }
  })
})
