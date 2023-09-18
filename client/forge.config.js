const fs = require("fs")
const path = require("path")
const process = require("process")

const afterExtract = []
const extraLinuxFiles = ["start-tomato.sh"]

if (process.platform === "linux") {
  // Override executable to start-tomato.sh for AppImage
  const appBuilder = require("app-builder-lib/out/util/appBuilder")
  const oldExecuteAppBuilderAsJson = appBuilder.executeAppBuilderAsJson
  appBuilder.executeAppBuilderAsJson = (args) => {
    const config = JSON.parse(args[args.length - 1])
    config.executableName = "start-tomato.sh"
    args[args.length - 1] = JSON.stringify(config)
    return oldExecuteAppBuilderAsJson(args)
  }

  afterExtract.push((buildPath, electronVersion, platform, arch, done) => {
    for (const file of extraLinuxFiles) {
      fs.copyFileSync(path.join("scripts/debian", file), path.join(buildPath, file))
    }
    done()
  })
}

module.exports = {
  packagerConfig: {
    ignore: ["^/src$", "^/scripts$", "^/forge.config.js$", "^/tailwind.config.js$"],
    executableName: "tomato",
    icon: "assets/icons/tomato",
    afterExtract
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
          bin: "start-tomato.sh",
          scripts: {
            postinst: "./scripts/debian/postinst.sh"
          }
        }
      }
    },
    {
      name: "electron-forge-maker-appimage",
    }
  ]
}
