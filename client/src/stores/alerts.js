import { readonly, writable } from "svelte/store"

const alertLevels = ["info", "success", "warning", "error"]

const data = writable([])
export const alerts = readonly(data)
export const dismiss = (index) =>
  data.update(($alerts) => {
    $alerts.splice(index, 1)
    return $alerts
  })

export const alert = (msg, level = "info", timeout = null) => {
  if (!alertLevels.includes(level)) {
    console.warn(`Invalid alert level: ${level}`)
    level = "info"
  }
  const expires = timeout !== null ? window.performance.now() + timeout : null
  data.update(($alerts) => [{ msg, level, expires }, ...$alerts])
}

setInterval(() => {
  const now = window.performance.now()
  data.update(($alerts) => $alerts.filter(({ expires }) => expires === null || expires > now))
}, 50)
