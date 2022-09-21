---
title: Server
---

# The Tomato Backend Server

The backend server is written in [Python]'s [Django web framework][django],
heavily leveraging its [automatic admin interface][django-admin].

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

    Now bring up the server,

    ```bash
    docker compose up
    ```

    In your web browser, navigate to <http://localhost:8000>.

    The default username and password, which you can _(and should)_ change will
    be `tomato` and `tomato`.

    To stop the server, press ++ctrl+c++.


=== "Production Deployment"

    Open up the `.env` file you just created using your favourite text editor.
    Take action on the following,

    1. Set `DEBUG` flag to `0` &mdash; which tells Tomato to run in production
       mode.
    2. `DOMAIN_NAME` is set to a domain name that resolves to a publicly
       accessible IP address of the server.
    3. `CERTBOT_EMAIL` is set to a valid email.
    4. Either set `EMAIL_EXCEPTIONS_ENABLED` to `0` to disable emails, or set it
       to `1` and edit all `EMAIL_*` values point to a properly configured SMTP
       server

    !!! danger "`DOMAIN_NAME` and `CERTBOT_EMAIL` **must** be properly set!"

        If you don't set `DOMAIN_NAME` and `CERTBOT_EMAIL` properly as described
        above, the production [Nginx] container will not  start correctly. This
        is a requirement of [Certbot], the underlying component that automatically
        generates an SSL certificate for you.

    Now, create a symbolic link for the production [Compose] overrides,

    ```bash
    ln -s docker-compose.prod.yml docker-compose.overrides.yml
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


[certbot]: https://certbot.eff.org/
[compose]: https://docs.docker.com/compose/
[django-admin]: https://docs.djangoproject.com/en/4.1/ref/contrib/admin/
[django]: https://www.djangoproject.com/
[docker-desktop]: https://www.docker.com/products/docker-desktop
[docker]: https://www.docker.com/
[nginx]: https://www.nginx.com/
[tomato-git]: https://github.com/dtcooper/tomato
[python]: https://www.python.org/
