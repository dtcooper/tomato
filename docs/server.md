---
title: Server
---

# The Tomato Backend Server

The backend server is written in [Python][python]'s [Django web framework][django],
heavily leveraging its [automatic admin interface][django-admin].

## Installation

Follow these steps to get started.

### Installing Docker

You'll need to install [Docker][docker] to get started (which now comes preloaded
with [Compose][compose]).

=== "Linux"

    At the command line, execute the following to install Docker,

    ```bash
    curl -fsSL https://get.docker.com | sh
    ```


=== "macOS"

    Install Docker Desktop by
    [following the instructions here][docker-desktop].


[compose]: https://docs.docker.com/compose/
[django-admin]: https://docs.djangoproject.com/en/4.1/ref/contrib/admin/
[django]: https://www.djangoproject.com/
[docker-desktop]: https://www.docker.com/products/docker-desktop
[docker]: https://www.docker.com/
[python]: https://www.python.org/

### Run & Build

Here are the instructions to install Tomato in both development mode and
production mode.
