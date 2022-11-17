const extraResource = []

if (process.platform === "linux") {
  extraResource.push('./scripts/debian/start-tomato.sh')
}

module.exports = {
  packagerConfig: {
    ignore: [
      '^/src$',
      '^/scripts$',
      '^/tailwind.config.js$'
    ],
    extraResource, 
    executableName: 'tomato',
    icon: 'assets/icons/tomato'
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
          scripts: {
            postinst: './scripts/debian/postinst.sh',
            postrm: './scripts/debian/postrm.sh'
          }
        }
      }
    }
  ]
}
