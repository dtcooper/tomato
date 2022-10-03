import { app, BrowserWindow, session } from 'electron'
import fs from 'fs'
import path from 'path'
import os from 'os'
import { VENDOR_ID as ELGATO_VENDOR_ID } from '@elgato-stream-deck/core'

app.commandLine.appendSwitch('disable-features', 'OutOfBlinkCors')

function createWindow () {
  const win = new BrowserWindow({
    width: 800,
    minWidth: 600,
    height: 600,
    minHeight: 480,
    icon: path.join(__dirname, 'dist/assets/tomato.ico'),
    webPreferences: {
      devTools: !app.isPackaged,
      webSecurity: false,
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
    if (permission === 'hid') {
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

  if (app.isPackaged) {
    win.loadFile('dist/index.html')
  } else {
    win.loadURL('http://localhost:8080')
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
