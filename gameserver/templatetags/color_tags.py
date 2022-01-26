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
        return "info"
    elif contest.is_ongoing():
        return "success"
    else:
        return ""


@register.filter
def problem_status(problem, user):
    if problem.is_private:
        return "private"
    if user.has_solved(problem):
        return "solved"
    if user.has_attempted(problem):
        return "attempted"
    else:
        return "unsolved"


@register.filter
def submission_status(submission):
    if submission.is_firstblood():
        return "firstblood"
    elif submission.is_correct:
        return "solved"
    else:
        return "attempted"


@register.filter
def contest_problem_status(contest_problem, user):
    if user.has_solved(contest_problem.problem):
        return "solved"
    if user.has_attempted(contest_problem.problem):
        return "attempted"
    else:
        return "unsolved"
