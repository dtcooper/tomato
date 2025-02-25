<h1 align="center">
  <a href="https://dtcooper.github.io/tomato/">
    <img src="https://raw.github.com/dtcooper/tomato/main/docs/assets/tomato.png" width="100"><br>
    Tomato Radio Automation
  </a>
</h1>

<p align="center">
  <a href="https://dtcooper.github.io/tomato/">Documentation</a> |
  <a href="https://dtcooper.github.io/tomato/client/">Desktop App</a> |
  <a href="https://dtcooper.github.io/tomato/server/">Server</a> |
  <a href="https://github.com/dtcooper/tomato/blob/main/controller/">Button Box</a>
</p>

[![Client build status](https://img.shields.io/github/actions/workflow/status/dtcooper/tomato/build-client.yml?branch=main&label=client%20build)](https://github.com/dtcooper/tomato/actions/workflows/build-client.yml) [![Server build &amp deploy status](https://img.shields.io/github/actions/workflow/status/dtcooper/tomato/build-deploy-on-push.yml?branch=main&label=server%20build)](https://github.com/dtcooper/tomato/actions/workflows/build-deploy-on-push.yml) [![Docs build status](https://img.shields.io/github/actions/workflow/status/dtcooper/tomato/docs.yml?branch=main&label=docs%20build)](https://github.com/dtcooper/tomato/actions/workflows/docs.yml)

[![Latest release](https://img.shields.io/github/v/tag/dtcooper/tomato?filter=!preview-build&label=release)](https://github.com/dtcooper/tomato/releases/latest) [![MIT License](https://img.shields.io/github/license/dtcooper/tomato)](https://github.com/dtcooper/tomato/blob/main/LICENSE) [![GitHub stars](https://img.shields.io/github/stars/dtcooper/tomato?style=flat)](https://github.com/dtcooper/tomato/stargazers) [![GitHub Issues](https://img.shields.io/github/issues/dtcooper/tomato)](https://github.com/dtcooper/tomato/issues) [![Latest commit](https://img.shields.io/github/last-commit/dtcooper/tomato)](https://github.com/dtcooper/tomato/commits/)

Client and server for Tomato Radio Automation software. Tomato is easy to use,
and hard to screw up playout software written for the specific use case of
[Burning Man Information Radio](https://bmir.org).

<div align="center">
  <img src="https://raw.github.com/dtcooper/tomato/main/docs/assets/client/screenshot.png" width="850">
</div>

The backend server is written in [Python](https://www.python.org/)'s
[Django web framework](https://www.djangoproject.com/), heavily leveraging its
[automatic admin interface](https://docs.djangoproject.com/en/4.1/ref/contrib/admin/).

The desktop app is a native, cross-platform [Svelte](https://svelte.dev/) +
[Electron](https://www.electronjs.org/) app. It communicates with the backend
via a websocket and supports intermittent connectivity loss.

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
    [docker-nginx-certbot](https://github.com/JonasAlfredsson/docker-nginx-certbot),
    and [Dozzle](https://dozzle.dev/).
* MIDI Controller Button Box &mdash;
  [Raspberry Pi Pico](https://www.raspberrypi.com/documentation/microcontrollers/raspberry-pi-pico.html)
  (or similar) and [CircuitPython](https://circuitpython.org/)
  * See [`controller/README.md`](controller/README.md) for firmware/setup instructions
* Documentation
  * [MkDocs](https://www.mkdocs.org/) and [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)

## Acknowledgements

Tomato's UX and UI was designed in part by
[Miranda Kay](mailto:miranda.e.kay@gmail.com). Testing and feedback was provided
by the entire [Burning Man Information Radio (BMIR)](https://bmir.org) team.

## TODO List

_See [TODO](TODO.md) list._

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT)
&mdash; see the [LICENSE](https://github.com/dtcooper/tomato/blob/main/LICENSE)
file for details.
