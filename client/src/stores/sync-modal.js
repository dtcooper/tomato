import { get, writable } from "svelte/store"

import { config } from "./config"


export const syncModalStore = writable({
  title: "",
  show: false,
  canDismiss: true,
})

export const showSyncModal = window.showSyncModal = (title, canDismiss = true) => {
  if (!title) {
    title = `Sync'ing with ${get(config).STATION_NAME}...`
  }

  syncModalStore.set({ title, show: true, canDismiss })
}

export const closeSyncModal = () => {
  syncModalStore.update($syncModalStore => ({...$syncModalStore, show: false}))
}
