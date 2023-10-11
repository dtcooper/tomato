module.exports = {
  packagerConfig: {
    ignore: ["^/src$", "^/scripts$", "^/forge.config.js$", "^/tailwind.config.js$"],
    executableName: "tomato",
    icon: "assets/icons/tomato"
  },
  makers: [
    {
      name: "@electron-forge/maker-dmg",
      config: {
        format: "ULFO"
      }
    },
    {
      name: "@electron-forge/maker-squirrel",
      config: {
        iconUrl: "https://raw.githubusercontent.com/dtcooper/tomato/main/client/assets/icons/tomato.ico",
        setupIcon: "assets/icons/tomato.ico"
      }
    },
    {
      name: "@electron-forge/maker-deb",
      config: {
        options: {
          icon: "assets/icons/tomato.png",
          desktopTemplate: "./scripts/debian/tomato.desktop",
          section: "sound",
          scripts: {
            postinst: "./scripts/debian/postinst.sh"
          }
        }
      }
    },
    {
      name: "electron-forge-maker-appimage"
    }
  ]
}
