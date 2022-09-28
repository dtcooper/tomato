import Alpine from 'alpinejs'
import { login, ping } from '../helpers/login'

document.addEventListener('alpine:init', () => {
  Alpine.data('login', function () {
    return {
      connStore: Alpine.store('conn'),
      error: false,
      authError: false,
      connecting: false,
      password: '',
      async init () {
        if (this.connStore.connected) {
          this.connStore.authenticated = false
          const pong = await ping(this.connStore.address, this.connStore.accessToken)
          if (pong.success) {
            this.connStore.authenticated = pong.access_token_valid
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
          address = new URL(this.connStore.address)
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
        this.connStore.address = address = address.toString()

        const pong = await ping(address)
        if (!pong.success) {
          error(pong.error)
          return
        }

        const auth = await login(address, this.connStore.username, this.password)
        if (!auth.success) {
          error(auth.error, true)
          return
        }

        this.password = ''
        this.connStore.accessToken = auth.access_token
        this.connStore.connected = true
        this.connStore.authenticated = true
        this.connecting = false
      }
    }
  })
})
