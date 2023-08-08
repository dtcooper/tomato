import dayjs from "dayjs"
import download from "download"
import fs from "fs/promises"
import md5File from "md5-file"
import path from "path"
import { pathToFileURL } from "url"
import { WeakRefSet } from "weak-ref-collections"

import { get, readonly, writable } from "svelte/store"

import { colors } from "../../../server/constants.json"
import { config } from "./config"
import { conn } from "./connection"
import { GeneratedStopset } from "./player"

const assetsDir = path.join(new URLSearchParams(window.location.search).get("userDataDir"), "assets")

const emptySyncProgress = { syncing: false, total: -1, index: -1, percent: 0, item: "" }
const syncProgress = writable(emptySyncProgress)
const syncProgressReadonly = readonly(syncProgress)
export { syncProgressReadonly as syncProgress }

const timestamp = () => Math.floor(Date.now() / 1000)

const fileExists = async (filename) => {
  try {
    await fs.access(filename)
    return true
  } catch {
    return false
  }
}

const fileSize = async (filename) => {
  const { size } = await fs.stat(filename)
  return size
}

const lsDir = async (dir, _results = []) => {
  const files = await fs.readdir(dir)
  for (const f of files) {
    const filePath = path.join(dir, f)
    const stat = await fs.stat(filePath)
    if (stat.isDirectory()) {
      await lsDir(filePath, _results)
    } else {
      _results.push(filePath)
    }
  }
  return _results
}

class HydratableObject {
  constructor(data, db) {
    this._db = db
    Object.assign(this, data)
  }

  toString() {
    console.log(this.name)
  }
}

class AssetStopsetHydratableObject extends HydratableObject {
  constructor({ begin, end, rotators, ...data }, db) {
    super(data, db)
    this._rotators = rotators
    this.begin = begin && dayjs(begin)
    this.end = end && dayjs(end)
  }
  get rotators() {
    return this._rotators.map((id) => this._db.rotators.get(id))
  }
}

class Asset extends AssetStopsetHydratableObject {
  constructor({ file, ...data }, db) {
    super(data, db)
    const filePath = path.join(assetsDir, file.filename)
    const dirname = path.dirname(filePath)
    const basename = path.basename(filePath)
    const tmpPath = path.join(dirname, `${basename}.tmp`)
    this.file = {
      url: `${db.host}${file.url}`,
      localUrl: pathToFileURL(filePath),
      path: filePath,
      basename,
      size: file.size,
      md5sum: file.md5sum,
      dirname,
      tmpPath,
      tmpBasename: path.basename(tmpPath)
    }
    // TODO: override weight via END_DATE_PRIORITY_WEIGHT_MULTIPLIER
  }

  async download() {
    const { url, path, size, md5sum, dirname, tmpPath, tmpBasename } = this.file

    try {
      let exists = await fileExists(path)

      if (exists) {
        // If it exists, just verify sizes match (md5sum was already checked)
        if ((await fileSize(path)) !== size) {
          console.error(`File size mismatch for ${this.name}. Deleting and trying again.`)
          await fs.unlink(path)
          exists = false
        }
      }
      if (!exists) {
        console.log(`Downloading: ${url}`)
        // Accept any certificate during local development (ie, self-signed ones)
        await download(url, dirname, { filename: tmpBasename, rejectUnauthorized: !IS_DEV })
        const actualMd5sum = await md5File(tmpPath)
        if (actualMd5sum !== md5sum) {
          throw new Error(`MD5 sum mismatch. Actual=${actualMd5sum} Expected=${md5sum}`)
        }
        fs.rename(tmpPath, path)
      }
      return true
    } catch (e) {
      try {
        if (await fileExists(tmpPath)) {
          await fs.unlink(tmpPath)
        }
      } catch (e) {
        console.error(`Error cleaning up ${tmpPath}\n`, e)
      }
      console.error(`Error downloading asset ${this.name} @ ${url}\n`, e)
      return false
    }
  }
}

const pickRandomItemByWeight = (objects) => {
  const totalWeight = objects.reduce((weight, obj) => weight + obj.weight, 0)
  const randomWeight = Math.random() * totalWeight
  let weight = 0
  for (const index in objects) {
    const object = objects[index]
    if (object.weight + weight > randomWeight) {
      return object
    }
    weight += object.weight
  }
  return null
}

const filterItemsByActive = (obj, dt = null) => {
  if (!dt) {
    dt = dayjs()
  }

  return obj.filter((o) => o.enabled && (!o.begin || o.begin.isSameOrBefore(dt)) && (!o.end || o.end.isSameOrAfter(dt)))
}

class Rotator extends HydratableObject {
  constructor({ color, ...data }, db) {
    super(data, db)
    this.assets = db.assets.filter((a) => a._rotators.includes(this.id))
    this.color = colors.find((c) => c.name === color)
  }

  getAsset(softIgnoreIds = new Set(), hardIgnoreIds = new Set(), startTime) {
    const activeAssets = filterItemsByActive(this.assets, startTime)
    const hardIgnoredAssets = activeAssets.filter((a) => !hardIgnoreIds.has(a.id))
    const softIgnoredAssets = hardIgnoredAssets.filter((a) => !softIgnoreIds.has(a.id))

    const tries = [softIgnoredAssets, hardIgnoredAssets]
    if (get(config).ALLOW_REPEATS_IN_STOPSET) {
      tries.push(activeAssets)
    }

    let asset = pickRandomItemByWeight(softIgnoredAssets)
    if (!asset) {
      console.log(`Failed to get an asset form soft ignores [rotator = ${this.name}]`)
      asset = pickRandomItemByWeight(hardIgnoredAssets)
      if (!asset) {
        console.log(`Failed to pick an asset from hard ignores [rotator = ${this.name}]`)
        if (get(config).ALLOW_REPEATS_IN_STOPSET) {
          asset = pickRandomItemByWeight(activeAssets)
        }
      }
    }

    if (asset) {
      console.log(`Picked asset ${asset.id} [rotator = ${this.name}]`)
    } else {
      console.log(`Failed to pick an asset entirely! [rotator = ${this.name}]`)
    }

    return asset
  }
}

class RotatorsMap extends Map {
  constructor(data, db) {
    super(data.map((rotator) => [rotator.id, new Rotator(rotator, db)]))
  }
}

class Stopset extends AssetStopsetHydratableObject {
  generate(startTime, doneCallback, updateCallback) {
    const hardIgnoreIds = new Set()
    let softIgnoreIds = undefined

    const NO_REPEAT_ASSETS_TIME = get(config).NO_REPEAT_ASSETS_TIME
    if (NO_REPEAT_ASSETS_TIME > 0) {
      // Purge _assetPlayTimes if their outside time bounds
      DB._assetPlayTimes = new Map(
        Array.from(DB._assetPlayTimes.entries()).filter(([, ts]) => ts + NO_REPEAT_ASSETS_TIME >= timestamp())
      )
      DB._saveAssetPlayTimes()
      softIgnoreIds = new Set(DB._assetPlayTimes.keys())
    }

    const items = []
    for (const rotator of this.rotators) {
      const asset = rotator.getAsset(softIgnoreIds, hardIgnoreIds, startTime)
      if (asset) {
        hardIgnoreIds.add(asset.id)
        /// XXX should this be marked by player code only?
        /// Except then the next stopset may include it, so maybe this _is_ the spot for marking
        DB.markPlayed(asset)
      }
      items.push({ rotator, asset })
    }

    return new GeneratedStopset(this, items, doneCallback, updateCallback)
  }
}

class DB {
  static _nonGarbageCollectedAssets = new WeakRefSet()
  static _filesToCleanup = new Set()
  static _assetPlayTimes = new Map()

  constructor({ assets, rotators, stopsets } = { assets: [], rotators: [], stopsets: [] }) {
    this.assets = assets.map((data) => new Asset(data, this))
    this.assets.forEach(this.constructor._nonGarbageCollectedAssets.add, this.constructor._nonGarbageCollectedAssets)
    this.rotators = new RotatorsMap(rotators, this)
    this.stopsets = stopsets.map((data) => new Stopset(data, this))
    this.lastSync = null
    this._host = null
  }

  get host() {
    if (!this._host) {
      const url = new URL(get(conn).host)
      url.protocol = url.protocol.replace(/^ws/i, "http")
      url.pathname = ""
      this._host = url.toString().slice(0, -1) // remove trailing slash
    }
    return this._host
  }

  static _saveAssetPlayTimes() {
    window.localStorage.setItem(
      "soft-ignored-ids",
      JSON.stringify(Array.from(this._assetPlayTimes.entries()), null, "")
    )
  }

  static _loadAssetPlayTimes() {
    try {
      this._assetPlayTimes = new Map(JSON.parse(window.localStorage.getItem("soft-ignored-ids")))
    } catch {}
  }

  static markPlayed(asset) {
    if (get(config).NO_REPEAT_ASSETS_TIME > 0) {
      this._assetPlayTimes.set(asset.id, timestamp())
      this._saveAssetPlayTimes()
    }
  }

  static async cleanup() {
    if (get(conn).ready) {
      // For all non-garbage collected assets, get set of used files
      const usedFiles = new Set(Array.from(this._nonGarbageCollectedAssets.values()).map((a) => a.file.basename))
      let deleted = 0
      const newFilesToCleanup = new Set()

      // Go through all files in assetsDir and make sure they'e used
      const foundFiles = await lsDir(assetsDir)
      for (const filePath of foundFiles) {
        if (!usedFiles.has(path.basename(filePath))) {
          // Wait until _next_ cleanup to delete the files (just to be on the safe side)
          if (this._filesToCleanup.has(filePath)) {
            await fs.unlink(filePath)
            deleted++
            this._filesToCleanup.delete(filePath)
          } else {
            newFilesToCleanup.add(filePath)
          }
        }
      }
      this._filesToCleanup = newFilesToCleanup
      console.log(`Cleaned up ${deleted} files. ${this._filesToCleanup.size} pending deletion.`)
    } else {
      console.log("Skipping cleanup due to ready=false")
    }
  }

  generateStopset(startTime, doneCallback, updateCallback) {
    const stopset = pickRandomItemByWeight(filterItemsByActive(this.stopsets, startTime))
    if (stopset) {
      return stopset.generate(startTime, doneCallback, updateCallback)
    }
    return null
  }
}

DB._loadAssetPlayTimes()
const emptyDB = new DB()
window.DB = DB
const dbStore = writable(emptyDB)
let db = emptyDB
const dbReadonly = readonly(dbStore)
export { dbReadonly as db }

const runOnceAndQueueLastCall = (func) => {
  let running = false
  let pendingCall = null

  return async (...args) => {
    if (running) {
      pendingCall = args
    } else {
      running = true
      await func(...args)
      running = false
      if (pendingCall) {
        const args = pendingCall
        pendingCall = null
        await func(...args)
      }
    }
  }
}

export const syncAssetsDB = runOnceAndQueueLastCall(async (jsonData) => {
  const replacementDB = new DB(jsonData)

  const downloadedAssetsIds = new Set()
  const total = replacementDB.assets.length
  console.log(`Sync'ing ${total} assets`)

  for (const [current, asset] of replacementDB.assets.entries()) {
    syncProgress.set({ syncing: true, total, current, percent: (current / total) * 100, item: asset.name })
    if (await asset.download()) {
      downloadedAssetsIds.add(asset.id)
    }
  }
  syncProgress.set({ syncing: true, total, current: total, percent: 100, item: "Finalizaing..." })

  console.log(`Sync'd ${downloadedAssetsIds.size} of ${total} assets successfully`)
  replacementDB.lastSync = dayjs()

  // filter down DB *and* jsonData (since that's what we put in localStorage)
  for (let data of [jsonData, replacementDB]) {
    data.assets = data.assets.filter((asset) => downloadedAssetsIds.has(asset.id))
  }
  window.localStorage.setItem("last-db-data", JSON.stringify(jsonData, null, ""))
  window.db = replacementDB // Swap out DB
  dbStore.set(replacementDB)
  db = replacementDB
  syncProgress.set(emptySyncProgress)
})

export const clearAssetsDB = () => {
  window.db = emptyDB
  dbStore.set(emptyDB)
  db = emptyDB
  window.localStorage.removeItem("last-db-data")
}

export const restoreAssetsDBFromLocalStorage = () => {
  try {
    const state = JSON.parse(window.localStorage.getItem("last-db-data"))
    if (state) {
      const loadedDb = (window.db = new DB(state))
      dbStore.set(loadedDb)
      db = loadedDb
      return
    }
  } catch (e) {
    console.error(e)
  }

  window.db = emptyDB
  dbStore.set(emptyDB)
  db = emptyDB
}

export const clearSoftIgnoredAssets = () => window.localStorage.removeItem("soft-ignored-ids")

setInterval(() => DB.cleanup(), 45 * 60 * 60) // Clean up every 45 minutes
