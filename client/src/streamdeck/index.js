import { openDevice } from '@elgato-stream-deck/webhid'
import { VENDOR_ID, DEVICE_MODELS } from '@elgato-stream-deck/core'

const validProductIds = new Set(DEVICE_MODELS.map((spec) => spec.productId))
const isStreamDeck = (device) => {
  return device.vendorId === VENDOR_ID && validProductIds.has(device.productId)
}

const [font, fontPath] = ['Undefined Medium Local', 'undefined-medium']
const icons = {}

const initialize = async () => {
  const undefinedMedium = new window.FontFace(font, `url(assets/fonts/${fontPath}.woff2)`)
  await undefinedMedium.load()
  document.fonts.add(undefinedMedium)

  const iconLoadPromises = []

  for (const iconName of ['tomato', 'mdi-play', 'mdi-pause']) {
    const icon = new window.Image()
    iconLoadPromises.push(new Promise((resolve) => {
      icon.onload = resolve
      icon.src = `assets/icons/${iconName}.svg`
    }))
    icons[iconName] = icon
  }
  await Promise.all(iconLoadPromises)
}

const invertCanvas = (canvas) => {
  const invertedCanvas = new window.OffscreenCanvas(canvas.width, canvas.height)
  const invertedCtx = invertedCanvas.getContext('2d', { willReadFrequently: true })

  invertedCtx.drawImage(canvas, 0, 0)
  invertedCtx.fillStyle = 'white'
  invertedCtx.globalCompositeOperation = 'difference'
  invertedCtx.globalAlpha = 1
  invertedCtx.fillRect(0, 0, canvas.width, canvas.height)
  invertedCtx.fill()
  return invertedCanvas
}

const renderText = (text, iconSize, verticalPadding = 8, horizontalPadding = 7, verticalLinePadding = 4) => {
  const canvas = new window.OffscreenCanvas(iconSize, iconSize)
  const ctx = canvas.getContext('2d', { willReadFrequently: true })

  ctx.fillStyle = 'black'
  ctx.fillRect(0, 0, iconSize, iconSize)
  ctx.fill()
  ctx.fillStyle = 'white'

  const lines = text.split('\n')
  const moreThanOneLine = Math.min(1, lines.length - 1)
  const totalHeight = iconSize - verticalPadding * 2 + verticalLinePadding * moreThanOneLine
  const lineHeight = totalHeight / lines.length - verticalLinePadding * moreThanOneLine

  for (let lineNum = 0; lineNum < lines.length; lineNum++) {
    const line = lines[lineNum]
    let fontWidth, fontHeight

    for (let fontPx = 80; fontPx >= 8; fontPx--) {
      ctx.font = `${fontPx}px ${font}`
      const measure = ctx.measureText(line)
      fontWidth = measure.width
      fontHeight = measure.actualBoundingBoxAscent + measure.actualBoundingBoxDescent

      if (
        fontWidth <= (iconSize - horizontalPadding * 2) &&
        fontHeight <= lineHeight) {
        break
      }
    }

    const stretchFactor = lineHeight / fontHeight
    // TODO take into account that 5 somewhere?
    ctx.setTransform(1, 0, 0, stretchFactor, 0, 0)
    ctx.textAlign = 'center'
    ctx.fillText(line, iconSize / 2, fontHeight + (verticalPadding + (lineHeight + verticalLinePadding) * lineNum) / stretchFactor)
    ctx.restore()
  }

  return canvas
}

const setupStreamDeck = async () => {
  const streamDecks = (await navigator.hid.getDevices()).filter(device => isStreamDeck(device))
  if (streamDecks.length === 0) {
    return null
  }
  const streamDeck = await openDevice(streamDecks[0])
  await streamDeck.clearPanel()
  await streamDeck.setBrightness(100)

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

  const canvases = [
    renderText('PLAY\nSTOPSET\nNOW!', streamDeck.ICON_SIZE),
    playIconCanvas,
    renderText('PAUSE', streamDeck.ICON_SIZE),
    pauseIconCanvas,
    tomatoIconCanvas,
    renderText('PLAY', streamDeck.ICON_SIZE),
  ]

  const invertedCanvases = canvases.map((canvas) => invertCanvas(canvas))

  for (let i = 0; i < canvases.length; i++) {
    await streamDeck.fillKeyCanvas(i, canvases[i])
  }

  streamDeck.on('down', async (keyIndex) => {
    const row = Math.floor(keyIndex / streamDeck.KEY_COLUMNS) + 1
    const column = (keyIndex % streamDeck.KEY_COLUMNS) + 1
    console.log(`Pressed ${row}:${column}`)
    await streamDeck.fillKeyCanvas(keyIndex, invertedCanvases[keyIndex])
  })

  streamDeck.on('up', async (keyIndex) => {
    await streamDeck.fillKeyCanvas(keyIndex, canvases[keyIndex])
  })

  streamDeck.on('error', async (error) => {
    console.error(error)
  })

  return streamDeck
}

await initialize()

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

// TODO better hooking to force waiting
window.addEventListener('beforeunload', async () => {
  if (streamDeck) {
    await streamDeck.resetToLogo()
  }
})
