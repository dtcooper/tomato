class GeneratedStopsetItem {
    constructor(asset, rotator) {
      this._asset = asset // Need to keep a reference to this to avoid garbage collection and file deletion
      this.rotator = chosenRotator
      Object.assign(this, asset)
      this.loadAudio()
    }

    loadAudio() {
      console.log(`Would load ${this.file.localUrl} for asset ${this.name}`)
    }
  }
