from django import template

from ..submit.views import resolve_url

register = template.Library()

@register.simple_tag(takes_context=True)
def submit_url(context, view_name, *args, **kwargs):
    return resolve_url(context["request"], view_name, *args, **kwargs)
