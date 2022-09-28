import Alpine from 'alpinejs'
import { sync } from '../helpers/sync'

document.addEventListener('alpine:init', () => {
  Alpine.store('conn', {
    initialized: false,
    online: navigator.onLine,
    connected: Alpine.$persist(false).as('connected'),
    authenticated: false,
    username: Alpine.$persist('').as('username'),
    address: Alpine.$persist('').as('address'),
    accessToken: Alpine.$persist('').as('accessToken'),
    data: Alpine.$persist(null).as('data'),
    // TODO: store naked on localstorage, and throw an event when it's updated
    logout () {
      this.connected = this.authenticated = false
      this.password = this.accessToken = ''
    },
    async sync (callback = null) {
      if (!callback) {
        callback = (event) => {
          const { index, total, filename } = event
          console.log(`sync: ${index}/${total} - ${filename}`)
        }
      }
      const data = await sync(this.address, this.accessToken, callback)
      if (data) {
        this.data = data
        return true
      } else {
        console.error("Error sync'ing")
        return false
      }
    },
    hasAssets () {
      console.log('hasAssets() called: ', !!this.data.assets && this.data.assets.length > 0)
      return !!this.data.assets && this.data.assets.length > 0
    },
    assets () {
      console.log('assets() called', this.data.assets.length)
      return this.data.assets || []
    }
  })

  Alpine.effect(async () => {
    const conn = Alpine.store('conn')
    if (conn.online) {
      if (conn.connected) {
        if (conn.authenticated) {
          await conn.sync()
        }
      }
    }
  })

  window.addEventListener('offline', () => { Alpine.store('conn').online = false })
  window.addEventListener('online', () => { Alpine.store('conn').online = true })
})
