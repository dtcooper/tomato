const materialUIColors = require('material-ui-colors')

// Use material UI colors
const colors = Object.keys(materialUIColors).reduce((obj, color) => {
  if (color !== 'common') {
    const newColor = color.replace(/([A-Z])/g, '-$&').toLowerCase().replace('grey', 'gray')
    obj[newColor] = materialUIColors[color]
  }
  return obj
}, {})

module.exports = {
  content: [
    './src/**/*.{html,js,njk}'
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: 'Space Grotesk Local',
        mono: 'Space Mono Local'
      },
      colors
    }
  },
  daisyui: {
    themes: ['synthwave']
  },
  plugins: [require('daisyui')]
}
