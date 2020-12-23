from django import template

register = template.Library()


@register.filter
def problem_color(problem, user):
    if user.has_attempted(problem):
        if user.has_solved(problem):
            return "success"
        else:
            return "warning"
    else:
        return "light"
