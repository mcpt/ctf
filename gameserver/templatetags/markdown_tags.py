import re

import bleach.sanitizer as sanitizer
import mistune
from django import template
from django.conf import settings
from django.contrib.sites.models import Site
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

from . import bleach_allowlist

render = mistune.create_markdown()

register = template.Library()

bodge_pattern = re.compile(f"\[([^\]]*)\]\(/")


def bodge_replace(match):
    return f"[{match.group(1)}]({settings.ROOT}/"


# https://github.com/mozilla/bleach/blob/main/bleach/sanitizer.py#L13

cleaner = sanitizer.Cleaner(
    tags=[
        *sanitizer.ALLOWED_TAGS,
        "br",
        "p",
        "img",
        *["h{}".format(i) for i in range(1, 7)],
        "hr",
        "iframe",
        "code",
    ],
    attributes={
        **sanitizer.ALLOWED_ATTRIBUTES,
        "iframe": ["src", "frameborder", "class"],
        "img": ["alt", "src", "style", "class"],
    },
    styles=[*bleach_allowlist.all_styles, "markdown-embed"],
    protocols=[
        "https",
        "mailto",
    ],
    strip=True,
)


@register.filter
@stringfilter
def markdown(field_name):
    return mark_safe(cleaner.clean(render(re.sub(bodge_pattern, bodge_replace, field_name))))
