
module.exports = {
  content: [
    './src/**/*.{html,js,njk}'
  ],
  theme: {},
  daisyui: {
    themes: [{
      tomato: {
        fontFamily: 'Space Mono,ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,Liberation Mono,Courier New,monospace',
        primary: '#fc49ab',
        secondary: '#5fe8ff',
        accent: '#c07eec',
        neutral: '#3d3a00',
        'neutral-content': '#ffee00',
        'base-100': '#ffee00',
        info: '#3ABFF8',
        success: '#36D399',
        warning: '#FBBD23',
        error: '#F87272',
        '--rounded-box': '0',
        '--rounded-btn': '0',
        '--rounded-badge': '0',
        '--tab-radius': '0',
        '--btn-text-case': 'none'
      }
    }]
  },
  plugins: [require('daisyui')]
}
