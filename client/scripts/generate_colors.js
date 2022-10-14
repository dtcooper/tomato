const muiColors = require('material-ui-colors')

const filter = ['common', 'brown', 'gray', 'blue-gray']
const colors = []

for (let [color, values] of Object.entries(muiColors)) {
  color = color.replace(/([A-Z])/g, '-$&').toLowerCase().replace('grey', 'gray')
  if (!filter.includes(color)) {
    colors.push({ name: color, light: values.A100, regular: values.A400, dark: values.A700 })
  }
}

console.log('[')
for (let i = 0; i < colors.length; i++) {
  process.stdout.write('  ' + JSON.stringify(colors[i]).replace(/[:,]/g, '$& '))
  if (i < colors.length - 1) {
    process.stdout.write(',')
  }
  process.stdout.write('\n')
}
console.log(']')
