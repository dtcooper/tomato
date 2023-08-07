import dayjs from "dayjs"

export const prettyDuration = (item, max) => {
  item = dayjs.duration(item, "seconds")
  max = max ? dayjs.duration(max, "seconds") : item
  if (max.hours() > 0) {
    return `${item.hours()}:${item.format("mm:ss")}`
  } else if (max.minutes() >= 10) {
    return item.format("mm:ss")
  } else {
    return item.format("m:ss")
  }
}
