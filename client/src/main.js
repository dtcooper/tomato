import { app, BrowserWindow, session } from 'electron'
import fs from 'fs'
import path from 'path'
import os from 'os'
import { VENDOR_ID as ELGATO_VENDOR_ID } from '@elgato-stream-deck/core'

if (!app.isPackaged) {
  require('electron-reloader')(module)
  console.log('Using electron-reloader')
}

app.commandLine.appendSwitch('disable-features', 'OutOfBlinkCors')
app.setAboutPanelOptions({
  applicationName: 'Tomato Radio Automation\n(Desktop App)',
  copyright: `\u00A9 2019-${(new Date()).getFullYear()} David Cooper & BMIR.\nAll rights reserved.`,
  website: 'https://github.com/dtcooper/tomato',
  iconPath: '../assets/icons/tomato.png'
})

// TODO single app lock?
console.log(__dirname)

function createWindow () {
  const win = new BrowserWindow({
    width: 800,
    minWidth: 600,
    height: 600,
    minHeight: 480,
    icon: path.join(__dirname, '../assets/icons/tomato.ico'),
    webPreferences: {
      devTools: !app.isPackaged,
      contextIsolation: false,
      nodeIntegration: true
    }
  })

  win.webContents.session.on('select-hid-device', (event, details, callback) => {
    console.log('select-hid-device', details)
    win.webContents.session.on('hid-device-added', (event, device) => {
      console.log('added', device)
      if (device.vendorId === ELGATO_VENDOR_ID) {
        console.log('Elgato device plugged in')
      }
    })

    win.webContents.session.on('hid-device-removed', (event, device) => {
      console.log('revemoved', device)
      if (device.vendorId === ELGATO_VENDOR_ID) {
        console.log('Elgato device removed')
      }
    })

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

  console.log('PATH:', path.normalize(path.join(__dirname, '..', 'index.html')))
  win.loadFile(path.normalize(path.join(__dirname, '..', 'index.html')))
  if (!app.isPackaged) {
    win.webContents.openDevTools({ mode: 'detach' })
  }
}

app.whenReady().then(async () => {
  const alpineDevToolsPath = path.join(
    os.homedir(),
    '/Library/Application Support/Google/Chrome/Default/Extensions/fopaemeedckajflibkpifppcankfmbhk/1.2.0_0'
  )
  if (fs.existsSync(alpineDevToolsPath)) {
    await session.defaultSession.loadExtension(alpineDevToolsPath)
  }

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
