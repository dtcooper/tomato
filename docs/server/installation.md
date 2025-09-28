---
title: Installation
---

## Step by Step

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
    ln -s compose.dev.yml compose.override.yml
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
    4. Set `TOMATO_VERSION` to the specific release tag you want to use, ie
       `v0.0.4`.

    === "With Included Nginx Container"

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

        The nginx container is now included in the default installation, so no
        further action need be taken.

    === "Reverse Proxying Yourself"

        !!! danger "Reverse proxying yourself is NOT recommended."
            This is method of setting up Tomato on your server is unsupported,
            and not recommended. However, here is a guide for non-standard
            setups, or if you don't have port `80` and `443` available on your
            server and still want to server Tomato on the default web ports.

        Create and edit a file named `compose.override.yml`,

        ```yaml title="server/compose.override.yml" hl_lines="4-6 9-10 13-14"
        services:
          logs:
            ports:
              # Replace 6666 with any port you like (logs server)
              # WARNING: should NOT be accessible, mark "internal;" with Nginx
              - 127.0.0.1:6666:8000
          api:
            ports:
              # Replace 7777 with any port you like (api server)
              - 127.0.0.1:7777:8000
          app:
            ports:
              # Replace 8888 with any port you like (app server)
              - 127.0.0.1:8888:8000
          nginx:
            profiles:
              - do-not-start
        ```

        Then in your web server, reverse proxy into the ports you chose.

        If you're using Nginx, you can use this configuration snippet,

        ```nginx title="tomato.conf" hl_lines="2 7-8 12-13 24-25 37-38 45-46"
        server {
          # ... your other Nginx config goes here

          client_max_body_size 25M;

          location /assets/ {
            # Replace /home/user/tomato with the path you cloned the repository
            alias /home/user/tomato/server/serve/assets/;
          }

          location /static/ {
            # Replace /home/user/tomato here too
            alias /home/user/tomato/server/serve/static/;
          }

          location /_internal/server-logs {
            internal;
            proxy_set_header Host $http_host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_buffering off;
            proxy_cache off;
            # Replace 6666 with the port you chose above (logs server)
            proxy_pass http://127.0.0.1:6666/server-logs;
          }

          location /api/ {
            proxy_http_version 1.1;
            proxy_set_header Connection $connection_upgrade;
            proxy_set_header Host $http_host;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Real-IP $remote_addr;
            # Replace 7777 with the port you chose above (api server)
            proxy_pass http://127.0.0.1:7777;
          }

          location / {
            proxy_set_header Host $http_host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            # Replace 8888 with the port you chose above (app server)
            proxy_pass http://127.0.0.1:8888;
          }
        }
        ```

        !!! warning "Logs server should be private!"

            Access to the logs server should be private. For example, Tomato uses
            the Nginx feature
            [X-Accel-Redirect](https://www.nginx.com/resources/wiki/start/topics/examples/x-accel/#x-accel-redirect)
            to protect it. The Nginx configuration snippet functions correctly
            in this regard, but if you're using another web server, take care to
            configure it appropriately.

    Checkout the release tag you want to use and pull the containers (or build
    them by instead executing `#!bash docker compose build`),

    ```bash
    git checkout v0.0.4
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
[docker-desktop]: https://www.docker.com/products/docker-desktop
[docker]: https://www.docker.com/
[nginx]: https://www.nginx.com/
[tomato-git]: https://github.com/dtcooper/tomato
