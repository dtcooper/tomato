# TODO List

## Client and Server

- [x] Make sure server has the same DB migration version as client via the ping
      and/or auth endpoints.
- [ ] Report assets played to server, probably using UIDs to allow accidental dupes
- [x] Logging and reporting on client actions.

## Server

- [ ] If an empty project is detected, create an install button on admin login/landing,
      providing option to create initial data. Bonus: Station ID says _55.5 FM, KMUR Made
      Up Radio_ or something silly.
- [x] Sample generation stop set block server side testing, with optional date override.
- [ ] Use expose nginx + gunicorn container, rather than Django so uploads are performant
      and one can deploy to prod using Docker.
- [ ] Implement `STRIP_UPLOADED_AUDIO`.

## Client

- [x] Minimum window dimensions and full screen on all three platforms.
- [x] Save window position on all three platforms and whether maximized / fullscreen
- [ ] Prevent hibernation, ie using `caffeinate` cmd on macOS and on Windows,
      `SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)`
- [ ] Write unit tests.
- [ ] Client standalone mode, ie run Django in a separate process. (Will need to
      include compiled sox with mp3 libs on macOS/Window and build an additional Django
      executable with PyInstaller, however will need to work around
      [`PyInstaller:MERGE(...)` being broken](https://pyinstaller.readthedocs.io/en/latest/spec-files.html#multipackage-bundles).)
- [ ] Build Windows with high res manifest file:
      [link](https://github.com/cztomczak/cefpython/issues/530#issuecomment-505066492)
- [x] Build macOS with a high DPI plist file `NSPrincipalClass = NSApplication`,
      [example here.](https://pyinstaller.readthedocs.io/en/stable/spec-files.html#spec-file-options-for-a-mac-os-x-bundle)
- [x] For linux PyInstaller example, need to move files to `dist/cefpython3` folder
      _or_ configure cefpython.Initialize(...) to use appropriate path settings.
      Can comment on bug [here](https://github.com/cztomczak/cefpython/issues/135).
- [ ] Create Linux `.deb` that depends on package `libgtk2.0`.
- [x] Allow output device selection, ie via `navigator.mediaDevices.enumerateDevices()`,
      and `wavesurfer.setSinkId()`. Note: there's
      [a bug](https://bitbucket.org/chromiumembedded/cef/issues/2064/persist-webrtc-deviceids-across-restart)
      in cef where the `deviceId` (aka `sinkId`) of a device changes every start,
      so I'll have to persist the output device via label matching.
- [ ] Long tracks render using NES.css's progress bar, rather than Wavesurfer.
- [ ] Error checking, see Wavesurfer's [error event](https://wavesurfer-js.org/docs/events.html)
- [ ] Refactor / clean up JS. Currently it's pretty prototype-y.
- [ ] Animation when wait time is up
- [ ] Clean cache button (cache size estimate based on files not backed by Asset rows)
- [x] Left/right keyboard controls iff `CLICKABLE_WAVEFORM = True`
- [ ] Total stopset time, as well as MM:SS / MM:SS total left in current Stop Set.
