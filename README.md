# Tomato Radio Automation

Client and server for Tomato Radio Automation software. Tomato is easy to use,
and hard to screw up playout software written for the specific use case of
[Burning Man Information Radio](https://bmir.org).

The server backend is written in [Python](https://www.python.org/)'s
[Django web framework](https://www.djangoproject.com/), heavily leveraging its
[automatic admin interface](https://docs.djangoproject.com/en/4.1/ref/contrib/admin/).

The client is a native, cross-platform [Electron](https://www.electronjs.org/)
app.

## Server Setup

Install [Docker](https://www.docker.com/) (which now includes
[Compose](https://docs.docker.com/compose/)),

```bash
# For Linux only. On macOS skip this step and install Docker Desktop.
curl -fsSL https://get.docker.com | sh
```

Then, clone the repository and enter the `server/` directory,

```bash
git clone https://github.com/dtcooper/tomato.git
cd tomato/server
```

Create and edit an `.env` environment variables file and optionally symlink
the development config for Compose,

```bash
cp .env.sample .env

# Only symlink this file when DEBUG=1
ln -s docker-compose.dev.yml docker-compose.override.yml
```

Now bring the server up using,

```bash
docker compose up
```


## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT)
&mdash; see the [LICENSE](https://github.com/dtcooper/tomato/blob/main/LICENSE)
file for details.
