import dayjs from "dayjs"
import dayjsPluginCustomParseFormat from "dayjs/plugin/customParseFormat"
import dayjsPluginDuration from "dayjs/plugin/duration"
import dayjsPluginIsSameOrAfter from "dayjs/plugin/isSameOrAfter"
import dayjsPluginIsSameOrBefore from "dayjs/plugin/isSameOrBefore"

dayjs.extend(dayjsPluginCustomParseFormat)
dayjs.extend(dayjsPluginDuration)
dayjs.extend(dayjsPluginIsSameOrAfter)
dayjs.extend(dayjsPluginIsSameOrBefore)

import App from "./App.svelte"

export default new App({
  target: document.body
})
