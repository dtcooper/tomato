import { app, BrowserWindow, powerSaveBlocker } from "electron"
import windowStateKeeper from "electron-window-state"
import fs from "fs"
import path from "path"

const elgatoVendorId = 4057
const [minWidth, minHeight, defaultWidth, defaultHeight] = [600, 480, 1000, 800]

const userDataDir = path.join(path.dirname(app.getPath("userData")), "tomato-radio-automation")
fs.mkdirSync(userDataDir, { recursive: true, permission: 0o700 })
app.setPath("userData", userDataDir)

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
    icon: path.resolve(path.join(__dirname, "../assets/icons/tomato.png")),
    webPreferences: {
      devTools: !app.isPackaged,
      contextIsolation: false,
      nodeIntegration: true,
      webSecurity: false
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

app.whenReady().then(async () => {
  powerSaveBlocker.start("prevent-display-sleep")
  createWindow()
})

app.on("window-all-closed", () => {
  app.quit()
})
