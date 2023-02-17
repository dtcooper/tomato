const fs = require('fs')
const path = require('path')
const process = require('process')

const afterExtract = []
const extraLinuxFiles = ['start-tomato.sh', '50-elgato.rules']

if (process.platform === 'linux') {
  afterExtract.push((buildPath, electronVersion, platform, arch, done) => {
    for (const file of extraLinuxFiles) {
      fs.copyFileSync(path.join('scripts/debian', file), path.join(buildPath, file))
    }
    done()
  })
}

module.exports = {
  packagerConfig: {
    ignore: [
      '^/src$',
      '^/scripts$',
      '^/forge.config.js$',
      '^/tailwind.config.js$'
    ],
    executableName: 'tomato',
    icon: 'assets/icons/tomato',
    osxUniversal: {
      x64ArchFiles: 'Contents/Resources/app/standalone/**'
    },
    afterExtract
  },
  makers: [
    {
      name: '@electron-forge/maker-zip',
      platforms: [
        'darwin',
        'win32'
      ]
    },
    {
      name: '@electron-forge/maker-deb',
      config: {
        options: {
          icon: 'assets/icons/tomato.png',
          desktopTemplate: './scripts/debian/tomato.desktop',
          recommends: ['udev'],
          section: 'sound',
          bin: 'start-tomato.sh',
          scripts: {
            postinst: './scripts/debian/postinst.sh',
            postrm: './scripts/debian/postrm.sh'
          }
        }
      }
    }
  ]
}
