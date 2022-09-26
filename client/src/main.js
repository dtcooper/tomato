const { app, BrowserWindow, session } = require('electron')
const fs = require('fs')
const path = require('path')
const process = require('process')
const os = require('os')

app.commandLine.appendSwitch('disable-features', 'OutOfBlinkCors')

function createWindow () {
  const win = new BrowserWindow({
    width: 800,
    minWidth: 600,
    height: 600,
    minHeight: 480,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      webSecurity: false
    }
  })

  if (app.isPackaged) {
    win.loadFile('dist/index.html')
  } else {
    win.loadURL('http://localhost:8080')
    win.webContents.openDevTools({ mode: 'detach' })
  }
}

app.whenReady().then(async () => {
  console.log('hi mom')
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
  if (process.platform !== 'darwin') {
    app.quit()
  }
})
