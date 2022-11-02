const { build: esbuild } = require('esbuild')
const electronReleases = require('electron-releases')
const { version: electronVersion } = require('electron/package.json')
const path = require('path')
const sveltePlugin = require('esbuild-svelte')
const sveltePreprocess = require('svelte-preprocess')

process.chdir(path.join(__dirname, '..'))

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
  watch: isDev,
  define: { 'process.env.NODE_ENV': `"${process.env.NODE_ENV}"` }
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

build('main.js', { external: ['electron', 'svelte-devtools-standalone'] })
build('app.js', {
  external: ['./assets/fonts/*'],
  format: 'esm',
  loader: { '.svg': 'text' },
  plugins: [
    sveltePlugin({
      compilerOptions: { dev: isDev, enableSourcemap: true },
      cache: 'overzealous',
      preprocess: [
        sveltePreprocess({
          sourceMap: true,
          postcss: {
            plugins: [
              require('tailwindcss'),
              require('autoprefixer')
            ]
          }
        })
      ]
    })
  ]
})

if (isDev) {
  const browserSync = require('browser-sync')
  browserSync({ port: 3000, server: '.', open: false, watch: true, notify: false })
}
