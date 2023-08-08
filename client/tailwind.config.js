const materialUIColors = require("material-ui-colors")
const { "[data-theme=synthwave]": synthwaveTheme } = require("daisyui/src/theming/themes")
const { themeOrder: daisyThemes } = require("daisyui/src/theming/themeDefaults")

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
    extend: {
      minWidth: {
        sm: "600px"
      },
      fontFamily: {
        sans: "Space Grotesk Local",
        mono: "Space Mono Local"
      },
      colors
    }
  },
  daisyui: {
    logs: false,
    themes: [
       {
         tomato: {
           ...synthwaveTheme,
           primary: "#fc49ab",
           secondary: "#5fe8ff",
           accent: "#c07eec"
         }
       },
       ...daisyThemes
    ]
  },
  plugins: [require("daisyui")]
}
