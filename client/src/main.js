const { app, BrowserWindow, powerSaveBlocker, shell, ipcMain, dialog, Menu } = require("electron")
const windowStateKeeper = require("electron-window-state")
const fs = require("fs")
const fsExtra = require("fs-extra")
const { parseArgs } = require("util")
const path = require("path")
const { check: squirrelCheck } = require("electron-squirrel-startup")
const { protocol_version } = require("../../server/constants.json")

const cmdArgs = parseArgs({
  options: {
    "enable-dev-mode": { type: "boolean", default: false },
    "show-quit-dialog-when-unpackaged": { type: "boolean", default: false }
  },
  strict: false
}).values
const isDev = cmdArgs["enable-dev-mode"] || process.env.NODE_ENV === "development"
const isNotPackagedAndDev = !app.isPackaged && isDev

// getting appData path *needs* to happen before single instance lock check (otherwise old path gets created)
const appDataDir = app.getPath("appData")
const getUserDataDir = (version = protocol_version) =>
  path.join(appDataDir, `tomato-radio-automation-p${version}${isNotPackagedAndDev ? "-dev" : ""}`)

const userDataDir = getUserDataDir()
console.log(`Using user data dir: ${userDataDir}`)
fs.mkdirSync(userDataDir, { recursive: true, permission: 0o700 })
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

  app.commandLine.appendSwitch("disable-features", "OutOfBlinkCors,HardwareMediaKeyHandling,MediaSessionService")
  app.commandLine.appendSwitch("disable-pinch")
  app.setAboutPanelOptions({
    applicationName: "Tomato Radio Automation\n(Desktop App)",
    copyright: `\u00A9 2019-${new Date().getFullYear()} David Cooper & BMIR.\nAll rights reserved.`,
    website: "https://github.com/dtcooper/tomato",
    iconPath,
    applicationVersion: TOMATO_VERSION,
    version: TOMATO_VERSION
  })

  const baseUrl = isNotPackagedAndDev
    ? "http://localhost:3000/"
    : `file://${path.normalize(path.join(__dirname, "..", "index.html"))}`
  const baseParams = new URLSearchParams({ userDataDir, dev: isDev ? "1" : "0" })
  const url = `${baseUrl}?${baseParams.toString()}`

  const createWindow = () => {
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
    win.webContents.session.setPermissionCheckHandler((webContents, permission, requestingOrigin, details) => {
      return allowedPermissions.includes(permission)
    })
    win.webContents.session.setPermissionRequestHandler((webContents, permission, callback, details) => {
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
    if (!app.isPackaged) {
      win.webContents.openDevTools({ mode: "detach" })
    }

    win.on("enter-full-screen", () => {
      win.webContents.send("set-fullscreen", true)
    })
    win.on("leave-full-screen", () => {
      win.webContents.send("set-fullscreen", false)
    })

    return win
  }

  app.whenReady().then(async () => {
    window = createWindow()
  })

  ipcMain.handle("refresh", (event, params) => {
    if (window) {
      let extra = ""
      if (params) {
        const urlParams = { errorType: params.type || "host", errorMessage: params.message }
        extra = "&" + new URLSearchParams(urlParams).toString()
      }
      window.loadURL(`${url}${extra}`)
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
