import dayjs from "dayjs"
import dayjsPluginCustomParseFormat from "dayjs/plugin/customParseFormat"
import dayjsPluginDuration from "dayjs/plugin/duration"
import dayjsPluginIsSameOrAfter from "dayjs/plugin/isSameOrAfter"
import dayjsPluginIsSameOrBefore from "dayjs/plugin/isSameOrBefore"
import { protocol_version } from "../../server/constants.json"

dayjs.extend(dayjsPluginCustomParseFormat)
dayjs.extend(dayjsPluginDuration)
dayjs.extend(dayjsPluginIsSameOrAfter)
dayjs.extend(dayjsPluginIsSameOrBefore)

import App from "./App.svelte"

console.log(`Starting Tomato Radio Automation ${TOMATO_VERSION} (protocol: ${protocol_version}) at ${dayjs().format()}`)
export default new App({
  target: document.body
})
