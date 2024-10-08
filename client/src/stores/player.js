import dayjs from "dayjs"
import { persisted } from "svelte-local-storage-store"
import { noop } from "svelte/internal"
import { derived, get, writable } from "svelte/store"
import { prettyDuration, progressBarAnimationFramerate } from "../utils"
import { log } from "./client-logs"
import { config, userConfig } from "./config"
import { markPlayed } from "./db"

export const speaker = persisted("speaker", null)
export const speakers = writable([])
export const playStatus = derived([speaker, speakers], ([$speaker, $speakers]) => ({
  speaker: $speaker,
  speakers: $speakers
}))
export const blockSpacebarPlay = writable(false)

// Web Audio API stuff
let compressorEnabled = false
let vizEnabled = false

export const audioContext = new AudioContext()

export const inputNode = audioContext.createGain() // Used by single play rotators too
inputNode.gain.value = 1

const mediaStreamDest = audioContext.createMediaStreamDestination()
export const mediaStreamMonitor = mediaStreamDest.stream

const outputNode = audioContext.createGain()
outputNode.gain.value = 1

// Thanks ChatGPT!
const compressor = audioContext.createDynamicsCompressor()
compressor.threshold.setValueAtTime(-25, audioContext.currentTime) // In dB, typically around -20 to -15 dBFS
compressor.ratio.setValueAtTime(4, audioContext.currentTime) // Typically around 2:1 to 4:1
compressor.attack.setValueAtTime(0.005, audioContext.currentTime) // In seconds, typically 5 ms to 20 ms
compressor.release.setValueAtTime(0.2, audioContext.currentTime) // In seconds, typically 100 ms to 300 ms
compressor.knee.setValueAtTime(6, audioContext.currentTime) // In dB, typically around 2 dB to 6 dB

const limiter = audioContext.createDynamicsCompressor()
limiter.threshold.setValueAtTime(-2, audioContext.currentTime) // In dB, to prevent clipping
limiter.ratio.setValueAtTime(20, audioContext.currentTime) // High ratio to act as a limiter
limiter.attack.setValueAtTime(0.001, audioContext.currentTime) // Fast attack time
limiter.release.setValueAtTime(0.02, audioContext.currentTime) // Relatively fast release time

compressor.connect(limiter)
limiter.connect(outputNode) // Route limiter to outputNode (path has no audio input when compression off)

outputNode.connect(audioContext.destination) // Route outputNode to speaker

/*
  Without compression:
    >>> inputNode => outputNode => destination

  With compression:
    >>> inputNode => compressor => limiter => outputNode => destination

  When visualizer is turned on (connection severed when visualizer off)
    >>> outputNode => mediaStreamDest
*/

// To start, route inputNode to outputNode (compression disabled)
inputNode.connect(outputNode)

config.subscribe(({ BROADCAST_COMPRESSION: enabled }) => {
  enabled = !!enabled // Make sure it's a bool
  if (enabled !== compressorEnabled) {
    if (enabled) {
      // Swap inputNode routing from outputNode to compressor (begin of compression chain)
      inputNode.disconnect(outputNode)
      inputNode.connect(compressor)
    } else {
      // Swap inputNode routing from compressor to outputNode (disabled compression chain)
      inputNode.disconnect(compressor)
      inputNode.connect(outputNode)
    }
    compressorEnabled = enabled
    console.log(`${enabled ? "Enabled" : "Disabled"} broadcast compression`)
  }
})

userConfig.subscribe(({ showViz: enabled }) => {
  enabled = !!enabled // Make sure it's a bool
  if (enabled !== vizEnabled) {
    if (enabled) {
      // Route outputNode to the media stream for WaveSurfer visualization
      outputNode.connect(mediaStreamDest)
    } else {
      // Remove routing of output node to media stream (visualization disabled)
      outputNode.disconnect(mediaStreamDest)
    }
    vizEnabled = enabled
    console.log(`${enabled ? "Connected" : "Disconnected"} visualizer media stream`)
  }
})

let currentGeneratedId = 0
const assetAlternateTracker = new Map()

class GeneratedStopsetAssetBase {
  constructor(rotator, generatedStopset, index, hasEndDateMultiplier, isSwapped = false) {
    this.rotator = rotator
    this.generatedStopset = generatedStopset
    this.index = index
    this.hasEndDateMultiplier = hasEndDateMultiplier
    this.error = false
    this.playing = false
    this.alternateNumber = 0
    this.isSwapped = isSwapped
  }

  serializeForSubscriber() {
    return {
      playable: this.playable,
      beforeActive: this.beforeActive,
      afterActive: this.afterActive,
      active: this.active,
      rotator: {
        id: this.rotator.id,
        name: this.rotator.name
      }
    }
  }

  updateCallback() {
    this.generatedStopset.updateCallback()
  }

  get color() {
    return this.rotator.color
  }

  get beforeActive() {
    return this.generatedStopset.current > this.index
  }
  get active() {
    return this.generatedStopset.current === this.index
  }
  get afterActive() {
    return this.generatedStopset.current < this.index
  }
  get finished() {
    return this.beforeActive
  }

  isAlternate() {
    return this.alternateNumber > 0
  }

  get logLine() {
    const stopset = this.generatedStopset
    let line = `[Stopset=${stopset.name}] [Rotator=${this.rotator.name}] [${this.index + 1}/${
      stopset.items.length
    }] [Asset=${this.name}]`
    if (this.alternateNumber > 0) {
      line += ` [Alt=${this.alternateNumber}]`
    }
    if (this.isSwapped) {
      line += " [Swapped]"
    }
    return line
  }

  done() {
    this.playing = false
    this.generatedStopset.donePlaying()
    this.updateCallback()
  }
}

class PlayableAsset extends GeneratedStopsetAssetBase {
  static _reusableAudioObjects = []

  constructor({ duration, ...asset }, ...args) {
    super(...args)
    // Assigns asset._db, which holds a reference to the underlying asset object
    // therefore a reference to the _original_ asset is held and it won't be garbage
    // collected and cleaned  up yet
    Object.assign(this, asset)

    if (this.alternates.length > 0) {
      if (assetAlternateTracker.has(this.id)) {
        this.alternateNumber = (assetAlternateTracker.get(this.id) + 1) % (this.alternates.length + 1)
      }
      if (this.alternateNumber > 0) {
        const alternate = this.alternates[this.alternateNumber - 1]
        duration = alternate.duration
        this.file = alternate
      }
      assetAlternateTracker.set(this.id, this.alternateNumber)
    }

    this._elapsed = 0
    this.playable = true
    this.audio = null
    this.error = false
    this.interval = null
    this._duration = duration
    this.doNotPauseStopsetOnPause = false
    this.didSkip = false
    this.didLogError = false
    this.queueForSkip = false
  }

  serializeForSubscriber() {
    return {
      name: this.name,
      id: this.id,
      duration: this.duration,
      elapsed: this.elapsed,
      remaining: this.remaining,
      ...super.serializeForSubscriber()
    }
  }

  static getAudioObject() {
    let audio = PlayableAsset._reusableAudioObjects.find((item) => !item.__tomato_used)

    if (!audio) {
      audio = new Audio()
      const audioSource = audioContext.createMediaElementSource(audio)
      audioSource.connect(inputNode)
      PlayableAsset._reusableAudioObjects.push(audio)
    }
    audio.__tomato_used = true

    if (PlayableAsset._reusableAudioObjects.length > 50) {
      console.warn(
        `Length of re-usable audio objects ${PlayableAsset._reusableAudioObjects.length} > 50. Really long stop sets could cause this.`
      )
      log("internal_error", `Length of re-usable audion objects ${PlayableAsset._reusableAudioObjects.length} > 50.`)
    }
    return audio
  }

  get duration() {
    return this.error ? 0 : this._duration
  }

  get elapsed() {
    return this.error ? 0 : this.beforeActive ? this.duration : this._elapsed
  }

  loadAudio() {
    if (!this.audio) {
      this.audio = PlayableAsset.getAudioObject()

      this.audio.ondurationchange = () => {
        this._duration = this.audio.duration
        this.updateCallback()
      }
      this.audio.ontimeupdate = () => {
        this._elapsed = this.audio.currentTime
        this.updateCallback()
      }
      this.audio.onended = () => this.done()
      this.audio.onerror = (e) => this._errorHelper(e)
      this.audio.onpause = () => {
        if (this.playing) {
          if (this.doNotPauseStopset) {
            this.generatedStopset.playing = false
          }
          this.pause()
        }
      }
      this.audio.src = this.file.localUrl
    }
  }

  unloadAudio() {
    clearInterval(this.interval)
    if (this.audio) {
      this.audio.ondurationchange =
        this.audio.ontimeupdate =
        this.audio.onerror =
        this.audio.onended =
        this.audio.onpause =
          null
      this.audio.pause()
      this.audio.__tomato_used = false
      this.audio = null
    }
  }

  get remaining() {
    return Math.max(this.duration - this.elapsed, 0)
  }

  get percentDone() {
    return Math.min((this.elapsed / this.duration) * 100, 100)
  }

  _errorHelper(e) {
    console.error("audio error:", e, `${this.name} / ${this.file.localUrl}`)
    this.error = true
    if (!this.didLogError) {
      this.didLogError = true
      log("internal_error", `Audio error with asset ${this.name}`)
    }
    if (this.playing) {
      this.playing = false
      this.done()
    }
  }

  play() {
    if (this.queueForSkip) {
      console.log(`Skipping queued ${this.id}: ${this.name}`)
      this.generatedStopset.didSkip = true
      this.skip()
    } else {
      console.log(`Playing ${this.id}: ${this.name}`)
      markPlayed(this)

      if (this.error) {
        this.done()
      } else {
        this.playing = true
        this.audio.play()
        clearInterval(this.interval)
        this.interval = setInterval(() => {
          if (this.audio && !this.error) {
            this._elapsed = this.audio.currentTime
            this.updateCallback()
          }
        }, progressBarAnimationFramerate)
      }
    }
    this.updateCallback()
  }

  done() {
    clearInterval(this.interval)
    log(this.didSkip ? "skipped_asset" : "played_asset", this.logLine)
    super.done()
  }

  skip() {
    this.didSkip = true
    this.pause()
    this.done()
  }

  pause() {
    clearInterval(this.interval)
    this.playing = false
    this.audio.pause()
    this.updateCallback()
  }

  toString() {
    return `${this.name} [${this.file.localUrl}]`
  }
}

class NonPlayableAsset extends GeneratedStopsetAssetBase {
  constructor(...args) {
    super(...args)
    this.playable = false
  }

  play() {
    console.log("Called play() on non-playable asset")
    this.done()
  }
}

export class GeneratedStopset {
  constructor(stopset, rotatorsAndAssets, doneCallback, updateCallback, generatedId) {
    this.generatedId = generatedId === undefined ? currentGeneratedId++ : generatedId
    Object.assign(this, stopset)
    this.updateCallback = updateCallback || noop // UI update function
    this.doneCallback = doneCallback || noop
    this.items = rotatorsAndAssets.map(({ rotator, asset, hasEndDateMultiplier }, index) => {
      const args = [rotator, this, index, hasEndDateMultiplier, false]
      return asset ? new PlayableAsset(asset, ...args) : new NonPlayableAsset(...args)
    })
    this.current = 0
    this.loaded = false
    this.type = "stopset"
    this.playing = false
    this.startedPlaying = false
    this.didSkip = false
    this.didLog = false
    this.destroyed = false
  }

  serializeForSubscriber() {
    return {
      name: this.name,
      id: this.generatedId,
      type: this.type,
      startedPlaying: this.startedPlaying,
      current: this.current,
      duration: this.duration,
      elapsed: this.elapsed,
      remaining: this.remaining,
      playing: this.playing,
      items: this.items.map((item) => item.serializeForSubscriber())
    }
  }

  get duration() {
    return this.playableItems.reduce((s, item) => s + item.duration, 0)
  }
  get elapsed() {
    return this.playableItems.reduce((s, item) => s + item.elapsed, 0)
  }
  get remaining() {
    return this.playableItems.reduce((s, item) => s + item.remaining, 0)
  }
  get durationAfterQueuedSkips() {
    return this.playableItems.filter((item) => !item.queueForSkip).reduce((s, item) => s + item.duration, 0)
  }

  get playableNonErrorItems() {
    return this.playableItems.filter((item) => !item.error)
  }

  get playableItems() {
    return this.items.filter((item) => item.playable)
  }

  regenerateAsset(index, startTime, mediumIgnoreIds, endDateMultiplier) {
    if (this.items.length > index) {
      // Item will already be included in medium ignore IDs
      // Hard ignore IDs should be everything in current stopset (less item)
      const hardIgnoreIds = new Set(this.items.filter((_, i) => i !== index).map((a) => a.id))
      const secondsUntilPlay = this.items
        .slice(0, index)
        .filter((item) => item.playable)
        .reduce((s, item) => s + item.remaining, 0)
      startTime = startTime.add(secondsUntilPlay, "seconds")

      const oldItem = this.items[index]
      const rotator = oldItem.rotator
      const { asset, hasEndDateMultiplier } = oldItem.rotator.getAsset(
        mediumIgnoreIds,
        hardIgnoreIds,
        startTime,
        endDateMultiplier
      )
      const args = [rotator, this, index, hasEndDateMultiplier, true]
      const newItem = asset ? new PlayableAsset(asset, ...args) : new NonPlayableAsset(...args)

      oldItem.unloadAudio() // Don't forget to unload its audio before we nuke it
      if (this.loaded && asset) {
        newItem.loadAudio() // If stopset was already loaded, load audio for swapped in item
      }

      this.items[index] = newItem
      this.updateCallback()
    } else {
      console.warn(`Invalid subindex ${index} in stopset. Won't regenerate item.`)
    }
  }

  swapAsset(index, asset, rotator) {
    if (!this._validateIndexForAssetAction(index, "swap")) {
      return false
    }
    const oldItem = this.items[index]
    const newItem = new PlayableAsset(asset, rotator, this, index, false, true)
    oldItem.unloadAudio() // Don't forget to unload its audio before we nuke it
    if (this.loaded) {
      newItem.loadAudio() // If stopset was already loaded, load audio for swapped in item
    }
    this.items[index] = newItem // Swap it
    this.updateCallback()
    return true
  }

  insertAsset(index, asset, rotator, before) {
    if (!this._validateIndexForAssetAction(index, `insert ${before ? "before" : "after"}`)) {
      return false
    }
    const newItem = new PlayableAsset(asset, rotator, this, index, false, true)
    if (this.loaded) {
      newItem.loadAudio()
    }
    const insertIndex = index + (before ? 0 : 1)
    this.items.splice(insertIndex, 0, newItem) // Splice it in
    this.items.forEach((item, i) => (item.index = i)) // Fix item indexes
    return true
  }

  deleteAsset(index) {
    if (!this._validateIndexForAssetAction(index, "delete")) {
      return false
    }
    const oldItem = this.items[index]
    oldItem.unloadAudio() // Don't forget to unload its audio before we nuke it
    this.items.splice(index, 1) // Nuke it
    this.items.forEach((item, i) => (item.index = i)) // Fix item indexes
    return true
  }

  _validateIndexForAssetAction(index, description) {
    if (this.startedPlaying && index <= this.current) {
      console.warn(
        `Stopset action ${description} on ${this.name} index ${index} cannot occur since that item is playing/played!`
      )
      return false
    } else if (index >= this.items.length) {
      console.warn(`Stopset action ${description} on ${this.name} index ${index} cannot occur since that index invalid`)
      return false
    } else {
      return true
    }
  }

  skip() {
    this.didSkip = true
    this.items[this.current].skip()
  }

  loadAudio() {
    if (!this.loaded) {
      this.loaded = true
      this.playableItems.forEach((item) => item.loadAudio())
    }
  }

  unloadAudio() {
    if (this.loaded) {
      this.loaded = false
      this.playableItems.forEach((item) => item.unloadAudio())
    }
  }

  donePlaying() {
    this.current++
    this.updateCallback()
    if (this.current < this.items.length) {
      this.play()
    } else {
      this.done()
    }
    this.updateCallback()
  }

  done(skipCallback = false, skipLog = false, forceDidSkip = false) {
    this.playing = false
    this.destroyed = true
    this.unloadAudio()
    if (!skipCallback) {
      this.doneCallback()
    }
    if (!skipLog && !this.didLog) {
      this.didLog = true
      log(this.didSkip || forceDidSkip ? "skipped_stopset" : "played_stopset", `[Stopset=${this.name}]`)
    }
  }

  play(subindex = null) {
    if (this.items.length > 0) {
      this.loadAudio()
      if (subindex !== null && subindex !== this.current) {
        // Pause items up to subindex
        this.items.slice(this.current, subindex).forEach((item) => {
          log("skipped_asset", item.logLine)
          if (item.playable) {
            // Avoids LED and button flash since the pause as the pause() called on the asset
            // here is to pause the underlying MediaElement, not pause the whole stopset
            item.doNotPauseStopsetOnPause = true
            item.pause()
          }
        })
        this.current = subindex
      }
      this.playing = this.startedPlaying = true
      this.items[this.current].play()
      this.updateCallback()
    } else {
      // Empty for some reason (empty stopset?)
      this.done()
    }
  }

  pause() {
    this.items[this.current].pause()
    this.playing = false
    this.updateCallback()
  }
}

export class Wait {
  static currentStopsetOverdueTime = 0

  constructor(duration, doneCallback, updateCallback) {
    this.generatedId = currentGeneratedId++
    this.updateCallback = updateCallback || noop
    this.doneCallback = doneCallback || noop
    this.duration = duration
    this.name = "Wait"
    this.elapsed = 0
    this.type = "wait"
    this.overdue = false
    this.overtimeElapsed = 0
    this.overtime = false
    this.expires = null
    this.interval = null
    this.active = false
    this.didLog = false
  }

  serializeForSubscriber() {
    return {
      id: this.generatedId,
      type: this.type,
      active: this.active,
      duration: this.duration,
      elapsed: this.elapsed,
      overdue: this.overdue,
      overtime: this.overtime,
      overtimeElapsed: this.overtimeElapsed,
      remaining: this.remaining
    }
  }

  get remaining() {
    return Math.max(this.duration - this.elapsed, 0)
  }

  get percentDone() {
    return Math.min((this.elapsed / this.duration) * 100, 100)
  }

  run() {
    if (!this.active) {
      this.active = true
      this.expires = dayjs().add(this.duration, "seconds")
      this.interval = setInterval(() => {
        const secondsLeft = this.expires.diff(dayjs(), "ms") / 1000
        this.elapsed = this.duration - secondsLeft
        if (secondsLeft < 0) {
          this.doneCountdown()
        }
        this.updateCallback()
      }, progressBarAnimationFramerate)
    }
  }

  doneCountdown() {
    this.overtime = true
    clearInterval(this.interval)
    if (this.doneCallback()) {
      // returns true if we want to do overtime stuff
      this.interval = setInterval(() => {
        this.overtimeElapsed = dayjs().diff(this.expires, "ms") / 1000
        this.updateCallback()
        if (Wait.currentStopsetOverdueTime > 0 && this.overtimeElapsed > Wait.currentStopsetOverdueTime) {
          this.overdue = true
        }
      }, 333)
    }
  }

  done(skipCallback, skipLog = false) {
    // Must be able to be called twice
    clearInterval(this.interval)

    if (!skipLog && !this.didLog) {
      this.didLog = true
      log("waited", `waited for ${prettyDuration(this.elapsed + this.overtimeElapsed)}`)
      if (this.overdue) {
        log("overdue", `overdue by ${prettyDuration(this.overtimeElapsed)}`)
      }
    }

    if (!skipCallback) {
      this.doneCallback()
    }
  }
}

config.subscribe(($config) => {
  Wait.currentStopsetOverdueTime = $config.STOPSET_OVERDUE_TIME || 0
})

// Speaker stuff
export const setSpeaker = (choice) => {
  const speakers = new Map(get(playStatus).speakers)
  let choicePretty = speakers.get(choice)

  if (!choice || choice === "default" || !speakers.has(choice)) {
    choice = ""
    choicePretty = "default"
  }

  if (!speakers.has("default")) {
    console.warn("speakers does NOT contain a default entry", speakers)
  }

  console.log(`Set speaker to: ${choicePretty}${choice ? ` (${choice})` : ""}`)
  audioContext.setSinkId(choice)

  speaker.set(choice === "" ? "default" : choice)
}

const updateSpeakers = async () => {
  let newSpeakers = []
  try {
    newSpeakers = (await navigator.mediaDevices.enumerateDevices())
      .filter((d) => d.kind === "audiooutput")
      .map((d) => [d.deviceId, d.label])
  } catch (e) {
    console.error("Error getting speakers!")
  }
  newSpeakers.sort(([, a], [, b]) => {
    if (a === "default") return -1
    if (b === "default") return 1
    return a.toLowerCase().localeCompare(b.toLowerCase())
  })

  speakers.set(newSpeakers)
}

navigator.mediaDevices.ondevicechange = async () => {
  await updateSpeakers()
  setSpeaker(get(speaker))
}

// Async code called at startup
;(async () => {
  await updateSpeakers()
  setSpeaker(get(speaker))
})()
