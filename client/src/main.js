const { app, BrowserWindow, powerSaveBlocker } = require("electron")
const windowStateKeeper = require("electron-window-state")
const fs = require("fs")
const fsExtra = require('fs-extra')
const path = require("path")
const child_process = require("child_process")
const os = require("os")
const util = require("util")
const { getPortPromise: getFreePort } = require('portfinder')
const { check: squirrelCheck } = require("electron-squirrel-startup")
const { protocol_version } = require("../../server/constants.json")
const { resourceLimits } = require("worker_threads")

if (squirrelCheck) {
  app.quit()
}

const elgatoVendorId = 4057
const [minWidth, minHeight, defaultWidth, defaultHeight] = [600, 480, 1000, 800]

const appDataDir = app.getPath("appData")
const userDataDir = path.join(app.getPath("appData"), `tomato-radio-automation-p${protocol_version}`)
fs.mkdirSync(userDataDir, { recursive: true, permission: 0o700 })
app.setPath("userData", userDataDir)

let serverPath, vendorLibsPath, pythonPath

if (app.isPackaged) {
  serverPath = path.join(process.resourcesPath, "server")
  vendorLibsPath = path.join(process.resourcesPath, "vendor")
} else {
  serverPath = path.resolve(path.join(__dirname, "../../server"))
  vendorLibsPath = path.resolve(path.join(__dirname, "../vendor"))
}

if (os.platform() === "win32") {
  pythonPath = path.resolve(vendorLibsPath, `python-${os.arch()}/python`)
} else {
  pythonPath = path.resolve(vendorLibsPath, `python-${os.arch()}/bin/python3`)
}

// Migrate when there's a protocol version bump
for (let i = 0; i < protocol_version; i++) {
  const oldUserDataDir = path.join(appDataDir, `tomato-radio-automation-p${i}`)
  if (fs.existsSync(oldUserDataDir)) {
    for (let oldDirToMove of ["assets", "embedded-tomato-server"]) {
      const oldDirToMovePath = path.join(oldUserDataDir, oldDirToMove)
      if (fs.existsSync(oldDirToMovePath)) {
        console.log(`Migrating old data dir ${oldDirToMove} => ${userDataDir}`)
        fsExtra.copySync(oldDirToMovePath, path.join(userDataDir, oldDirToMove), { overwrite: false })
      }
    }
    fsExtra.removeSync(oldUserDataDir)
  }
}

app.commandLine.appendSwitch("disable-features", "OutOfBlinkCors")
app.setAboutPanelOptions({
  applicationName: "Tomato Radio Automation\n(Desktop App)",
  copyright: `\u00A9 2019-${new Date().getFullYear()} David Cooper & BMIR.\nAll rights reserved.`,
  website: "https://github.com/dtcooper/tomato",
  iconPath: path.resolve(path.join(__dirname, "../assets/icons/tomato.png"))
})

function createWindow() {
  const { screen } = require("electron")
  const primaryDisplay = screen.getPrimaryDisplay()
  const { width: screenWidth, height: screenHeight } = primaryDisplay.workAreaSize

  const mainWindowState = windowStateKeeper({
    defaultWidth: Math.min(minWidth, Math.max(screenWidth, defaultWidth)),
    defaultHeight: Math.min(minHeight, Math.max(screenHeight, defaultHeight))
  })

  const win = new BrowserWindow({
    x: mainWindowState.x,
    y: mainWindowState.y,
    width: mainWindowState.width,
    height: mainWindowState.height,
    minWidth,
    minHeight,
    fullscreen: false,
    fullscreenable: false,
    icon: path.resolve(path.join(__dirname, "../assets/icons/tomato.png")),
    webPreferences: {
      devTools: !app.isPackaged,
      contextIsolation: false,
      nodeIntegration: true,
      webSecurity: false,
      spellcheck: false
    }
  })
  win.webContents.setVisualZoomLevelLimits(1, 1)

  mainWindowState.manage(win)

  win.webContents.session.on("select-hid-device", (event, details, callback) => {
    if (details.deviceList && details.deviceList.length > 0) {
      callback(details.deviceList[0].deviceId)
    }
  })

  win.webContents.session.setPermissionCheckHandler((webContents, permission, requestingOrigin, details) => {
    if (permission === "hid" || permission === "media") {
      return true
    }
    return false
  })

  win.webContents.session.setDevicePermissionHandler((details) => {
    if (details.deviceType === "hid" && details.device.vendorId === elgatoVendorId) {
      return true
    }
    return false
  })

  if (!app.isPackaged && process.env.SVELTE_DEVTOOLS) {
    win.webContents.session.setPreloads([require.resolve("svelte-devtools-standalone")])
  }

  const queryString = "userDataDir=" + encodeURIComponent(userDataDir)
  const url = app.isPackaged
    ? `file://${path.normalize(path.join(__dirname, "..", "index.html"))}`
    : "http://localhost:3000/"
  win.loadURL(`${url}?${queryString}`)
  if (!app.isPackaged) {
    win.webContents.openDevTools({ mode: "detach" })
  }
}

let djangoProcess = null, miniRedisProcess = null, hueyProcess = null, wsApiProcess = null

const spawnPromise = async (...args) => {
  let stdout, stderr
  try {
    ({ stdout, stderr } = await util.promisify(child_process.execFile)(...args))
  } catch (e) {
    ({ stdout, stderr } = e)
  }
  if (stdout)
    console.log(stdout)
  if (stderr)
    console.error(stderr)
}

const startEmbeddedDjangoServer = async () => {
  fs.mkdirSync(path.join(userDataDir, "embedded-tomato-server"), { recursive: true, permission: 0o700 })

  const djangoPort = await getFreePort({host: "127.0.0.1", port: 9152})
  const miniRedisPort = await getFreePort({host: "127.0.0.1", port: 9162})
  const wsApiPort = await getFreePort({host: "127.0.0.1", port: 9172})
  const pyRun = (cmd, asPromise = false, env = {}) => {
    func = asPromise ? spawnPromise : child_process.spawn
    console.log("Executing:", pythonPath, ...cmd)
    return func(pythonPath, cmd, {stdio: "inherit", env: {
      ...process.env,
      TOMATO_STANDALONE: "1",
      TOMATO_STANDALONE_USERDATA_DIR: path.join(userDataDir, "embedded-tomato-server"),
      TOMATO_STANDALONE_FFMPEG_DIR: vendorLibsPath,
      TOMATO_STANDALONE_MINI_REDIS_PORT: miniRedisPort,
      TIMEZONE: Intl.DateTimeFormat().resolvedOptions().timeZone,
      PYTHONPATH: path.join(vendorLibsPath, "pypackages"),
      ...env
    }})
  }

  const managePath = path.join(serverPath, "manage.py")
  await pyRun([managePath, "migrate"], true)
  await pyRun([managePath, "createsuperuser", "--noinput", "--username", "tomato"], true, { DJANGO_SUPERUSER_PASSWORD: "tomato" })

  console.log(`running mini redis @ ${miniRedisPort}`)
  miniRedisProcess = child_process.spawn(path.join(vendorLibsPath, "mini-redis-server"), ["--port", miniRedisPort], {stdio: "inherit"})
  djangoProcess = pyRun([managePath, "runserver", "--noreload", "--insecure", `127.0.0.1:${djangoPort}`])
  hueyProcess = pyRun([managePath, "run_huey", "--workers", "4", "--flush-locks"])
  wsApiProcess = pyRun(["-m", "uvicorn", "--port", wsApiPort, "--host", "127.0.0.1", "--workers", "1", "--app-dir", serverPath, "ws_api:app"], false, { DJANGO_SETTINGS_MODULE: "tomato.settings" })
  return djangoPort
}

app.whenReady().then(async () => {
  powerSaveBlocker.start("prevent-display-sleep")
  createWindow()
  try {
    await startEmbeddedDjangoServer()
  } catch (e) {
    console.error(e)
    console.log("Error starting Django server")
  }
})

app.on("window-all-closed", () => {
  app.quit()
})

app.on('before-quit', () => {
  const processes = [djangoProcess, miniRedisProcess, hueyProcess, wsApiProcess]
  for (let process of processes) {
    if (process) {
      console.log("Killing:", ...process.spawnargs)
      process.kill("SIGINT")
    }
  }
})
