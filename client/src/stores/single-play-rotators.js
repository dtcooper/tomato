import { derived, writable } from "svelte/store"
import { progressBarAnimationFramerate } from "../utils"
import { alert } from "./alerts"
import { log } from "./client-logs"
import { userConfig } from "./config"
import { db, markPlayed } from "./db"
import { audioContext, inputNode } from "./player"

const audio = new Audio()
const audioSource = audioContext.createMediaElementSource(audio)
audioSource.connect(inputNode)

let interval = null

const notPlayingTemplate = {
  asset: null,
  isPlaying: false,
  duration: 0,
  elapsed: 0,
  remaining: 0,
  rotator: null
}
export const playing = writable({
  ...notPlayingTemplate,
  errors: new Map()
})

export const singlePlayRotators = derived([userConfig, db, playing], ([$userConfig, $db, $playing]) => {
  const rotators = Array.from($db.rotators.values()).filter((r) => r.is_single_play)
  rotators.sort((a, b) => a.name.toLowerCase().localeCompare(b.name.toLowerCase()))
  return {
    enabled: rotators.length > 0 && $userConfig.uiMode > 0,
    ...$playing,
    rotators
  }
})

const error = (error) => {
  stop()
  alert(error, "error", 7500)
}

export const stop = () => {
  clearInterval(interval)
  audio.ondurationchange = audio.ontimeupdate = audio.onended = audio.onerror = audio.onpause = null
  audio.pause()
  playing.update(($playing) => ({ ...$playing, ...notPlayingTemplate }))
}

export const play = (asset, rotator) => {
  clearInterval(interval) // Just in case we enter twice

  log("played_single", `[Rotator=${rotator.name}] [Asset=${asset.name}]`)
  const files = [
    [asset.duration, asset.file.localUrl],
    ...asset.alternates.map(({ duration, localUrl }) => [duration, localUrl])
  ]
  const [duration, localUrl] = files[Math.floor(Math.random() * files.length)] // just pick a file (or alternate) at random
  markPlayed(asset, rotator)
  playing.update(($playing) => ({
    ...$playing,
    asset,
    duration,
    elapsed: 0,
    isPlaying: true,
    remaining: 0,
    rotator
  }))
  audio.src = localUrl
  audio.play()
  audio.ondurationchange = () =>
    playing.update(($playing) => ({
      ...$playing,
      duration: audio.duration,
      remaining: audio.duration - audio.currentTime || 0
    }))
  audio.ontimeupdate = () =>
    playing.update(($playing) => ({
      ...$playing,
      elapsed: audio.currentTime || 0,
      remaining: audio.duration - audio.currentTime || 0
    }))
  audio.onended = () => stop()
  audio.onerror = () => error(`Error playing asset: ${asset.name}`)
  audio.onpause = () => {
    // In the unlikely event we get a pause event from the OS?
    audio.pause()
    stop()
  }
  interval = setInterval(() => {
    playing.update(($playing) => ({ ...$playing, elapsed: audio.currentTime }))
  }, progressBarAnimationFramerate)
}

export const playFromRotator = (rotator, mediumIgnoreIds = new Set()) => {
  clearInterval(interval) // Just in case we enter twice
  const asset = rotator.getRandomAssetForSinglePlay(mediumIgnoreIds)
  if (asset) {
    play(asset, rotator)
  } else {
    error(`No assets to play from ${rotator.name}!`)
  }
}
