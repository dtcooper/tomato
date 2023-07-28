---
title: Tomato Backend Server
---

# The Tomato Backend Server

The backend server is written in [Python]'s [Django web framework][django],
heavily leveraging its automatic admin interface.

To get started, you'll have to [install the server](installation.md) first.

## Configuration

{% for section, config_names in DJANGO_SETTINGS.CONSTANCE_CONFIG_FIELDSETS.items() %}
### {{ section }}

!!! info ""
    {% for name in config_names %}
    {% with config=DJANGO_SETTINGS.CONSTANCE_CONFIG[name] %}
    {% with default=config[0], description=config[1], type=config[2] %}
    `{{ name }}` --- **Type: {{ get_constance_config_type(default, type) }}**
    :   {{ description }}

        Default: `{{ get_constance_config_default(name, default) }}`
    {% endwith %}
    {% endwith %}
    {% endfor %}
{% endfor %}

[certbot]: https://certbot.eff.org/
[compose]: https://docs.docker.com/compose/
[django]: https://www.djangoproject.com/
[docker-desktop]: https://www.docker.com/products/docker-desktop
[docker]: https://www.docker.com/
[nginx]: https://www.nginx.com/
[tomato-git]: https://github.com/dtcooper/tomato
[python]: https://www.python.org/
