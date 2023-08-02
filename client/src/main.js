const { app, BrowserWindow, powerSaveBlocker, shell, ipcMain } = require("electron")
const windowStateKeeper = require("electron-window-state")
const fs = require("fs")
const fsExtra = require("fs-extra")
const path = require("path")
const { check: squirrelCheck } = require("electron-squirrel-startup")
const { protocol_version } = require("../../server/constants.json")

// Needs to happen before single instance lock check
const appDataDir = app.getPath("appData")
const userDataDir = path.join(appDataDir, `tomato-radio-automation-p${protocol_version}`)
fs.mkdirSync(userDataDir, { recursive: true, permission: 0o700 })
app.setPath("userData", userDataDir)

const singleInstanceLock = app.requestSingleInstanceLock()

if (squirrelCheck || !singleInstanceLock) {
  app.quit()
} else {
  let window = null
  const elgatoVendorId = 4057
  const [minWidth, minHeight, defaultWidth, defaultHeight] = [600, 480, 1000, 800]

  // Migrate when there's a protocol version bump
  for (let i = 0; i < protocol_version; i++) {
    const oldUserDataDir = path.join(appDataDir, `tomato-radio-automation-p${i}`)
    const oldAssetsDir = path.join(oldUserDataDir, "assets")
    if (fs.existsSync(oldUserDataDir)) {
      // Copy over old assets to new folder
      if (fs.existsSync(oldAssetsDir)) {
        console.log(`Migrating old data dir ${oldUserDataDir} => ${userDataDir}`)
        fsExtra.copySync(oldAssetsDir, path.join(userDataDir, "assets"), { overwrite: false })
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

  const baseUrl = app.isPackaged || NODE_ENV === "production"
    ? `file://${path.normalize(path.join(__dirname, "..", "index.html"))}`
    : "http://localhost:3000/"
  const url = `${baseUrl}?userDataDir=${encodeURIComponent(userDataDir)}`

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

    win.webContents.on("will-navigate", (event) => {
      // Allow niave page refreshes in dev only, when baseURL is matched (ie browser-sync)
      // Actual refresh uses "refresh" ipc message
      if (!IS_DEV || !event.url.startsWith(baseUrl)) {
        event.preventDefault()
        shell.openExternal(event.url)
      }
    })

    win.loadURL(url)
    if (!app.isPackaged) {
      win.webContents.openDevTools({ mode: "detach" })
    }

    return win
  }

  app.whenReady().then(async () => {
    powerSaveBlocker.start("prevent-display-sleep")
    window = createWindow()
  })

  ipcMain.handle("refresh", (event, params) => {
    if (window) {
      let extra = ''
      if (params) {
        const urlParams = { errorType: params.type || "host", errorMessage: params.message }
        extra = '&' + (new URLSearchParams(urlParams)).toString()
      }
      window.loadURL(`${url}${extra}`)
    }
  })

  app.on("second-instance", () => {
    if (window) {
      if (window.isMinimized()) {
        window.restore()
      }
      window.show()
    }
  })

  app.on("window-all-closed", () => {
    app.quit()
  })
}
