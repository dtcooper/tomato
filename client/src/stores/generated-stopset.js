import dayjs from "dayjs"


class GeneratedStopsetAssetBase {
  constructor(rotator, generatedStopset, index) {
    this.rotator = rotator
    this.generatedStopset = generatedStopset
    this.index = index
    this.finished = false
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

  constructor({duration, ...asset}, ...args) {
    super(...args)
    // Assigns asset._db, which holds a reference to the underlying asset object
    // therefore a reference to the _original_ asset is held and it won't be garbage
    // collected and cleaned  up yet
    Object.assign(this, asset)
    this._duration = duration
    this.playable = true
    this.audio = null
  }

  get duration() {
    // Go based on real time if possible
    if (this.audio && !isNaN(this.audio.duration) && isFinite(this.audio.duration)) {
      return dayjs.duration(Math.ceil(this.audio.duration), "seconds")
    } else {
      return this._duration
    }
  }

  get currentTime() {
    if (this.finished) {
      return this.duration
    } else {
      return dayjs.duration(Math.round(this.audio ? this.audio.currentTime : 0), "seconds")
    }
  }

  getAudioObject() {
    const i = PlayableAsset._reusableAudioObjects.find(audio => audio._used)
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
    const audio = this.audio = this.getAudioObject()

    console.log(`Loading ${this.file.localUrl}`)
    audio.ondurationchange = audio.ontimeupdate = (event) => {
      this.generatedStopset.update()
    }
    audio.onended = audio.onerror = audio.onabort = audio.reject = () => this.done()
    audio.src = this.file.localUrl
  }

  play() {
    console.log(`Playing ${this.name}`)
    this.audio.play().catch(() => this.done())
  }

  toString() {
    return `${this.name} [${this.file.localUrl}]`
  }
}

class NonPlayableAsset extends GeneratedStopsetAssetBase{
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
  constructor(stopset, rotatorsAndAssets, update) {
    Object.assign(this, stopset)
    this.update = update || (() => {})  // UI update function (or no-op)
    this.items = rotatorsAndAssets.map(({ rotator, asset }, index) => {
      const args = [rotator, this, index]
      return asset ? new PlayableAsset(asset, ...args) : new NonPlayableAsset(...args)
    })
    this.current = 0
    this.loaded = false
  }

  loadAudio() {
    if (!this.loaded) {
      this.items.forEach(item => item.playable && item.loadAudio())
      this.loaded = true
    }
  }

  unloadAudio() {
    if (!this.loaded) {

      this.loaded = false
    }
  }

  donePlaying(index) {
    this.current++
    this.update()
    if (this.current < this.items.length) {
      this.play()
    } else {
      this.done()
    }
    this.update()
  }

  done() {
    this.items.filter(item => item.playable).forEach(this.item.audio._used = false)
  }

  play() {
    this.loadAudio()
    this.items[this.current].play()
    this.update()
  }

  pause() {
    this.items[this.current].pause()
    this.update()
  }
}
