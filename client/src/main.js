import { app, BrowserWindow } from 'electron'
import path from 'path'
import { VENDOR_ID as ELGATO_VENDOR_ID } from '@elgato-stream-deck/core'

app.commandLine.appendSwitch('disable-features', 'OutOfBlinkCors')
app.setAboutPanelOptions({
  applicationName: 'Tomato Radio Automation\n(Desktop App)',
  copyright: `\u00A9 2019-${(new Date()).getFullYear()} David Cooper & BMIR.\nAll rights reserved.`,
  website: 'https://github.com/dtcooper/tomato',
  iconPath: path.resolve(path.join(__dirname, '../assets/icons/tomato.png'))
})

// TODO single app lock?
console.log('dirname', path.resolve(path.join(__dirname, '../assets/icons/tomato.ico')))

function createWindow () {
  const win = new BrowserWindow({
    width: 800,
    minWidth: 600,
    height: 600,
    minHeight: 480,
    icon: path.resolve(path.join(__dirname, '../assets/icons/tomato.png')),
    webPreferences: {
      devTools: !app.isPackaged,
      contextIsolation: false,
      nodeIntegration: true,
      webSecurity: false,
      nativeWindowOpen: true
    }
  })

  win.webContents.session.on('select-hid-device', (event, details, callback) => {
    if (details.deviceList && details.deviceList.length > 0) {
      callback(details.deviceList[0].deviceId)
    }
  })

  win.webContents.session.setPermissionCheckHandler((webContents, permission, requestingOrigin, details) => {
    if (permission === 'hid' || permission === 'media') {
      return true
    }
    return false
  })

  win.webContents.session.setDevicePermissionHandler((details) => {
    if (details.deviceType === 'hid' && details.device.vendorId === ELGATO_VENDOR_ID) {
      return true
    }
    return false
  })

  if (!app.isPackaged && process.env.SVELTE_DEVTOOLS) {
    win.webContents.session.setPreloads([require.resolve('svelte-devtools-standalone')])
  }

  if (app.isPackaged) {
    win.loadFile(path.normalize(path.join(__dirname, '..', 'index.html')))
  } else {
    win.loadURL('http://localhost:3000')
    win.webContents.openDevTools({ mode: 'detach' })
  }
}

app.whenReady().then(async () => {
  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  app.quit()
})
