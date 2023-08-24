import { derived, writable } from "svelte/store"
import { progressBarAnimationFramerate } from "../utils"
import { log } from "./client-logs"
import { userConfig } from "./config"
import { db, markPlayed } from "./db"

const audio = new Audio()
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

const error = (rotator, error) => {
  stop()
  playing.update(($playing) => {
    const errors = $playing.errors
    errors.set(rotator.id, error)
    return { ...$playing, errors }
  })
  setTimeout(() => {
    playing.update(($playing) => {
      const errors = $playing.errors
      errors.delete(rotator.id)
      return { ...$playing, errors }
    })
  }, 2000)
}

export const stop = () => {
  clearInterval(interval)
  audio.ondurationchange = audio.ontimeupdate = audio.onended = audio.onerror = audio.onpause = null
  audio.pause()
  playing.update(($playing) => ({ ...$playing, ...notPlayingTemplate }))
}

export const play = (rotator, mediumIgnoreIds = new Set()) => {
  clearInterval(interval) // Just in case we enter twice
  const asset = rotator.getAsset(mediumIgnoreIds)
  if (!asset) {
    error(rotator, "No assets to play!")
  } else {
    log("played_single", `[Rotator=${rotator.name}] [Asset=${asset.name}]`)
    markPlayed(asset)
    playing.update(($playing) => ({
      ...$playing,
      asset,
      duration: asset.duration,
      elapsed: 0,
      isPlaying: true,
      remaining: 0,
      rotator
    }))
    audio.src = asset.file.localUrl
    audio.play().catch(() => error(rotator, "Error playing asset"))
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
    audio.onerror = () => error(rotator, "Error playing asset")
    audio.onpause = () => {
      // In the unlikely event we get a pause event from the OS?
      audio.pause()
      stop()
    }
    interval = setInterval(() => {
      playing.update(($playing) => ({ ...$playing, elapsed: audio.currentTime }))
    }, progressBarAnimationFramerate)
  }
}
