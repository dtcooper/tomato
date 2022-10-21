import dayjs from 'dayjs'
import duration from 'dayjs/plugin/duration'

import App from './App.svelte'

dayjs.extend(duration)

export default new App({
  target: document.body
})
