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
    data: Alpine.$persist({ assets: [], stopsets: [], rotators: {} }).as('data'),
    logout () {
      this.connected = this.authenticated = false
      this.password = this.accessToken = ''
    },
    async sync () {
      const data = await sync(this.address, this.accessToken)
      if (data) {
        for (const [key, value] of Object.entries(data)) {
          if (key in this.data) {
            this.data[key] = value
          }
        }
      } else {
        console.error("Error sync'ing")
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
