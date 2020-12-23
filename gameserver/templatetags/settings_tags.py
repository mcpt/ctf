from django import template
import pCTF.settings as settings

register = template.Library()


@register.simple_tag
def settings_value(name):
    return getattr(settings, name)
