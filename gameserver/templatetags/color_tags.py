from django import template

register = template.Library()


@register.filter
def problem_color(problem, user):
    entity = user
    if user.current_contest is not None:
        entity = user.current_contest
    if entity.has_solved(problem):
        return "success"
    else:
        return "light"


@register.filter
def contest_color(contest):
    if not contest.is_started():
        return "warning"
    elif contest.is_ongoing():
        return "primary"
    else:
        return "success"
