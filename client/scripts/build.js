const axios = require("axios")
const dayjs = require("dayjs")
const dayjsUtc = require("dayjs/plugin/utc")
const { context: esbuildContext, build: esbuild } = require("esbuild")
const { version: electronVersion } = require("electron/package.json")
const path = require("path")
const process = require("process")
const sveltePlugin = require("esbuild-svelte")
const stylePlugin = require("esbuild-style-plugin")

dayjs.extend(dayjsUtc)

process.chdir(path.join(__dirname, ".."))

if (!process.env.NODE_ENV) {
  process.env.NODE_ENV = "production"
}

const releasesUrl = "https://electronjs.org/headers/index.json"
const IS_MAC = process.platform === "darwin"
const IS_WIN32 = process.platform === "win32"
const IS_LINUX = process.platform === "linux"

const runBuild = async () => {
  let electronReleases
  try {
    electronReleases = (await axios.get(releasesUrl, { timeout: 10000, maxContentLength: 1024 * 1024 * 1024 })).data
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

  const TOMATO_VERSION = `"${process.env.TOMATO_VERSION || (isDev ? "dev" : "unknown")}"`
  const TOMATO_EXTRA_BUILD_INFO = process.env.TOMATO_EXTRA_BUILD_INFO
    ? `"${process.env.TOMATO_EXTRA_BUILD_INFO}"`
    : "null"
  console.log(
    `Building for ${isDev ? "development" : "production"} (version: ${TOMATO_VERSION.slice(1, -1)}), ` +
      `electron ${electronVersion}, node ${nodeVersion || "unknown"}${watch ? ", watching" : ""}...`
  )

  const defaults = {
    bundle: true,
    logLevel: "info",
    minify: !isDev,
    platform: "node",
    sourcemap: true,
    define: {
      TOMATO_VERSION,
      TOMATO_EXTRA_BUILD_INFO,
      IS_MAC: IS_MAC.toString(),
      IS_WIN32: IS_WIN32.toString(),
      IS_LINUX: IS_LINUX.toString(),
      BUILD_TIME: Date.now().toString()
    }
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

    if (!options.bundle && options.external) {
      options.external = undefined
    }

    if (watch) {
      const ctx = await esbuildContext(options)
      ctx.watch()
    } else {
      esbuild(options)
    }
  }

  build("main.js", { bundle: !isDev, format: "cjs", external: ["electron", "svelte-devtools-standalone"] })
  build("app.js", {
    external: ["electron", "./assets/fonts/*"],
    loader: { ".svg": "text" },
    plugins: [
      sveltePlugin({
        compilerOptions: { dev: isDev, enableSourcemap: true }
      }),
      stylePlugin({
        postcss: {
          plugins: [require("tailwindcss"), require("autoprefixer")]
        }
      })
    ]
  })

  if (watch) {
    const browserSync = require("browser-sync")
    browserSync({ port: 3000, server: ".", open: false, watch: true, notify: false })
  }
}

runBuild()
