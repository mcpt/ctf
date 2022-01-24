import django.contrib.humanize.templatetags.humanize as humanize
from django import template
from django.shortcuts import reverse
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from gameserver import models

register = template.Library()


@register.filter
def user(username, suffix=""):
    user_obj = models.User.objects.get(username=username)
    return format_html(
        '<a href="{0}{1}">{2}</a>',
        mark_safe(user_obj.get_absolute_url()),
        mark_safe(suffix),
        user_obj,
    )


@register.filter
def users(usernames, suffix=""):
    user_objs = models.User.objects.filter(pk__in=usernames)
    return format_html_join(
        ", ",
        '<a href="{0}{1}">{2}</a>',
        ((user_obj.get_absolute_url(), suffix, user_obj) for user_obj in user_objs),
    )


@register.filter
def userst(usernames, suffix=""):
    user_objs = models.User.objects.filter(pk__in=usernames)
    return format_html_join(
        ", ",
        "{0}",
        ((user_obj,) for user_obj in user_objs),
    )


@register.filter
def problem(slug, suffix=""):
    problem_obj = models.Problem.objects.get(slug=slug)
    return format_html(
        '<a href="{0}{1}">{2}</a>',
        mark_safe(problem_obj.get_absolute_url()),
        mark_safe(suffix),
        problem_obj,
    )


@register.filter
def comment(pk, suffix=""):
    comment_obj = models.Comment.objects.get(pk=pk)
    return format_html(
        '<a href="{0}{1}">{2}</a>',
        mark_safe(comment_obj.get_absolute_url()),
        mark_safe(suffix),
        comment_obj,
    )


def comment_info(comment_obj):
    parent_type = comment_obj.parent_content_type.model
    if parent_type == "problem":
        parent_url = problem(comment_obj.parent.slug)
    elif parent_type == "user":
        parent_url = user(comment_obj.parent.username)
    elif parent_type == "comment":
        parent_url = comment(comment_obj.parent.pk)
    elif parent_type == "blogpost":
        parent_url = post(comment_obj.parent.slug)
    elif parent_type == "organization":
        parent_url = organization(comment_obj.parent.slug)
    elif parent_type == "contest":
        parent_url = contest(comment_obj.parent.slug)
    elif parent_type == "contestparticipation":
        parent_url = contest_participation(comment_obj.parent.pk)
    else:
        parent_url = "unknown."
    comment_url = comment(comment_obj.pk)
    author_url = user(comment_obj.author.username)
    comment_date = humanize.naturaltime(comment_obj.date_created)
    return comment_url, author_url, comment_date, parent_url


@register.filter
def comment_html_nodate(comment_obj):
    comment_url, author_url, comment_date, parent_url = comment_info(comment_obj)
    return format_html("{0} commented on {1}", author_url, parent_url)


@register.filter
def comment_html(comment_obj):
    comment_url, author_url, comment_date, parent_url = comment_info(comment_obj)
    return format_html(
        "{0} commented {1} on {2}",
        author_url,
        comment_date,
        parent_url,
    )


@register.filter
def comment_html_short(comment_obj):
    comment_url, author_url, comment_date, parent_url = comment_info(
        comment_obj
    )
    return format_html(
        "{0} → {1}", author_url, parent_url
    )


@register.filter
def post(slug, suffix=""):
    post_obj = models.BlogPost.objects.get(slug=slug)
    return format_html(
        '<a href="{0}{1}">{2}</a>',
        mark_safe(post_obj.get_absolute_url()),
        mark_safe(suffix),
        post_obj,
    )


@register.filter
def organization(slug, suffix=""):
    organization_obj = models.Organization.objects.get(slug=slug)
    return format_html(
        '<a href="{0}{1}">{2}</a>',
        mark_safe(organization_obj.get_absolute_url()),
        mark_safe(suffix),
        organization_obj,
    )


@register.filter
def team(pk, suffix=""):
    team_obj = models.Team.objects.get(pk=pk)
    return format_html(
        '<a href="{0}{1}">{2}</a>',
        mark_safe(team_obj.get_absolute_url()),
        mark_safe(suffix),
        team_obj,
    )


@register.filter
def contest(slug, suffix=""):
    contest_obj = models.Contest.objects.get(slug=slug)
    return format_html(
        '<a href="{0}{1}">{2}</a>',
        mark_safe(contest_obj.get_absolute_url()),
        mark_safe(suffix),
        contest_obj,
    )


@register.filter
def contest_participation(pk, suffix=""):
    contest_participation_obj = models.ContestParticipation.objects.get(pk=pk)
    return format_html(
        '<a href="{0}{1}">{2}</a>',
        mark_safe(contest_participation_obj.get_absolute_url()),
        mark_safe(suffix),
        contest_participation_obj,
    )
