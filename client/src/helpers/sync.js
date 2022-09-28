import process from 'process'
import path from 'path'
import { promises as fs } from 'fs'
import md5File from 'md5-file'
import download from 'download'

const appData = process.env.APPDATA || `${process.env.HOME}${process.platform === 'darwin' ? '/Library/Preferences' : '/.local/share'}`
const dataDir = path.join(appData, 'com.bmir.tomato')

const fileExists = async (asset) => {
  try {
    await fs.access(asset.file.filename)
    return true
  } catch {
    return false
  }
}

const downloadAsset = async (asset) => {
  try {
    return await download(
      asset.file.url,
      path.dirname(asset.file.filename),
      { filename: path.basename(asset.file.filename) }
    )
  } catch (error) {
    console.error(error)
    return false
  }
}

const isMd5Correct = async (asset) => {
  try {
    const sum = await md5File(asset.file.filename)
    if (sum !== asset.md5sum) {
      console.error(`Bad md5sum for ${path.basename(asset.file.filename)}`)
      return false
    } else {
      return true
    }
  } catch {
    console.warn(`Error computing md5sum for ${asset.file.filename}`)
    return false
  }
}

// TODO should there be a way to abort?
const sync = async (address, accessToken, progressCallback = null) => {
  let response, data

  try {
    response = await fetch(`${address}sync/`, { headers: { 'X-Access-Token': accessToken } })
    data = await response.json()
  } catch (error) {
    console.error(error)
    return false
  }

  const total = data.assets.length
  const badAssets = new Set()

  // TODO: assets is a list now, so needs to be deleted
  for (let i = 0; i < total; i++) {
    const asset = data.assets[i]
    let url = asset.file.url
    if (url.startsWith('/')) {
      url = url.substr(1)
    }
    asset.file.url = `${address}${url}`
    asset.file.filename = path.join(dataDir, asset.file.filename)
    asset.file.localUrl = `file://${asset.file.filename}`
    const shortname = path.basename(asset.file.filename)

    if (progressCallback) {
      progressCallback({ index: i + 1, total, percent: i / total * 100, filename: shortname })
    }

    if (!await fileExists(asset) || !await isMd5Correct(asset)) {
      if (await downloadAsset(asset)) {
        if (!await isMd5Correct(asset)) {
          console.error(`Bad sum for ${shortname}`)
          badAssets.add(i)
        }
      } else {
        console.error(`Error downloading ${shortname}`)
        badAssets.add(i)
      }
    }
  }

  data.assets = data.assets.filter((_, i) => !badAssets.has(i))
  return data
}

export { sync }
