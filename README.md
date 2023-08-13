<h1 align="center">
  <a href="https://dtcooper.github.io/tomato/">
    <img src="https://raw.github.com/dtcooper/tomato/main/client/assets/icons/tomato.png" width="100"><br>
    Tomato Radio Automation
  </a>
</h1>

<p align="center">
  <a href="https://dtcooper.github.io/tomato/">Documentation</a> |
  <a href="https://dtcooper.github.io/tomato/client/">Desktop App</a> |
  <a href="https://dtcooper.github.io/tomato/server/">Server</a>
</p>

Client and server for Tomato Radio Automation software. Tomato is easy to use,
and hard to screw up playout software written for the specific use case of
[Burning Man Information Radio](https://bmir.org).

The backend server is written in [Python](https://www.python.org/)'s
[Django web framework](https://www.djangoproject.com/), heavily leveraging its
[automatic admin interface](https://docs.djangoproject.com/en/4.1/ref/contrib/admin/).

The desktop app is a native, cross-platform [Svelte](https://svelte.dev/) +
[Electron](https://www.electronjs.org/) app and optionally uses the
[Elgato Stream Deck](https://www.elgato.com/en/stream-deck) as a physical control
pad. It communicates withs the backend via a websocket and supports intermittant
connectivity loss.

## Running the Code

### Server

Detailed instructions on how to install the server in both development and
production environments
[can be found here in the docs](https://dtcooper.github.io/tomato/server/installation/).

### Client (Desktop App)

Download a
[development preview build here](https://github.com/dtcooper/tomato/releases/tag/preview-build)
or run the client's code locally
[following the instruction here](https://dtcooper.github.io/tomato/client/#run-development-code)

### Documentation

To run the documentation locally, install [Python 3.9](https://www.python.org/)
or higher. Then in your terminal,

```bash
# Install Poetry (for Python dependencies) if you don't already have it.
curl -sSL https://install.python-poetry.org | python3 -

# Clone the repo
git clone https://github.com/dtcooper/tomato.git

# Enter the docs code
cd tomato/docs

# Install dependencies and run
poetry install
poetry run mkdocs serve
```

Head over to <http://localhost:8888/> in your web browser.

## Stack

* Client &mdash; JavaScript ([Node.js](https://nodejs.org/en/))
  * [Electron](https://electronjs.org/), [Svelte](https://svelte.dev/),
    [Tailwind CSS](https://tailwindcss.com/), [daisyUI](https://daisyui.com/),
    and [esbuild](https://esbuild.github.io/).
* Server &mdash; [Python](https://www.python.org/)
  * Libraries: [Django](https://www.djangoproject.com/), [huey](https://huey.readthedocs.io/en/latest/),
    [Constance](https://django-constance.readthedocs.io/en/latest/), and [Starlette](https://www.starlette.io/)
  * Tools, Databases, and Containers: [PostgreSQL](https://www.postgresql.org/),
    [Redis](https://redis.io/),
    [docker-nginx-certbot](https://github.com/JonasAlfredsson/docker-nginx-certbot),
    and [Dozzle](https://dozzle.dev/).
* Documentation
  * [MkDocs](https://www.mkdocs.org/) and [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)

## TODO List

### Version 1

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

### Future Versions

- [ ] "Island Mode" with an embedded [standalone Python distribution](https://python-build-standalone.readthedocs.io/en/latest/)
- [ ] Login interstitial to populate with demo data
- [ ] Integrated Twilio call board
- [ ] Single app client lock (ie only ONE client per username/password)'
- [ ] Way to parse filename into rotator, start/end date
- [ ] Export all audio assets as zip
  - [ ] Import as well (have to be careful with different `protocol.json:protocol_version`)
- [ ] Custom UI labels unused labels that play every N times (ie for telling the DJ to do something)
- [ ] Add configurable silence between ads
- [ ] Client "Demo mode", requiring no backend with demo assets.
- [ ] Button to play an asset from a specific rotator (on Stream Deck too).
  - [x] Backend done as `SINGLE_PLAY_ROTATORS`

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT)
&mdash; see the [LICENSE](https://github.com/dtcooper/tomato/blob/main/LICENSE)
file for details.
