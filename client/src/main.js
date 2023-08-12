const { app, BrowserWindow, powerSaveBlocker, shell, ipcMain, nativeTheme, dialog, Menu } = require("electron")
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
  let blocker = null
  const [minWidth, minHeight, defaultWidth, defaultHeight] = [800, 600, 1000, 800]
  const isLinux = process.platform === "linux"
  const isMac = process.platform === "darwin"
  const isDev = process.argv.includes("--enable-dev-mode") || process.env.NODE_ENV === "development"
  const iconPath = path.resolve(path.join(__dirname, "../assets/icons/tomato.png"))

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
  app.commandLine.appendSwitch("disable-pinch")
  app.setAboutPanelOptions({
    applicationName: "Tomato Radio Automation\n(Desktop App)",
    copyright: `\u00A9 2019-${new Date().getFullYear()} David Cooper & BMIR.\nAll rights reserved.`,
    website: "https://github.com/dtcooper/tomato",
    iconPath,
    applicationVersion: TOMATO_VERSION,
    version: TOMATO_VERSION
  })

  const baseUrl =
    (!app.isPackaged && isDev)
      ? "http://localhost:3000/"
      : `file://${path.normalize(path.join(__dirname, "..", "index.html"))}`
  const url = `${baseUrl}?userDataDir=${encodeURIComponent(userDataDir)}&dev=${isDev ? "1" : "0"}`

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
      ...(isMac
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
        submenu: [...(isMac ? [{ role: "close" }] : [{ role: "quit" }])]
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
          ...(isMac ? [{ role: "pasteAndMatchStyle" }] : []),
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
          ...(isMac
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
      if (!isDev || !event.url.startsWith(baseUrl)) {
        event.preventDefault()
        shell.openExternal(event.url)
      }
    })

    if (app.isPackaged) {
      // Prevent accidental closing (except when unpackaged, since electron-forge restart kills the app
      win.on("close", async (event) => {
        event.preventDefault()
        const choice = await dialog.showMessageBox(win, {
          type: "question",
          normalizeAccessKeys: false,
          buttons: ["Quit", "Cancel & Keeping Running"],
          defaultId: 1,
          cancelId: 1,
          title: "Quit Tomato",
          message: "Are you SURE you want to quit Tomato?"
        })
        if (choice.response === 0) {
          window.destroy()
          app.quit()
        }
      })
    }

    win.loadURL(url)
    if (!app.isPackaged) {
      win.webContents.openDevTools({ mode: "detach" })
    }

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

  if (isLinux) {
    const dbus = require("@homebridge/dbus-native") // Don't bundle on mac/windows

    // Switch night and dark mode on Linux by subscribing to dbus
    dbus
      .sessionBus()
      .getService("org.freedesktop.portal.Desktop")
      .getInterface(
        "/org/freedesktop/portal/desktop",
        "org.freedesktop.portal.Settings",
        function (err, notifications) {
          notifications.Read("org.freedesktop.appearance", "color-scheme", function (err, resp) {
            console.log("Current color-scheme", resp[1][0][1][0])
            nativeTheme.themeSource = resp[1][0][1][0] ? "dark" : "light"
          })

          // dbus signals are EventEmitter events
          notifications.on("SettingChanged", function () {
            if (arguments["0"] == "org.freedesktop.appearance" && arguments["1"] == "color-scheme") {
              nativeTheme.themeSource = arguments["2"][1][0] ? "dark" : "light"
              console.log("SettingChanged", arguments)
            }
          })
        }
      )
  }
}
