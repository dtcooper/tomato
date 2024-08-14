const materialUIColors = require("material-ui-colors")
const daisyui = require("daisyui")
const themes = require("daisyui/src/theming/themes")

// Need to be the exact same as in src/utils.js
const lightTheme = "emerald"
const darkTheme = "night"

// Use material UI colors
const colors = Object.keys(materialUIColors).reduce(
  (obj, color) => {
    if (color !== "common") {
      const newColor = color
        .replace(/([A-Z])/g, "-$&")
        .toLowerCase()
        .replace("grey", "gray")
      obj[newColor] = materialUIColors[color]
    }
    return obj
  },
  {
    "tomato-green-dark": "#046736",
    "tomato-green-regular": "#40904c",
    "tomato-red-regular": "#db0201",
    "tomato-red-dark": "#aa0000",
    "tomato-green-light": "#9dc14b"
  }
)

module.exports = {
  content: ["index.html", "./src/**/*.{html,js,svelte}"],
  theme: {
    screens: {
      md: "900px",
      "clk-sm": "1145px", // Clock when not wide
      "clk-wd": "1525px" // Clock when wide
    },
    extend: {
      fontFamily: {
        sans: "Inter Local",
        mono: "Space Mono Local"
      },
      colors
    }
  },
  daisyui: {
    logs: false,
    darkTheme: darkTheme,
    themes: [{ [lightTheme]: themes[lightTheme] }, { [darkTheme]: themes[darkTheme] }]
  },
  plugins: [daisyui]
}
