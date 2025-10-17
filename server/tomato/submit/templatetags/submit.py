import json
import logging
import string
import textwrap

from django import template
from django.conf import settings
from django.contrib import messages
from django.utils.html import escape, format_html
from django.utils.safestring import mark_safe

from constance import config

from ..views import resolve_url


logger = logging.getLogger(__name__)
register = template.Library()

CONSTANTS_FILE = settings.PROJECT_DIR / "tomato" / "submit" / "content_block_defaults.json"


@register.simple_block_tag(takes_context=True)
def confblock(context, content, name):
    name = name.upper()
    content = textwrap.dedent(content.replace("\t", "  ")).strip()

    config_name = f"USER_SUBMIT_CONTENT_BLOCK_{name}"
    config_entry = settings.CONSTANCE_CONFIG.get(config_name)
    if config_entry is None:
        logger.warning(f"Config {config_name} doesn't exist in constance settings, but is referred to in a template!")
        if settings.DEBUG:
            request = context.get("request")
            if request is not None:
                messages.warning(
                    request,
                    format_html(
                        "Invalid content block name (<code>{}</code>). Set <code>{}</code> in constance config.",
                        name,
                        config_name,
                    ),
                )
        else:
            raise template.TemplateSyntaxError(
                f"Invalid user submission content block name ({name}). Set {config_name} in constance settings."
            )
        block_html = content

    else:
        if settings.DEBUG and content:
            default_config_value = config_entry[0]
            if default_config_value != content:
                logger.warning(f"Constance config {config_name} has an updated template value. Overwriting it.")
                request = context.get("request")
                if request is not None:
                    messages.info(
                        request,
                        format_html(
                            "Constance config <code>{}</code> had an updated template value. Overwrote it.", config_name
                        ),
                    )
                with open(CONSTANTS_FILE, "r") as f:
                    defaults = json.load(f)
                defaults[config_name] = content

                with open(CONSTANTS_FILE, "w") as f:
                    json.dump(defaults, f, indent=2, sort_keys=True)
                    f.write("\n")

                setattr(config, config_name, content)
        block_html = getattr(config, config_name)

    block_template = string.Template(block_html)
    block_context = {k: escape(v) for k, v in context.flatten().items()}
    for key in block_template.get_identifiers():
        if key.startswith("CONTENT_BLOCK_"):
            block_context[key] = confblock(context, "", key.removeprefix("CONTENT_BLOCK_"))
    return mark_safe(block_template.safe_substitute(block_context))


@register.simple_tag(takes_context=True)
def submit_url(context, url_name, *args, **kwargs):
    return resolve_url(context["request"], url_name, *args, **kwargs)
