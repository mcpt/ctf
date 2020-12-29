import pCTF.settings as settings
from django import template

register = template.Library()


@register.simple_tag
def settings_value(name):
    return getattr(settings, name)
