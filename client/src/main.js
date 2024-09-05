const { app, BrowserWindow, powerSaveBlocker, shell, ipcMain, dialog, Menu, systemPreferences } = require("electron")
const dayjs = require("dayjs")
const dayjsUtc = require("dayjs/plugin/utc")
const windowStateKeeper = require("electron-window-state")
const fs = require("fs")
const { createGzip } = require("zlib")
const { pipeline } = require("stream")
const fsExtra = require("fs-extra")
const { parseArgs } = require("util")
const path = require("path")
const squirrelCheck = require("electron-squirrel-startup")
const { protocol_version } = require("../../server/constants.json")

const cmdArgs = parseArgs({
  options: {
    "enable-dev-mode": { type: "boolean", default: false },
    "show-quit-dialog-when-unpackaged": { type: "boolean", default: false },
    "disable-logs": { type: "boolean", default: false }
  },
  strict: false
}).values
const isDev = !!(cmdArgs["enable-dev-mode"] || process.env.NODE_ENV === "development")
const isNotPackagedAndDev = !app.isPackaged && isDev

// getting appData path *needs* to happen before single instance lock check (otherwise old path gets created)
const appDataDir = app.getPath("appData")
const getUserDataDir = (version = protocol_version) =>
  path.join(appDataDir, `tomato-radio-automation-p${version}${isNotPackagedAndDev ? "-dev" : ""}`)

const userDataDir = getUserDataDir()
const tomatoDataDir = path.join(userDataDir, "tomato")
const hardResetFile = path.join(tomatoDataDir, ".clear-dir")

if (fs.existsSync(hardResetFile)) {
  console.warn(`Got hard reset file (${hardResetFile}). Clearing user data dir: ${userDataDir}`)
  if (fs.existsSync(userDataDir)) {
    fs.rmSync(userDataDir, { recursive: true, force: true })
  }
}

console.log(`Using user data dir: ${userDataDir}`)
fs.mkdirSync(tomatoDataDir, { recursive: true, permission: 0o700 })
app.setPath("userData", userDataDir)

const singleInstanceLock = app.requestSingleInstanceLock()

if (squirrelCheck || !singleInstanceLock) {
  if (!singleInstanceLock) {
    console.error("Couldn't acquire single instance lock!")
  }
  app.quit()
} else {
  let window = null
  let blocker = null
  const [minWidth, minHeight, defaultWidth, defaultHeight] = [800, 600, 1000, 800]
  const iconPath = path.resolve(path.join(__dirname, "../assets/icons/tomato.png"))

  // Migrate when there's a protocol version bump
  for (let i = 0; i < protocol_version; i++) {
    const oldUserDataDir = getUserDataDir(i)
    if (i <= 6) {
      // We didn't use to add the tomato/ prefix to our data up to (and including) protocol 6
      if (fs.existsSync(oldUserDataDir)) {
        const oldAssetsDir = path.join(oldUserDataDir, "assets")
        // Copy over old assets to new folder
        if (fs.existsSync(oldAssetsDir)) {
          console.log(`Migrating old assets dir ${oldAssetsDir} => ${tomatoDataDir}`)
          fsExtra.copySync(oldAssetsDir, path.join(tomatoDataDir, "assets"), { overwrite: false })
        }
        fsExtra.removeSync(oldUserDataDir)
      }
    } else {
      // Starting with protocol 7, all our data directories were prefixed with tomato/
      const oldTomatoDataDir = path.join(oldUserDataDir, "tomato")
      if (fs.existsSync(oldTomatoDataDir)) {
        console.log(`Migrating old tomato dir ${oldTomatoDataDir} => ${tomatoDataDir}`)
        fsExtra.copySync(oldTomatoDataDir, tomatoDataDir, { overwrite: false })
      }
      if (fs.existsSync(oldUserDataDir)) {
        fsExtra.removeSync(oldUserDataDir)
      }
    }
  }

  app.commandLine.appendSwitch("disable-features", "OutOfBlinkCors,HardwareMediaKeyHandling,MediaSessionService")
  app.commandLine.appendSwitch("disable-pinch")

  if (!cmdArgs["disable-logs"]) {
    const logFileDir = path.join(tomatoDataDir, "logs")

    // Archive existing log files
    if (fs.existsSync(logFileDir)) {
      fs.readdir(logFileDir, (err, files) => {
        for (const file of files) {
          if (file.endsWith(".log")) {
            const filePath = path.join(logFileDir, file)
            const filePathGz = `${filePath}.gz`
            pipeline(
              fs.createReadStream(filePath),
              createGzip({ level: 9 }),
              fs.createWriteStream(filePathGz),
              (err) => {
                const fileToRemove = err ? filePathGz : filePath
                if (err) {
                  console.error("An error occurred:", err)
                } else {
                  console.log(`Archived previous log file: ${file}`)
                }
                fs.rm(fileToRemove, { force: true }, (err) => {
                  if (err) {
                    console.error(err)
                  }
                })
              }
            )
          }
        }
      })
    }

    fs.mkdirSync(logFileDir, { recursive: true, permission: 0o700 })
    dayjs.extend(dayjsUtc)
    const logFile = path.join(logFileDir, `${dayjs().format("YYYYMMDDHHmmss")}.log`)
    console.log(`Enabling electron logging: ${logFile}`)
    app.commandLine.appendSwitch("enable-logging", "file")
    app.commandLine.appendSwitch("log-file", logFile)
  }

  const buildTime = dayjs(BUILD_TIME)
  let applicationVersion = `${TOMATO_VERSION}\n(Built on ${buildTime.format("YYYY/MM/DD HH:mm:ss")})`
  if (TOMATO_EXTRA_BUILD_INFO) {
    applicationVersion = `${applicationVersion}\n${TOMATO_EXTRA_BUILD_INFO}`
  }
  app.setAboutPanelOptions({
    applicationName: "Tomato Radio Automation",
    copyright: `Released under the MIT license.\n\u00A9 2019-${buildTime.format("YYYY")} David Cooper, Miranda Kay, & the BMIR team.\nAll rights reserved.`,
    website: "https://github.com/dtcooper/tomato",
    iconPath,
    applicationVersion,
    version: "" // hide on macOS
  })

  const baseUrl = isNotPackagedAndDev
    ? "http://localhost:3000/"
    : `file://${path.normalize(path.join(__dirname, "..", "index.html"))}`
  // Append userDataDir with 'tomato' for client
  const baseParams = new URLSearchParams({
    tomatoDataDir,
    dev: isDev ? "1" : "0",
    packaged: app.isPackaged ? "1" : "0"
  })
  const url = `${baseUrl}?${baseParams.toString()}`

  const createWindow = () => {
    const { screen } = require("electron")
    const primaryDisplay = screen.getPrimaryDisplay()
    const { width: screenWidth, height: screenHeight } = primaryDisplay.workAreaSize

    const mainWindowState = windowStateKeeper({
      defaultWidth: Math.min(minWidth, Math.max(screenWidth, defaultWidth)),
      defaultHeight: Math.min(minHeight, Math.max(screenHeight, defaultHeight))
    })

    if (IS_MAC) {
      // Always show scrollbars on macos
      systemPreferences.setUserDefault("AppleShowScrollBars", "string", "Always")
    }

    const win = new BrowserWindow({
      x: mainWindowState.x,
      y: mainWindowState.y,
      width: mainWindowState.width,
      height: mainWindowState.height,
      useContentSize: true,
      minWidth,
      minHeight,
      icon: iconPath,
      webPreferences: {
        devTools: isDev,
        contextIsolation: false,
        nodeIntegration: true,
        webSecurity: false,
        spellcheck: false,
        backgroundThrottling: false
      }
    })
    win.webContents.setVisualZoomLevelLimits(1, 1)

    mainWindowState.manage(win)

    const menu = Menu.buildFromTemplate([
      // { role: 'appMenu' }
      ...(IS_MAC
        ? [
            {
              label: app.name,
              submenu: [
                { role: "about" },
                { type: "separator" },
                { role: "services" },
                { type: "separator" },
                { role: "hide" },
                { role: "hideOthers" },
                { role: "unhide" },
                { type: "separator" },
                { role: "quit" }
              ]
            }
          ]
        : []),
      // { role: 'fileMenu' }
      {
        label: "File",
        submenu: [...(IS_MAC ? [{ role: "close" }] : [{ role: "about" }, { role: "quit" }])]
      },
      // { role: 'editMenu' }
      {
        label: "Edit",
        submenu: [
          { role: "undo" },
          { role: "redo" },
          { type: "separator" },
          { role: "cut" },
          { role: "copy" },
          { role: "paste" },
          { role: "delete" },
          ...(IS_MAC ? [{ role: "pasteAndMatchStyle" }] : []),
          { type: "separator" },
          { role: "selectAll" }
        ]
      },
      // { role: 'viewMenu' }
      {
        label: "View",
        submenu: [
          ...(isDev
            ? [{ role: "reload" }, { role: "forceReload" }, { role: "toggleDevTools" }, { type: "separator" }]
            : []),
          { role: "togglefullscreen" }
        ]
      },
      // { role: 'windowMenu' }
      {
        label: "Window",
        submenu: [
          { role: "minimize" },
          { role: "zoom" },
          ...(IS_MAC
            ? [{ type: "separator" }, { role: "front" }, { type: "separator" }, { role: "window" }]
            : [{ role: "close" }])
        ]
      },
      {
        role: "help",
        submenu: [
          {
            label: "Learn More",
            click: async () => {
              await shell.openExternal("https://dtcooper.github.io/tomato/")
            }
          }
        ]
      }
    ])
    Menu.setApplicationMenu(menu)

    // Enable autoplay + midi
    const allowedPermissions = ["media", "midi", "midiSysex"]
    win.webContents.session.setPermissionCheckHandler((webContents, permission) => {
      return allowedPermissions.includes(permission)
    })
    win.webContents.session.setPermissionRequestHandler((webContents, permission, callback) => {
      callback(allowedPermissions.includes(permission))
    })

    if (!app.isPackaged && process.env.SVELTE_DEVTOOLS) {
      win.webContents.session.setPreloads([require.resolve("svelte-devtools-standalone")])
    }

    win.webContents.on("will-navigate", (event) => {
      // Allow niave page refreshes in dev only, when baseURL is matched (ie browser-sync)
      // Actual refresh uses "refresh" ipc message
      if (!isDev || !event.url.startsWith(baseUrl)) {
        event.preventDefault()
        shell.openExternal(event.url)
      }
    })

    if (app.isPackaged || cmdArgs["show-quit-dialog-when-unpackaged"]) {
      // Prevent accidental closing (except when unpackaged, since electron-forge restart kills the app
      win.on("close", (event) => {
        const choice = dialog.showMessageBoxSync(win, {
          type: "question",
          normalizeAccessKeys: false,
          buttons: ["Quit", "Cancel and keeping running"],
          defaultId: 1,
          cancelId: 1,
          title: "Quit Tomato",
          message: "Are you SURE you want to quit Tomato Radio Automation?"
        })

        if (choice === 1) {
          event.preventDefault()
        }
      })
    }

    win.loadURL(url)
    if (isNotPackagedAndDev) {
      win.webContents.openDevTools({ mode: "detach" })
    }

    if (IS_WIN32) {
      win.menuBarVisible = !win.isFullScreen()
    }
    win.on("enter-full-screen", () => {
      if (IS_WIN32) {
        win.menuBarVisible = false
      }
      win.webContents.send("set-fullscreen", true)
    })
    win.on("leave-full-screen", () => {
      if (IS_WIN32) {
        win.menuBarVisible = true
      }
      win.webContents.send("set-fullscreen", false)
    })

    return win
  }

  app.whenReady().then(async () => {
    window = createWindow()
  })

  const doRefresh = (params) => {
    if (window) {
      let extra = ""
      if (params) {
        const urlParams = { errorType: params.type || "host", errorMessage: params.message }
        extra = "&" + new URLSearchParams(urlParams).toString()
      }
      window.loadURL(`${url}${extra}`)
    }
  }

  ipcMain.handle("refresh", (event, params) => doRefresh(params))

  ipcMain.handle("clear-user-data-and-restart", () => {
    if (app.isPackaged) {
      fs.closeSync(fs.openSync(hardResetFile, "w"))
      app.relaunch()
      app.exit()
    } else {
      doRefresh({ type: "host", message: "Can't hard logout unless app is packaged!" })
    }
  })

  ipcMain.handle("is-fullscreen", () => {
    if (window) {
      return window.isFullScreen()
    }
  })
  ipcMain.handle("set-fullscreen", (event, value) => {
    if (window) {
      window.setFullScreen(value)
    }
  })

  ipcMain.handle("power-save-blocker", (event, on) => {
    if (on && blocker === null) {
      blocker = powerSaveBlocker.start("prevent-display-sleep")
      console.log("Turning on power save blocker")
    } else if (!on && blocker !== null) {
      console.log("Turning off power save blocker")
      powerSaveBlocker.stop(blocker)
      blocker = null
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
