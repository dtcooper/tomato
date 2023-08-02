class PlayableAsset {
  static _reusableAudioObjects = new Map()

  constructor(asset, rotator, index) {
    // Assigns asset._db, which holds a reference to the underlying asset object
    // therefore a reference to the _original_ asset is held and it won't be garbage
    // collected and cleaned  up yet
    Object.assign(this, asset)
    this.rotator = rotator
    this.playable = true
    this.playing = false
    this.index = index
  }

  loadAudio() {
    this.audio = PlayableAsset._reusableAudioObjects.get(this.index)
    if (!this.audio) {
      this.audio = new Audio()
      PlayableAsset._reusableAudioObjects.set(this.index, this.audio)
    }

    this.audio.onerror = this.audio.onabort = (e) => {
      console.error(`An error occured while loading ${this.name}`, e)
      this.playable = false
    }

    this.audio.src = this.file.localUrl
    console.log(`Loading ${this.file.localUrl}`)
  }

  play() {
    return new Promise(async (resolve, reject) => {
      console.log(`Playing ${this.name}`)
      this.audio.play().catch(reject)
      this.audio.onended = resolve
      this.audio.onerror = this.audio.onabort = reject
      this.audio.onpause
    })
  }

  toString() {
    return `${this.name} [${this.file.localUrl}]`
  }
}

class NonPlayableAsset {
  constructor(rotator, index) {
    this.playable = false
    this.rotator = rotator
    this.index = index
  }
}

export class GeneratedStopset {
  constructor(name, items) {
    this.name = name
    this.items = items.map(({ rotator, asset }, index) => {
      return asset ? new PlayableAsset(asset, rotator, index) : new NonPlayableAsset(rotator, index)
    })
    this.loaded = false
  }

  loadAudio() {
    this.items.forEach(item => item.playable && item.loadAudio())
    this.loaded = true
  }

  async play() {
    if (!this.loaded) {
      this.loadAudio()
    }

    // Keep track of playing index, so it can be skipped elsewhere
    for (const item of this.items) {
      if (item.playable) {
        try {
          await item.play()
        } catch (e) {
          console.error(`Failed to play ${item.name}`, e)
        }
      } else {
        console.error(`Skipped rotator ${item.rotator.name}`)
      }
    }
  }

  pause() {

  }

  stop() {
    this.items.forEach(item => item.playable && item.audio.pause())
  }
}
