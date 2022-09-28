import process from 'process'
import path from 'path'
import { promises as fs } from 'fs'
import md5File from 'md5-file'
import download from 'download'

const appData = process.env.APPDATA || `${process.env.HOME}${process.platform === 'darwin' ? '/Library/Preferences' : '/.local/share'}`
const dataDir = path.join(appData, 'tomato-radio-automation')

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
    return await md5File(asset.file.filename) === asset.md5sum
  } catch {
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

  for (const [id, asset] of Object.entries(data.assets)) {
    let url = asset.file.url
    if (url.startsWith('/')) {
      url = url.substr(1)
    }
    asset.file.url = `${address}${url}`
    asset.file.filename = path.join(dataDir, asset.file.filename)
    asset.localUrl = `file://${asset.file.filename}`
    const shortname = path.basename(asset.file.filename)

    if (!await fileExists(asset) || !await isMd5Correct(asset)) {
      if (await downloadAsset(asset)) {
        if (!await isMd5Correct(asset)) {
          console.error(`Bad sum for ${shortname}`)
          delete data.assets[id]
        }
      } else {
        console.error(`Error downloading ${shortname}`)
        delete data.assets[id]
      }
    }

    asset.file = `file://${asset.file.filename}`
  }

  return data
}

export { sync }
