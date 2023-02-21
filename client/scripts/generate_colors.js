const muiColors = require("material-ui-colors")
const Color = require("color")

const filter = ["common", "brown", "gray", "blue-gray"]
const colors = []

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
    colors.push({ name: color, value: values.A400, content: contentColor(values.A400) })
  }
}

console.log("[")
for (let i = 0; i < colors.length; i++) {
  process.stdout.write("  " + JSON.stringify(colors[i]).replace(/[:,]/g, "$& "))
  if (i < colors.length - 1) {
    process.stdout.write(",")
  }
  process.stdout.write("\n")
}
console.log("]")
