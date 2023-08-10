import dayjs from "dayjs"
import { persisted } from "svelte-local-storage-store"
import { noop } from "svelte/internal"
import { derived, get, writable } from "svelte/store"
import { config } from "./config"

export const speaker = persisted("speaker", null)
export const speakers = writable([])
export const playStatus = derived([speaker, speakers], ([$speaker, $speakers]) => ({
  speaker: $speaker,
  speakers: $speakers
}))

let compressorEnabled = false
let currentGeneratedId = 0
const audioContext = new AudioContext()

const inputNode = audioContext.createGain()
inputNode.gain.value = 1
inputNode.connect(audioContext.destination)

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
limiter.connect(audioContext.destination)

class GeneratedStopsetAssetBase {
  constructor(rotator, generatedStopset, index) {
    this.rotator = rotator
    this.generatedStopset = generatedStopset
    this.index = index
    this.error = false
    this.finished = false
    this.playing = false
  }

  updateCallback() {
    this.generatedStopset.updateCallback()
  }

  get active() {
    return this.generatedStopset.current === this.index
  }

  done(error) {
    this.finished = true
    this.playing = false
    if (error) {
      console.log(`An error occurred while playing ${this.name}`, error)
    }
    this.generatedStopset.donePlaying(this.index)
  }
}

class PlayableAsset extends GeneratedStopsetAssetBase {
  static _reusableAudioObjects = []

  constructor({ ...asset }, ...args) {
    super(...args)
    // Assigns asset._db, which holds a reference to the underlying asset object
    // therefore a reference to the _original_ asset is held and it won't be garbage
    // collected and cleaned  up yet
    Object.assign(this, asset)
    this.elapsed = 0
    this.playable = true
    this.audio = null
  }

  get color() {
    return this.rotator.color
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
    }
    return audio
  }

  loadAudio() {
    if (!this.audio) {
      this.audio = PlayableAsset.getAudioObject()

      // TODO set duration quicker than this using an interval for smoother UI?
      this.audio.ondurationchange = () => {
        this.duration = this.audio.duration
        this.updateCallback()
      }
      this.audio.ontimeupdate = () => {
        this.elapsed = this.audio.currentTime
        this.updateCallback()
      }
      this.audio.onended = () => this.done()
      this.audio.onerror = (e) => {
        this.error = true
        this.done()
      }
      this.audio.src = this.file.localUrl
    }
  }

  unloadAudio() {
    if (this.audio) {
      this.audio.ondurationchange = this.audio.ontimeupdate = this.audio.onended = this.audio.onended = null
      this.audio.pause()
      this.audio.__tomato_used = false
      this.audio = null
    }
  }

  get remaining() {
    return this.duration - this.elapsed
  }

  get percentDone() {
    return Math.min((this.elapsed / this.duration) * 100, 100)
  }

  play() {
    console.log(`Playing ${this.name}`)
    this.playing = true
    this.audio.play().catch(() => this.done())
    this.updateCallback()
  }

  skip() {
    this.play()
    this.audio.currentTime = this.audio.duration
  }

  pause() {
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
    this.name = "Non-playable asset"
    this.playable = false
  }

  play() {
    console.log("Called play() on non-playable asset")
    done()
  }
}

export class GeneratedStopset {
  constructor(stopset, rotatorsAndAssets, doneCallback, updateCallback, generatedId) {
    this.generatedId = generatedId === undefined ? currentGeneratedId++ : generatedId
    Object.assign(this, stopset)
    this.updateCallback = updateCallback || noop // UI update function
    this.doneCallback = doneCallback || noop
    this.items = rotatorsAndAssets.map(({ rotator, asset }, index) => {
      const args = [rotator, this, index]
      return asset ? new PlayableAsset(asset, ...args) : new NonPlayableAsset(...args)
    })
    this.current = 0
    this.loaded = false
    this.type = "stopset"
    this.playing = false
  }

  get duration() {
    return this.playableNonErrorItems.reduce((s, item) => s + item.duration, 0)
  }
  get elapsed() {
    return this.playableNonErrorItems.reduce((s, item) => s + item.elapsed, 0)
  }
  get remaining() {
    return this.playableNonErrorItems.reduce((s, item) => s + item.remaining, 0)
  }

  get playableNonErrorItems() {
    return this.items.filter((item) => item.playable && !item.error)
  }

  get playableItems() {
    return this.items.filter((item) => item.playable)
  }

  skip() {
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

  donePlaying(index) {
    this.current++
    this.updateCallback()
    if (this.current < this.items.length) {
      this.play()
    } else {
      this.done()
    }
    this.updateCallback()
  }

  done(skipCallback = false) {
    // Must be able to be called twice
    this.playing = false
    this.unloadAudio()
    if (!skipCallback) {
      console.log("calling done callback")
      this.doneCallback()
    }
  }

  play() {
    this.loadAudio()
    this.playing = true
    this.items[this.current].play()
    this.updateCallback()
  }

  pause() {
    this.items[this.current].pause()
    this.playing = false
    this.updateCallback()
  }
}

export class Wait {
  static currentWaitInterval = 1
  static currentStopsetOverdueTime = 0

  constructor(doneCallback, updateCallback) {
    this.generatedId = currentGeneratedId++
    this.updateCallback = updateCallback || noop
    this.doneCallback = doneCallback || noop
    this.duration = Wait.currentWaitInterval || 1 // Should never get created if it's 0
    this.name = "Wait"
    this.elapsed = 0
    this.type = "wait"
    this.overdue = false
    this.overtimeElapsed = 0
    this.overtime = false

    this.expires = null
    this.interval = null
    this.active = false
  }

  get remaining() {
    return this.duration - this.elapsed
  }

  get percentDone() {
    return Math.min((this.elapsed / this.duration) * 100, 100)
  }

  run() {
    this.active = true
    this.expires = dayjs().add(this.duration, "seconds")
    this.interval = setInterval(() => {
      const secondsLeft = this.expires.diff(dayjs(), "ms") / 1000
      this.elapsed = this.duration - secondsLeft
      if (secondsLeft < 0) {
        this.doneCountdown()
      }
      this.updateCallback()
    }, 50)
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

  done(skipCallback) {
    // Must be able to be called twice
    clearInterval(this.interval)
    if (!skipCallback) {
      this.doneCallback()
    }
  }
}

config.subscribe(($config) => {
  Wait.currentWaitInterval = $config.WAIT_INTERVAL || 1
  Wait.currentStopsetOverdueTime = $config.STOPSET_OVERDUE_TIME || 0
})

const setCompression = (value) => {
  if (value !== compressorEnabled) {
    if (value) {
      inputNode.disconnect(audioContext.destination)
      inputNode.connect(compressor)
    } else {
      inputNode.disconnect(compressor)
      inputNode.connect(audioContext.destination)
    }
    compressorEnabled = value
    console.log("Changed broadcast compression:", value)
  }
}

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

  console.log(`Set speaker to: ${choicePretty} (${choice})`)
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

config.subscribe(($config) => {
  setCompression($config.BROADCAST_COMPRESSION || false)
})
;(async () => {
  setCompression(get(config).BROADCAST_COMPRESSION || false)
  await updateSpeakers()
  setSpeaker(get(speaker))
})()
