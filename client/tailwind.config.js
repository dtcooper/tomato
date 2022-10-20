const materialUIColors = require('material-ui-colors')

// Use material UI colors
const colors = Object.keys(materialUIColors).reduce((obj, color) => {
  if (color !== 'common') {
    const newColor = color.replace(/([A-Z])/g, '-$&').toLowerCase().replace('grey', 'gray')
    obj[newColor] = materialUIColors[color]
  }
  return obj
}, {
  'tomato-green-dark': '#046736',
  'tomato-green-regular': '#40904c',
  'tomato-red-regular': '#db0201',
  'tomato-red-dark': '#aa0000',
  'tomato-green-light': '#9dc14b'
})

module.exports = {
  content: [
    'index.html',
    './src/**/*.{html,js,svelte}'
  ],
  theme: {
    screens: {
      sm: '601px', // must match minimum width in electron + 1
      md: '980px',
      lg: '1280px'
    },
    extend: {
      fontFamily: {
        sans: 'Space Grotesk Local',
        mono: 'Space Mono Local'
      },
      colors
    }
  },
  daisyui: {
    themes: ['dark', 'light']
  },
  plugins: [require('daisyui')]
}
