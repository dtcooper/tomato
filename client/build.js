const { build: esbuild } = require('esbuild')
const electronReleases = require('electron-releases')
const { version: electronVersion } = require('electron/package.json')
const path = require('path')
const process = require('process')
const sveltePlugin = require('esbuild-svelte')
const sveltePreprocess = require('svelte-preprocess')

if (!process.env.NODE_ENV) {
  process.env.NODE_ENV = 'production'
}

const isDev = process.env.NODE_ENV === 'development'
const srcDir = 'src'
const distDir = 'dist'
const { deps: { node: nodeVersion } = {} } = electronReleases.find(release => release.version === (electronVersion)) || {}

const defaults = {
  bundle: true,
  logLevel: 'info',
  minify: !isDev,
  platform: 'node',
  sourcemap: true,
  watch: isDev
}

if (nodeVersion) {
  defaults.target = `node${nodeVersion}`
}

const build = (infile, options) => {
  return esbuild({
    entryPoints: [path.join(srcDir, infile)],
    outfile: path.join(distDir, infile),
    ...defaults,
    ...options
  })
}

build('main.js', { external: ['electron', 'electron-reloader'] })
build('app.js', {
  external: ['./assets/*'],
  format: 'esm',
  plugins: [
    sveltePlugin({
      compilerOptions: { dev: isDev },
      preprocess: sveltePreprocess({
        sourceMap: true,
        postcss: {
          plugins: [
            require('tailwindcss'),
            require('autoprefixer')
          ]
        }
      })
    })
  ]
})
