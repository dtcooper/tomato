import md5File from 'md5-file'
import download from 'download'
import dayjs from 'dayjs'

import { derived, get, writable } from 'svelte/store'
import { writable as persistentWritable } from 'svelte-local-storage-store'

import { address, accessToken } from './connection'

const path = require('path')
const { promises: fs } = require('fs')

const appData = process.env.APPDATA || `${process.env.HOME}${process.platform === 'darwin' ? '/Library/Preferences' : '/.local/share'}`
const dataDir = path.join(appData, 'com.bmir.tomato/assets')

export const syncing = writable(false)
export const progress = writable(false)
const emptyStore = { assets: [], rotators: [], stopsets: [], config: [] }
const store = persistentWritable('store', emptyStore)
let rotatorsById = window.rotatorsById = {}

export const rotators = derived(store, $store => $store.rotators)
rotators.subscribe($rotators => {
  rotatorsById = ($rotators || []).reduce((obj, rotator) => {
    obj[rotator.id] = rotator
    return obj
  }, {})
})

const processAssetsAndStopsets = objs => objs.map(obj => ({
  ...obj,
  begin: obj.begin && dayjs(obj.begin),
  end: obj.end && dayjs(obj.end),
  rotators: obj.rotators.map(id => rotatorsById[id])
}))

export const assets = derived(store, $store => processAssetsAndStopsets($store.assets))
export const stopsets = derived(store, $store => processAssetsAndStopsets($store.stopsets))
export const config = derived(store, $store => $store.config)
export const darkMode = persistentWritable('darkMode', window.matchMedia('(prefers-color-scheme: dark)').matches)
darkMode.subscribe((value) => {
  document.documentElement.setAttribute('data-theme', value ? 'dark' : 'light')
})

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
    console.log(`Downloading ${path.basename(asset.file.filename)}`)
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

export const sync = async () => {
  let response, data

  if (get(syncing)) {
    return
  }

  syncing.set(true)

  try {
    response = await fetch(`${get(address)}sync/`, { headers: { 'X-Access-Token': get(accessToken) } })
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
    asset.file.url = `${get(address)}${url}`
    asset.file.filename = path.join(dataDir, asset.file.filename)
    asset.file.localUrl = `file://${asset.file.filename}`
    const shortname = path.basename(asset.file.filename)

    progress.set({ index: i + 1, total, percent: i / total * 100, filename: shortname })

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
  data.config.SINGLE_PLAY_ROTATORS = (data.config.SINGLE_PLAY_ROTATORS || []).map(rotatorId => rotatorsById[rotatorId])

  store.set(data)
  progress.set(false)
  syncing.set(false)
  console.log("Done sync'ing")
  return true
}

const isCurrentlyAiring = (obj, now = null) => {
  if (now === null) {
    now = dayjs()
  }
  return obj.enabled &&
    (obj.begin === null || obj.begin.isSame(now) || obj.begin.isBefore(now)) &&
    (obj.end === null || obj.end.isSame(now) || obj.end.isAfter(now))
}

const pickRandomItemByWeight = objects => {
  const totalWeight = objects.reduce((weight, obj) => weight + obj.weight, 0)
  const randomWeight = Math.random() * totalWeight
  let weight = 0
  for (const index in objects) {
    const object = objects[index]
    if (object.weight + weight > randomWeight) {
      return index
    }
    weight += object.weight
  }
}

export const generateStopset = () => {
  const now = dayjs()
  let eligibleAssets = get(assets).filter(asset => isCurrentlyAiring(asset, now))
  const eligibleStopsets = get(stopsets).filter(stopset => isCurrentlyAiring(stopset, now))

  while (eligibleStopsets.length > 0) {
    const stopset = eligibleStopsets.splice(pickRandomItemByWeight(eligibleStopsets), 1)[0]
    const generated = []
    for (const rotator of stopset.rotators) {
      const rotatorAssets = eligibleAssets.filter(a => a.rotators.findIndex(r => r.id === rotator.id) > -1)
      let asset = null
      if (rotatorAssets.length > 0) {
        asset = rotatorAssets[pickRandomItemByWeight(rotatorAssets)]
        eligibleAssets = eligibleAssets.filter(a => a.id !== asset.id)
      }
      generated.push([rotator, asset])
    }
    if (generated.length > 0) {
      return { stopset, assets: generated }
    }
  }

  return null
}
