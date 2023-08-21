import decimal
import sys
from unittest.mock import Mock


_django_settings = None
TYPES_TO_STRING = {
    int: "Numeric",
    decimal.Decimal: "Numeric",
    bool: "Boolean (true or false)",
    str: "String",
}
TYPE_HINTS_TO_STRING = {
    "audio_bitrate": "32kbps through 320kbps",
    "ui_modes": "Simple, standard, and/or advanced mode",
}


def get_django_settings():
    global _django_settings
    if _django_settings is None:
        sys.path.append("../server")
        # Mock out imports
        sys.modules.update(
            {
                "django.core.exceptions": Mock(ValidationError=None),
                "django.utils.safestring": Mock(mark_safe=lambda s: s),
                "environ": Mock(Env=lambda: Mock(bool=lambda *args, **kwargs: False), read_env=lambda s: None),
            }
        )
        from tomato import settings

        _django_settings = settings
    return _django_settings


def get_constance_config_type(default, type_hint=None):
    if type_hint is None or type_hint not in TYPE_HINTS_TO_STRING:
        return TYPES_TO_STRING[type(default)]
    else:
        return TYPE_HINTS_TO_STRING[type_hint]


def get_constance_config_default(name, default):
    if isinstance(default, decimal.Decimal):
        default = int(default)

    if name == "AUDIO_BITRATE":
        return f"{default}kbps"
    elif name == "UI_MODES":
        return "Simple & standard mode"
    return repr(default)


def define_env(env):
    env.variables["DJANGO_SETTINGS"] = get_django_settings()
    # with open("LICENSE", "r") as license:
    #     env.variables["LICENSE"] = license.read()
    # with open(".default.env", "r") as default_env:
    #     env.variables["DEFAULT_ENV"] = default_env.read()
    env.macro(get_constance_config_type)
    env.macro(get_constance_config_default)
