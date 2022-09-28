
const process = require('process')
const fs = require('fs')
const htmlmin = require('html-minifier')
const nunjucks = require('nunjucks')

module.exports = (eleventyConfig) => {
  eleventyConfig.setBrowserSyncConfig({
    files: ['dist/**/*'],
    port: 8080
  })
  eleventyConfig.addPassthroughCopy('assets')

  eleventyConfig.setNunjucksEnvironmentOptions({
    throwOnUndefined: true
  })

  eleventyConfig.addNunjucksGlobal('icon', function (name, classes = '') {
    const svg = fs.readFileSync(`assets/icons/${name.replace(':', '-')}.svg`, 'utf-8')
    return new nunjucks.runtime.SafeString(svg.replace(/^<svg/i, `<svg class="${classes}"`))
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
