const muiColors = require("material-ui-colors")
const Color = require("color")
const fs = require("fs")
const path = require("path")

const constants = require("../../server/constants.json")

const contantsFilePath = path.normalize(path.join(__dirname, "../../server/constants.json"))

// https://stackoverflow.com/a/43636793/1864783
const sortKeysReplacer = (key, value) =>
  value instanceof Object && !(value instanceof Array)
    ? Object.keys(value)
        .sort()
        .reduce((sorted, key) => {
          sorted[key] = value[key]
          return sorted
        }, {})
    : value

const stringify = (data) => JSON.stringify(data, sortKeysReplacer, 2) + "\n"

const filter = ["common", "brown", "gray", "blue-gray"]
let colors = []

// Borrowed front daisyUI
const contentColor = (color, percentage = 0.8) => {
  const mixColor = Color(color).isDark() ? "white" : "black"
  return Color(color).mix(Color(mixColor), percentage).saturate(10).round().hex().toLowerCase()
}

for (let [color, values] of Object.entries(muiColors)) {
  color = color
    .replace(/([A-Z])/g, "-$&")
    .toLowerCase()
    .replace("grey", "gray")
  if (!filter.includes(color)) {
    colors.push({ name: color, value: values.A400, content: contentColor(values.A400), dark: values.A700 })
  }
}

// Replace colors
fs.writeFileSync(contantsFilePath, stringify({ ...constants, colors }))

console.log("Successfully wrote constants.json file!")
