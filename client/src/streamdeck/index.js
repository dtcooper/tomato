import { openDevice } from '@elgato-stream-deck/webhid'
import { VENDOR_ID, DEVICE_MODELS } from '@elgato-stream-deck/core'

const validProductIds = new Set(DEVICE_MODELS.map((spec) => spec.productId))
const isStreamDeck = (device) => {
  return device.vendorId === VENDOR_ID && validProductIds.has(device.productId)
}

const [font, fontPath] = ['Undefined Medium Local', 'undefined-medium']

const renderText = (text, iconSize, verticalPadding = 15, horizontalPadding = 5) => {
  const canvas = document.createElement('canvas')
  canvas.width = canvas.height = iconSize
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

  const invertedCanvas = document.createElement('canvas')
  invertedCanvas.width = invertedCanvas.height = iconSize
  const invertedCtx = invertedCanvas.getContext('2d', { willReadFrequently: true })

  invertedCtx.drawImage(canvas, 0, 0)
  invertedCtx.fillStyle = 'white'
  invertedCtx.globalCompositeOperation = 'difference'
  invertedCtx.globalAlpha = 1
  invertedCtx.fillRect(0, 0, iconSize, iconSize)
  invertedCtx.fill()

  return { canvas, invertedCanvas }
}

const setupStreamDeck = async () => {
  const streamDecks = (await navigator.hid.getDevices()).filter(device => isStreamDeck(device))
  if (streamDecks.length === 0) {
    return null
  }
  const streamDeck = await openDevice(streamDecks[0])
  await streamDeck.setBrightness(100)
  const { canvas: playCanvas, invertedCanvas: playInvertedCanvas } = renderText('PLAY', streamDeck.ICON_SIZE)
  const { canvas: pauseCanvas, invertedCanvas: pauseInvertedCanvas } = renderText('PAUSE', streamDeck.ICON_SIZE)
  const { canvas: nextCanvas, invertedCanvas: nextInvertedCanvas } = renderText('NEXT', streamDeck.ICON_SIZE)
  const tomatoSvg = new window.Image()
  await new Promise((resolve) => {
    tomatoSvg.onload = resolve
    tomatoSvg.src = '../assets/icons/tomato.svg'
  })

  const tomatoCanvas = document.createElement('canvas')
  const tomatoCtx = tomatoCanvas.getContext('2d', { willReadFrequently: true })
  const tomatoPadding = 2
  tomatoCtx.drawImage(tomatoSvg, tomatoPadding, tomatoPadding, streamDeck.ICON_SIZE - tomatoPadding * 2, streamDeck.ICON_SIZE - tomatoPadding * 2)

  const playIndex = 0
  const pauseIndex = streamDeck.KEY_COLUMNS
  const nextIndex = streamDeck.KEY_ROWS * streamDeck.KEY_COLUMNS - 1
  for (let i = 0; i < streamDeck.NUM_KEYS; i++) {
    if (i !== playIndex && i !== pauseIndex && i !== nextIndex) {
      await streamDeck.fillKeyCanvas(i, tomatoCanvas)
    }
  }
  await streamDeck.fillKeyCanvas(playIndex, playCanvas)
  await streamDeck.fillKeyCanvas(pauseIndex, pauseCanvas)
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
  const undefinedMedium = new window.FontFace(font, `url(../assets/fonts/${fontPath}.woff2)`)
  await undefinedMedium.load()
  document.fonts.add(undefinedMedium)

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
