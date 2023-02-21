const axios = require("axios")
const { context: esbuildContext, build: esbuild } = require("esbuild")
const { version: electronVersion } = require("electron/package.json")
const path = require("path")
const sveltePlugin = require("esbuild-svelte")
const sveltePreprocess = require("svelte-preprocess")

process.chdir(path.join(__dirname, ".."))

if (!process.env.NODE_ENV) {
  process.env.NODE_ENV = "production"
}

const releasesUrl = "https://electronjs.org/headers/index.json"

const runBuild = async () => {
  let electronReleases
  try {
    electronReleases = (await axios.get(releasesUrl, { timeout: 5000, maxContentLength: 1024 * 1024 * 1024 })).data
    if (!Array.isArray(electronReleases)) {
      throw new Error("Response not a JSON array")
    }
  } catch (e) {
    console.error(`Error fetching Electron releases: ${e.message}`)
    electronReleases = []
  }

  const isDev = process.env.NODE_ENV === "development"
  const watch = isDev && !process.env.BUILD_NO_WATCH
  const srcDir = "src"
  const distDir = "dist"
  const { node: nodeVersion } = electronReleases.find((release) => release.version === electronVersion) || {}

  console.log(
    `Building for ${isDev ? "development" : "production"}, electron ${electronVersion}, ` +
      `node ${nodeVersion || "unknown"}${watch ? ", watching" : ""}...`
  )

  const defaults = {
    bundle: true,
    logLevel: "info",
    minify: !isDev,
    platform: "node",
    sourcemap: true,
    define: { "process.env.NODE_ENV": `"${process.env.NODE_ENV}"` }
  }

  if (nodeVersion) {
    defaults.target = `node${nodeVersion}`
  }

  const build = async (infile, options) => {
    options = {
      entryPoints: [path.join(srcDir, infile)],
      outfile: path.join(distDir, infile),
      ...defaults,
      ...options
    }

    if (watch) {
      const ctx = await esbuildContext({
        entryPoints: [path.join(srcDir, infile)],
        outfile: path.join(distDir, infile),
        ...defaults,
        ...options
      })
      ctx.watch()
    } else {
      esbuild(options)
    }
  }

  build("main.js", { external: ["electron", "svelte-devtools-standalone"] })
  build("app.js", {
    external: ["./assets/fonts/*"],
    format: "esm",
    loader: { ".svg": "text" },
    plugins: [
      sveltePlugin({
        compilerOptions: { dev: isDev, enableSourcemap: true },
        cache: "overzealous",
        preprocess: [
          sveltePreprocess({
            sourceMap: true,
            postcss: {
              plugins: [require("tailwindcss"), require("autoprefixer")]
            }
          })
        ]
      })
    ]
  })

  if (watch) {
    const browserSync = require("browser-sync")
    browserSync({ port: 3000, server: ".", open: false, watch: true, notify: false })
  }
}

runBuild()
