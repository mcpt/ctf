import hashlib
import urllib
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def gravatar_url(email, size=40):
    email = email.encode("utf-8")
    return "https://www.gravatar.com/avatar/%s?%s" % (
        hashlib.md5(email.lower()).hexdigest(),
        urllib.parse.urlencode({"d": "retro", "s": str(size)}),
    )


@register.filter
def gravatar(email, size=40):
    url = gravatar_url(email, size)
    return mark_safe('<img src="%s" width="%d" height="%d">' % (url, size, size))
