import Alpine from 'alpinejs'
import persist from '@alpinejs/persist'

import './store/conn'
import './components/login'
import './streamdeck'

Alpine.plugin(persist)
window.Alpine = Alpine
Alpine.start()
