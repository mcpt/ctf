from django import template

register = template.Library()


@register.filter
def problem_color(problem, user):
    if user.has_solved(problem):
        return "success"
    if user.has_attempted(problem):
        return "warning"
    else:
        return "unsolved"


@register.filter
def contest_problem_color(contest_problem, user):
    if user.has_solved(contest_problem):
        return "success"
    if user.has_attempted(contest_problem):
        return "warning"
    else:
        return "unsolved"


@register.filter
def contest_color(contest):
    if not contest.is_started():
        return "warning"
    elif contest.is_ongoing():
        return "primary"
    else:
        return "success"
