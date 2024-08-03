const materialUIColors = require("material-ui-colors")

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
      md: "900px"
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
    darkTheme: "night",
    themes: ["emerald", "night"]
  },
  plugins: [require("daisyui")]
}
