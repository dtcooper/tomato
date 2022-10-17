export const randomChoice = items => {
  if (items.length > 0) {
    return items[Math.floor(Math.random() * items.length)]
  } else {
    return null
  }
}
