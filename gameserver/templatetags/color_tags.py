from django import template

from ..models import Problem

register = template.Library()


@register.filter
def contest_color(contest):
    if not contest.is_started:
        return "info"
    elif contest.is_ongoing:
        return "success"
    else:
        return ""


@register.filter
def problem_status(problem, user):
    if (
        isinstance(problem, Problem)
        and not problem.is_public
        and not (user.current_contest and user.current_contest.contest.has_problem(problem))
    ):
        return "private"
    elif user.has_firstblooded(problem):
        return "firstblood"
    elif user.has_solved(problem):
        return "solved"
    elif user.has_attempted(problem):
        return "attempted"
    else:
        return "unsolved"
