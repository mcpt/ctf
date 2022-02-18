from django import template

register = template.Library()


@register.filter
def startswith(string, substring):
    return string.startswith(substring)


@register.filter
def split(string, split_char=" "):
    return string.split(split_char)


@register.filter
def strfdelta(tdelta, fmt="{t_hours}:{minutes}:{seconds}"):
    days = tdelta.days
    hours = tdelta.seconds // 3600
    t_hours = days * 24 + hours
    minutes = (tdelta.seconds // 60) % 60
    t_minutes = t_hours * 60 + minutes
    seconds = tdelta.seconds % 60
    t_seconds = t_minutes * 60 + seconds

    kwargs = {
        "days": days,
        "hours": hours,
        "t_hours": t_hours,
        "minutes": f"{minutes:02}",
        "t_minutes": f"{t_minutes:02}",
        "seconds": f"{seconds:02}",
        "t_seconds": f"{t_seconds:02}",
    }

    return fmt.format(**kwargs)
