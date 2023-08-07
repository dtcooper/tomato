import { noop } from "svelte/internal"

class GeneratedStopsetAssetBase {
  constructor(rotator, generatedStopset, index) {
    this.rotator = rotator
    this.generatedStopset = generatedStopset
    this.index = index
    this.error = false
  }

  done(error) {
    this.finished = true
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
    this.elapsed = this.elapsedFull = 0
    this.playable = true
    this.audio = null
    this.durationFull = this.duration
  }

  getAudioObject() {
    const i = PlayableAsset._reusableAudioObjects.find((audio) => audio._used)
    let audio
    if (i > -1) {
      audio = PlayableAsset._reusableAudioObjects[i]
    } else {
      audio = new Audio()
      PlayableAsset._reusableAudioObjects.push(audio)
    }
    audio._used = true

    if (PlayableAsset._reusableAudioObjects.length > 50) {
      console.warn("Length of PlayableAsset._reusuableAudioObjects exceeds > 50, something may be very wrong.")
    }

    return audio
  }

  loadAudio() {
    this.audio = this.getAudioObject()

    console.log(`Loading ${this.file.localUrl}`)
    this.audio.ondurationchange = () => {
      this.durationFull = this.audio.duration
      this.duration = Math.ceil(this.audio.duration)
      this.generatedStopset.updateCallback()
    }
    this.audio.ontimeupdate = () => {
      this.elapsedFull = this.audio.currentTime
      this.elapsed = Math.round(this.audio.currentTime)
      this.generatedStopset.updateCallback()
    }
    this.audio.onended = () => this.done()
    this.audio.onerror = this.audio.onabort = () => {
      this.error = true
      this.done()
    }
    this.audio.src = this.file.localUrl
  }

  unloadAudio() {
    this.audio._used = false
  }

  get remaining() {
    return this.duration - this.elapsed
  }

  play() {
    console.log(`Playing ${this.name}`)
    this.audio.play().catch(() => this.done())
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
    done()
  }
}

export class GeneratedStopset {
  constructor(stopset, rotatorsAndAssets, doneCallback, updateCallback) {
    Object.assign(this, stopset)
    this.updateCallback = updateCallback || noop // UI update function
    this.doneCallback = doneCallback || noop
    this.items = rotatorsAndAssets.map(({ rotator, asset }, index) => {
      const args = [rotator, this, index]
      return asset ? new PlayableAsset(asset, ...args) : new NonPlayableAsset(...args)
    })
    this.current = 0
    this.loaded = false
  }

  get durationFull() {
    return this.playableNonErrorItems.reduce((s, item) => s + item.durationFull, 0)
  }
  get elapsedFull() {
    return this.playableNonErrorItems.reduce((s, item) => s + item.elapsedFull, 0)
  }
  get duration() {
    return this.playableNonErrorItems.reduce((s, item) => s + item.duration, 0)
  }
  get elapsed() {
    return this.playableNonErrorItems.reduce((s, item) => s + item.elapsed, 0)
  }
  get remaining() {
    return this.duration - this.elapsed
  }

  //TODO: may want to change this to playableNonErrorItems
  get playableNonErrorItems() {
    return this.items.filter((item) => item.playable && !item.error)
  }

  get playableItems() {
    return this.items.filter((item) => item.playable)
  }

  loadAudio() {
    if (!this.loaded) {
      this.items.filter((item) => item.playable)
      this.playableNonErrorItems.forEach((item) => item.loadAudio())
      this.loaded = true
    }
  }

  unloadAudio() {
    if (!this.loaded) {
      this.loaded = false
      this.items.filter((item) => item.playable).forEach((item) => item.unloadAudio())
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

  done() {
    this.unloadAudio()
    this.doneCallback()
  }

  play() {
    this.loadAudio()
    this.items[this.current].play()
    this.updateCallback()
  }

  pause() {
    this.items[this.current].pause()
    this.updateCallback()
  }
}
