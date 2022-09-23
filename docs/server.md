---
title: Server
---

# The Tomato Backend Server

The backend server is written in [Python]'s [Django web framework][django],
heavily leveraging its automatic admin interface.

## Installation

Follow these steps to get started.

!!! note "Docker Installation"

    You'll need to install [Docker] to get started (which now comes preloaded
    with [Compose]).

    === "Linux Instructions"
        On Linux, execute the following at the command line to install Docker,

        ```bash
        curl -fsSL https://get.docker.com | sh
        ```

    === "macOS Instructions"
        You can install Docker Desktop by [following the instructions here][docker-desktop].


At the command line clone and enter [Tomato's git repository][tomato-git], then
copy over the `.env` configuration file.

```bash
git clone https://github.com/dtcooper/tomato.git
cd tomato/server
cp .env.sample .env
```

=== "Development Mode"

    Open up the `.env` file you just created using your favourite text editor.
    Action on the following,

    * Set `DEBUG` flag to `1` &mdash; which tells Tomato to run in development
      mode.

    Now, create a symbolic link for the development [Compose] overrides,

    ```bash
    ln -s docker-compose.dev.yml docker-compose.overrides.yml
    ```

    Build the containers (or pull them by instead executing `#!bash docker compose pull`),

    ```bash
    docker compose build
    ```

    !!! tip "Generating Sample Data"
        If you just want to demo Tomato with loads of prefilled sample data, run
        this command,

        ```bash
        docker compose run --rm app ./manage.py prefill_sample_data --created-by tomato
        ```

    Now bring up the server,

    ```bash
    docker compose up
    ```

    In your web browser, navigate to <http://localhost:8000>.

    The default username and password, which you can _(and should)_ change will
    be,

    | Username | Password |
    | :------: | :------: |
    | `tomato` | `tomato` |

    To stop the server, press ++ctrl+c++.


=== "Production Deployment"

    Open up the `.env` file you just created using your favorite text editor.
    Take action on the following,

    1. Set `DEBUG` flag to `0` &mdash; which tells Tomato to run in production
       mode.
    2. Either set `EMAIL_EXCEPTIONS_ENABLED` to `0` to disable emails, or set it
       to `1` and edit all `EMAIL_*` values to point to a properly configured
       SMTP server
    3. `DOMAIN_NAME` is set to a domain name that resolves to a publicly
       accessible IP address of the server.

    === "Setting Up an Nginx Container"

        It's **highly recommended** that you use the production [Nginx]
        container, which automatically generates an SSL certificate for you and
        takes care of reverse proxying into Tomato for you.

        To do so, first make sure of the following in your `.env` file,

        * `CERTBOT_EMAIL` is set to a valid email.

        !!! danger "`DOMAIN_NAME` and `CERTBOT_EMAIL` **must** be properly set!"
            If you don't set `DOMAIN_NAME` and `CERTBOT_EMAIL` properly as described
            above, the production Nginx container will not  start correctly. This
            is a requirement of [Certbot], the underlying component that automatically
            generates an SSL certificate for you.

        Now, create a symbolic link for the Nginx Compose overrides,

        ```bash
        ln -s docker-compose.nginx.yml docker-compose.overrides.yml
        ```

    === "Reverse Proxying Yourself"

        !!! danger "Reverse proxying yourself is **NOT** recommended."
            This is method of setting up Tomato on your server is unsupported,
            and not recommended. However, here is a guide for non-standard
            setups, or if you don't have port `80` and `443` available on your
            server.

        Create and edit a file named `docker-compose.overrides.yml`,

        ```yaml title="server/docker-compose.overrides.yml"
        services:
          app:
            ports:
              # Replace 1234 with any port you like
              - 127.0.0.1:1234:8000
        ```

        Then in your web server, reverse proxy into port you chose.

        If you're using Nginx, you can use configuration like this,

        ```nginx title="sample.conf"
        server {
          # ... other Nginx config here

          location /assets/ {
            # Replace /home/user/tomato with the path you cloned the repository
            alias /home/user/tomato/server/serve/assets/;
          }

          location /static/ {
            # Replace /home/user/tomato here too
            alias /home/user/tomato/server/serve/static/;
          }

          location / {
            proxy_set_header Host $http_host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            # Replace 1234 with the port you chose above
            proxy_pass http://127.0.0.1:1234;
          }
        }
        ```

    Pull the containers (or build them by instead executing `#!bash docker compose build`),

    ```bash
    docker compose pull
    ```

    Create an admin user by following the instructions after typing this at the
    command line,

    ```bash
    docker compose run --rm app ./manage.py createsuperuser
    ```

    Now bring up the server,

    ```bash
    docker compose up -d
    ```

    Head over to `https://<DOMAIN_NAME>/` in your web browser.

    To stop the server,

    ```bash
    docker compose down
    ```

    Tomato will be configured to auto-restart on crashes, and and system
    start-up.

[certbot]: https://certbot.eff.org/
[compose]: https://docs.docker.com/compose/
[django]: https://www.djangoproject.com/
[docker-desktop]: https://www.docker.com/products/docker-desktop
[docker]: https://www.docker.com/
[nginx]: https://www.nginx.com/
[tomato-git]: https://github.com/dtcooper/tomato
[python]: https://www.python.org/
