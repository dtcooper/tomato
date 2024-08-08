TODO List

## Version 1

- [x] [Supress power save mode](https://www.electronjs.org/docs/latest/api/power-save-blocker)
- [x] Trim silence on uploaded assets
- [x] Reject files based on pre-processed file hash
- [x] CSV export to client log entries
- [x] Idiot mode, easy mode, advanced mode
- [ ] ~~Timeout on fetch?~~ (websockets makes this unneeded, except for downloading files)
- [x] Attempt to prevent duplicate assets from playing within a certain time period
- [x] Start/end time for assets in client are based on "is likely to play at" time
- [x] Empty rotators are warned on (based on feature flag)
- [x] Deal with non-playable assets (error state ones)
- [x] Compression and selecting output device using a bridge to
      [the web audio API](https://developer.mozilla.org/en-US/docs/Web/API/AudioContext/createMediaElementSource).
- [x] Any custom django admin pages can [follow this guide](https://dev.to/daiquiri_team/creating-a-custom-page-in-django-admin-4pbd)
- [x] Flash **whole** screen after configurable time with some messaging ("play the promos, station management has been notified")
- [x] Button to get out of fullscreen (useful on Linux)

## Future Versions

Changes for 2024 based on real world usage in 2023 and feedback
- [x] Make rotators able to disabled (UI for assets / stopsets needs to show that too)
- [x] ~~Implement soft delete for assets~~ -- keep the file, but delete the DB entity
  - [x] Behind the scenes track deleted files.
- [x] Easier way to toggle, simple / standard / advanced view settings in client. Not in settings.
  - [ ] Change advanced mode copy to "admin" mode
  - [x] Build out "switch back to simple mode" timer feature a little better, ie ~~comma separated times?~~
- [x] Better datetime picker in admin
- [x] Skip track in stopset when we get to it
- [ ] ~~Mark a bad asset? Interesting. Not sure how it would work.~~ – too difficult
      to implement, too many opinions, person wishing to flag talks to manager-of-the-moment
- [x] Refresh playlist from backend. ~~Connected client status from backend? Communicate what's in the playlist?~~
  - [x] Minimally completed via `RELOAD_PLAYLIST_AFTER_DATA_CHANGES` setting
- [x] Backend client playlist editor
- [ ] ~~Status updates, ie news and traffic? Fullscreen thing?~~ / ~~Custom UI labels unused labels that play every N times (ie for telling the DJ to do something)~~ -- Probably not
- [x] Round-robin (or "cycle evenly") rotator scheduling, ignoring weight as an option for a rotator
- [x] Check / validate randomization algorithm
  - [x] Validated! Review of algorithm provided by [Andy](https://github.com/sagittandy/)
- [x] Mini-player column in asset list view
- [x] Asset alternates (single asset has 4-5 underlying audio files that are cycled through)
  - [x] Backend done
- [x] A large clock in the UI
- [x] Make weights for previous 24 hours... AND reflect that in front-end (day-of
      pill) and back-end (sortable)... will require change to `END_DATE_PRIORITY_WEIGHT_MULTIPLIER`
    - [x] Added day-of-event pill
- [x] Rudimentary stopset editor, in the form of "skip/queue", regenerate asset, and swap asset
  - [ ] Ability to "audition" assets on a second audio output?
- [x] ~~Stop playing at end of current asset. (Stop playing in 3s with fadeout as well?)~~ (Covered by skip)
- [x] A way to send a custom text notification to all connected clients from backend UI


## Other things

- [ ] Ability to do speech synthesis / pull asset from API? / weather
  - [ ] Best cross-platform way to do this might be to use [text2wav.node.js](https://github.com/abbr/text2wav.node.js)
        to generate WAV files with a timeout
- [ ] KLOS color scheme: `#D91E75`, `#4B89BF`, `#8CBF3F`, `#F2D750`, and `#D95525`
- [ ] "Island Mode" with an embedded [standalone Python distribution](https://python-build-standalone.readthedocs.io/en/latest/)
- [ ] Login interstitial to populate with demo data
- [ ] Integrated Twilio call board
- [x] Single app client lock (ie only ONE client per username/password)'
- [ ] Way to parse filename into rotator, start/end date
  - [ ] Submit form built into Tomato?
- [ ] Silence detection REJECTs audio assets in backend (if there's more than 2 seconds?) (behind FEATURE flag)
- [x] Export all audio assets as zip
  - [x] Import as well (have to be careful with different `protocol.json:protocol_version`)
- [ ] Add configurable silence between ads. Crossfade, with fade points? Fancy!
- [ ] Client "Demo mode", requiring no backend with demo assets.
- [x] Button to play an asset from a specific rotator
  - [x] Backend done as `SINGLE_PLAY_ROTATORS`
- [ ] Cursor can be a fun thing?
- [ ] Clickable playbar that seeks?


## August 2024 UX review with [Miranda Kay](mailto:miranda.e.kay@gmail.com)

- [x] Button box flashes between assets
- [ ] ~~Switch connected icons with feather wifi on/off~~
- [x] Danger button in settings
- [x] Denser progress radials - decrease to 4rem
- [x] First asset of next stop doesn't show log tooltip if current stop startedPlaying
- [x] Assets queued for skipping should grey out
- [x] Seed, leaf, flower icon for simple, intermediate, advanced
- [x] Alternating grey/white rows in AssetPicker component
- [x] Fix regenerate/swap not working button when wait intervals are disabled
