import Alpine from 'alpinejs'
import persist from '@alpinejs/persist'

import { login, ping } from './js/login.js'

Alpine.plugin(persist)

window.Alpine = Alpine
window.ping = ping

document.addEventListener('alpine:init', () => {
  Alpine.store('globals', {
    connected: false,
    authenticated: false,
    username: '',
    address: '',
    accessToken: ''
  })

  Alpine.data('conn', function () {
    return {
      globals: Alpine.store('globals'),
      accessToken: Alpine.$persist('').as('accessToken'),
      address: Alpine.$persist('').as('address'),
      username: Alpine.$persist('').as('username'),
      error: false,
      authError: false,
      connecting: false,
      password: '',
      async init () {
        if (this.address && this.accessToken && this.username) {
          this.globals.connected = true
          this.globals.authenticated = false
          this.globals.username = this.username
          this.globals.address = this.address
          this.globals.accessToken = this.accessToken
          const pong = await ping(this.address, this.accessToken)
          if (pong.success) {
            console.log('Got pong from server')
            this.globals.authenticated = pong.access_token_value
          }
        }
      },
      async login () {
        let address

        this.connecting = true

        const error = (error, isAuth = false) => {
          if (isAuth) {
            this.authError = error
          } else {
            this.error = error
          }
          this.connecting = false
        }

        this.error = this.authError = false
        this.connecting = true

        try {
          address = new URL(this.address)
        } catch {
          error('Invalid Server Address')
          return
        }
        if (!['https:', 'http:'].includes(address.protocol)) {
          error('Server must being with http:// or https://')
          return
        }

        if (!address.pathname.endsWith('/')) {
          address.pathname += '/'
        }
        address = address.toString()

        const pong = await ping(address)
        if (!pong.success) {
          error(pong.error)
          return
        }

        const auth = await login(address, this.username, this.password)
        if (!auth.success) {
          error(auth.error, true)
          return
        }

        this.connecting = false
        console.log(auth)
      }
    }
  })
})

Alpine.start()
