import dayjs from "dayjs"
import duration from "dayjs/plugin/duration"
import isSameOrAfter from "dayjs/plugin/isSameOrAfter"
import isSameOrBefore from "dayjs/plugin/isSameOrBefore"
import download from "download"
import md5File from "md5-file"
import { WeakRefSet } from "weak-ref-collections"

import { get, writable } from "svelte/store"

import { config } from "./config"
import { auth, ready } from "./connection"

const path = require("path")
const fs = require("fs/promises")

dayjs.extend(duration)
dayjs.extend(isSameOrAfter)
dayjs.extend(isSameOrBefore)

const assetsDir = path.join(new URLSearchParams(window.location.search).get("userDataDir"), "assets")

const syncInfo = writable({
  syncing: false,
  total: -1,
  current: -1,
  percent: 0,
  assetName: ""
})

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
    this._data = data
    this._db = db
    Object.assign(this, this._data)
  }

  toString() {
    console.log(this.name)
  }
}

class AssetStopsetHydratableObject extends HydratableObject {
  constructor({ rotators, ...data }, db) {
    super(data, db)
    this._rotators = rotators
    this.begin = this.begin && dayjs(this.begin)
    this.end = this.end && dayjs(this.end)
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
      path: filePath,
      basename,
      size: file.size,
      md5sum: file.md5sum,
      dirname,
      tmpPath,
      tmpBasename: path.basename(tmpPath)
    }
    this.duration = dayjs.duration(this.duration, "seconds")
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
        await download(url, dirname, { filename: tmpBasename })
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
  constructor(data, db) {
    super(data, db)
    this.assets = db.assets.filter((a) => a._rotators.includes(this.id))
  }

  getAsset(softIgnoreIds = new Set(), hardIgnoreIds = new Set()) {
    const activeAssets = filterItemsByActive(this.assets)
    const hardIgnoredAssets = activeAssets.filter((a) => !hardIgnoreIds.has(a.id))
    const softIgnoredAssets = hardIgnoredAssets.filter((a) => !softIgnoreIds.has(a.id))

    const tries = [softIgnoredAssets, hardIgnoredAssets]
    if (get(config).ALLOW_DUPLICATES_IN_STOPSET) {
      tries.push(activeAssets)
    }

    let asset = pickRandomItemByWeight(softIgnoredAssets)
    if (!asset) {
      console.log(`Failed to get an asset form soft ignores [rotator = ${this.name}]`)
      asset = pickRandomItemByWeight(hardIgnoredAssets)
      if (!asset) {
        console.log(`Failed to pick an asset from hard ignores [rotator = ${this.name}]`)
        if (get(config).ALLOW_DUPLICATES_IN_STOPSET) {
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

class Stopset extends AssetStopsetHydratableObject {}

class DB {
  static _nonGarbageCollectedAssets = new WeakRefSet()
  static _playTimes = new Map()

  constructor({ assets, rotators, stopsets } = { assets: [], rotators: [], stopsets: [] }) {
    this.assets = assets.map((data) => new Asset(data, this))
    this.assets.forEach(this.constructor._nonGarbageCollectedAssets.add, this.constructor._nonGarbageCollectedAssets)
    this.rotators = new RotatorsMap(rotators, this)
    this.stopsets = stopsets.map((data) => new Stopset(data, this))
    this._host = null
  }

  get host() {
    if (!this._host) {
      const url = new URL(get(auth).host)
      url.protocol = url.protocol.replace(/^ws/i, "http")
      url.pathname = ""
      this._host = url.toString().slice(0, -1) // remove trailing slash
    }
    return this._host
  }

  static _savePlayTimes() {
    window.localStorage.setItem("soft-ignored", JSON.stringify(Array.from(this._playTimes.entries()), null, ""))
  }

  static _loadPlayTimes() {
    try {
      this._playTimes = new Map(JSON.parse(window.localStorage.getItem("soft-ignored")))
    } catch {}
  }

  static markPlayed(asset) {
    if (parseInt(get(config).NO_REPEAT_ASSETS_TIME) > 0) {
      // XXX no parseInt
      this._playTimes.set(asset.id, timestamp())
      this._savePlayTimes()
    }
  }

  static async cleanup() {
    if (get(ready)) {
      // For all non-garbage collected assets, get set of used files
      const usedFiles = new Set(Array.from(this._nonGarbageCollectedAssets.values()).map((a) => a.file.basename))
      let deleted = 0

      // Go through all files in assetsDir and make sure their used
      const foundFiles = await lsDir(assetsDir)
      for (const filePath of foundFiles) {
        if (!usedFiles.has(path.basename(filePath))) {
          await fs.unlink(filePath)
          deleted++
        }
      }
      console.log(`Cleaned up ${deleted} files.`)
    } else {
      console.log("Skipping cleanup due to ready=false")
    }
  }

  generateStopset() {
    const stopset = pickRandomItemByWeight(filterItemsByActive(this.stopsets))
    const hardIgnoreIds = new Set()
    let softIgnoreIds = undefined

    const NO_REPEAT_ASSETS_TIME = parseInt(get(config).NO_REPEAT_ASSETS_TIME) // XXXX no parseint
    if (NO_REPEAT_ASSETS_TIME > 0) {
      // Purge _playTimes if their outside time bounds
      DB._playTimes = new Map(
        Array.from(DB._playTimes.entries()).filter(([, ts]) => ts + NO_REPEAT_ASSETS_TIME >= timestamp())
      )
      DB._savePlayTimes()
      softIgnoreIds = new Set(DB._playTimes.keys())
    }

    const assets = []
    if (stopset) {
      console.log(stopset.rotators)
      for (const rotator of stopset.rotators) {
        const asset = rotator.getAsset(softIgnoreIds, hardIgnoreIds)
        if (asset) {
          hardIgnoreIds.add(asset.id)
          DB.markPlayed(asset)
        }
        assets.push({ rotator, asset })
      }
    }

    return { stopset, assets }
  }
}

DB._loadPlayTimes()
const emptyDB = new DB()
let db = emptyDB
window.DB = DB

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

export const syncData = runOnceAndQueueLastCall(async (jsonData) => {
  const replacementDB = new DB(jsonData)

  const downloadedAssetsIds = new Set()
  const total = replacementDB.assets.length
  console.log(`Sync'ing ${total} assets`)

  for (const [current, asset] of replacementDB.assets.entries()) {
    syncInfo.set({ syncing: true, total, current, percent: (current / total) * 100, assetName: asset.name })
    if (await asset.download()) {
      downloadedAssetsIds.add(asset.id)
    }
  }

  console.log(`Sync'd ${downloadedAssetsIds.size} of ${total} assets successfully`)

  // filter down DB *and* jsonData (since that's what we put in localStorage)
  for (let data of [jsonData, replacementDB]) {
    data.assets = data.assets.filter((asset) => downloadedAssetsIds.has(asset.id))
  }
  window.localStorage.setItem("last-db-data", JSON.stringify(jsonData, null, ""))
  db = window.db = replacementDB // Swap out DB
})

export const clearData = () => {
  db = emptyDB
  window.localStorage.removeItem("last-db-data")
}

export const restoreDBFromLocalStorage = () => {
  try {
    const state = JSON.parse(window.localStorage.getItem("last-db-data"))
    if (state) {
      db = window.db = new DB(state)
      return
    }
  } catch (e) {
    console.error(e)
  }

  db = window.db = emptyDB
}

setInterval(() => DB.cleanup(), 45 * 60 * 60) // Clean up every 45 minutes
