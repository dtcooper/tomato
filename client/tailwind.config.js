
module.exports = {
  content: [
    './src/**/*.{html,js,njk}'
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: 'Space Grotesk Local',
        mono: 'Space Mono Local'
      }
    }
  },
  daisyui: {
    themes: ['synthwave']
  },
  plugins: [require('daisyui')]
}
