
const process = require('process')
const htmlmin = require('html-minifier')

module.exports = (eleventyConfig) => {
  eleventyConfig.setBrowserSyncConfig({
    files: ['dist/**/*'],
    port: 8080,
  })

  eleventyConfig.setNunjucksEnvironmentOptions({
    throwOnUndefined: true
  })

  eleventyConfig.addNunjucksGlobal('static', function (url) {
    if (process.env.NODE_ENV === 'production') {
      const urlNoExt = url.split('.').slice(0, -1).join('.')
      const ext = url.split('.').at(-1)
      url = `${urlNoExt}.min.${ext}`
    }
    return url
  })

  eleventyConfig.addTransform('htmlmin', function (content) {
    if (process.env.NODE_ENV === 'production' && this.outputPath && this.outputPath.endsWith('.html')) {
      return htmlmin.minify(content, {
        useShortDoctype: true,
        removeComments: true,
        collapseWhitespace: true
      })
    }
    return content
  })

  return {
    dir: {
      input: 'src',
      output: 'dist'
    }
  }
}
