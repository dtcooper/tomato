import dayjs from "dayjs"
import duration from "dayjs/plugin/duration"

import { get } from "svelte/store"

import { config } from "./config"

dayjs.extend(duration)

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
  constructor({ rotators, ...data}, db) {
    super(data, db)
    this._rotators = rotators
    this.begin = this.begin && dayjs(this.begin)
    this.end = this.end && dayjs(this.end)
  }
  get rotators() {
    return this._rotators.map(id => this.db.rotators.get(id))
  }
}

class Asset extends AssetStopsetHydratableObject {
  constructor(data, db) {
    super(data, db)
    this.duration = dayjs.duration(this.duration, "seconds")
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

class Rotator extends HydratableObject {
  constructor(data, db) {
    super(data, db)
    this.assets = db.assets.filter(a => a._rotators.includes(this.id))
  }

  getAsset(softIgnoreIds = [], hardIgnoreIds = []) {
    let hardIgnoredAssets = this.assets.filter(a => !hardIgnoreIds.includes(a.id))
    let softIgnoredAssets = hardIgnoredAssets.filter(a => !softIgnoreIds.includes(a.id))

    const tries = [softIgnoredAssets, hardIgnoredAssets]
    if (get(config).ALLOW_DUPLICATES_IN_STOPSET) {
      tries.push(this.assets)
    }

    for (const assetsTry of tries) {
      const asset = pickRandomItemByWeight(assetsTry)
      if (asset) {
        return asset
      }
    }

    return null
  }
}

class RotatorsMap extends Map {
  constructor(data, db) {
    super(data.map((rotator) => [rotator.id, new Rotator(rotator, db)]))
  }
}

class Stopset extends AssetStopsetHydratableObject {
}

class DB {
  constructor({assets, rotators, stopsets} = {assets: [], rotators: [], stopsets: []}) {
    this.assets = assets.map(data => new Asset(data, this))
    this.rotators = new RotatorsMap(rotators, this)
    this.stopsets = stopsets.map(data => new Stopset(data, this))
  }
}

const emptyDB = new DB()
let db = emptyDB

export const syncData = async (jsonData) => {
  window.localStorage.setItem("last-db-data", JSON.stringify(jsonData, null, ''))
  const replacementDB = window.db = new DB(jsonData)
}

export const clearData = () => {
  db = emptyDB
  window.localStorage.removeItem("last-db-data")
}

export const restoreDBFromLocalStorage = () => {
  db = window.db = emptyDB
  try {
    const state = JSON.parse(window.localStorage.getItem("last-db-data"))
    if (state) {
      db = window.db = new DB(state)
    }
  } catch (e) {
    console.error(e)
  }
}
