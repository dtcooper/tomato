export class GeneratedStopset {
  constructor(name, assets) {
    this.name = name
    console.log(assets)

    this.assets = assets.map(({ rotator, asset }) => {
      let audio = null
      if (asset) {
        audio = new Audio()
        audio._asset = asset
        audio.src = asset.file.localUrl
        audio.preload = "auto"
        audio.load()
      }
      return { rotator, asset, audio }
    })
  }
}
