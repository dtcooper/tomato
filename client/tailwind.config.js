const materialUIColors = require("material-ui-colors")
const { emerald, night } = require("daisyui/src/theming/themes")

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
      colors: {
        playhead: "oklch(var(--playhead) / <alpha-value>)"
      }
    }
  },
  daisyui: {
    logs: false,
    darkTheme: "night",
    themes: [
      {
        emerald: {
          ...emerald,
          "--playhead": "var(--bc)" // base-content
        }
      },
      {
        night: {
          ...night,
          primary: emerald.primary,
          "--playhead": "100% 0 0" // white
        }
      }
    ]
  },
  plugins: [require("daisyui")]
}
