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

[django]: https://www.djangoproject.com/
[python]: https://www.python.org/
