from django import template
from django.utils.safestring import mark_safe
from django.utils.html import format_html, format_html_join
from django.shortcuts import reverse
from gameserver import models
import django.contrib.humanize.templatetags.humanize as humanize

register = template.Library()


@register.filter
def user_url(username):
    return reverse("user_detail", args=[username])


@register.filter
def user(username, postfix=""):
    user_obj = models.User.objects.get(username=username)
    return format_html(
        '<a href="{0}{1}">{2}</a>', mark_safe(user_obj.get_absolute_url()), mark_safe(postfix), user_obj.username
    )


@register.filter
def users(usernames, postfix=""):
    user_objs = models.User.objects.filter(pk__in=usernames)
    return format_html_join(
        ', ', '<a href="{0}{1}">{2}</a>',
        ((user_obj.get_absolute_url(), postfix, user_obj.username) for user_obj in user_objs),
    )


@register.filter
def problem_url(slug):
    return reverse("problem_detail", args=[slug])


@register.filter
def problem(slug, postfix=""):
    url = problem_url(slug)
    problem = models.Problem.objects.get(slug=slug)
    return format_html(
        '<a href="{0}{1}">{2}</a>', mark_safe(url), mark_safe(postfix), problem.name
    )


@register.filter
def submission_url(pk):
    return reverse("submission_detail", args=[pk])


@register.filter
def submission(pk, postfix=""):
    url = submission_url(pk)
    return format_html(
        '<a href="{0}{1}">#{2}</a>', mark_safe(url), mark_safe(postfix), str(pk)
    )


@register.filter
def comment_url(pk):
    return reverse("comment", args=[pk])


@register.filter
def comment(pk, postfix=""):
    url = comment_url(pk)
    return format_html(
        '<a href="{0}{1}">#{2}</a>', mark_safe(url), mark_safe(postfix), str(pk)
    )


def comment_info(comment_obj):
    parent_type = comment_obj.parent_content_type.model
    if parent_type == "problem":
        parent_url = problem(comment_obj.parent.slug)
    elif parent_type == "submission":
        parent_url = "Submission " + submission(comment_obj.parent.pk)
    elif parent_type == "user":
        parent_url = user(comment_obj.parent.username)
    elif parent_type == "comment":
        parent_url = "Comment " + comment(comment_obj.parent.pk)
    elif parent_type == "blogpost":
        parent_url = post(comment_obj.parent.slug)
    elif parent_type == "organization":
        parent_url = organization(comment_obj.parent.slug)
    else:
        parent_url = "unknown."
    comment_url = comment(comment_obj.pk)
    author_url = user(comment_obj.author.username)
    comment_date = humanize.naturaltime(comment_obj.created_date)
    return comment_url, author_url, comment_date, parent_url


@register.filter
def comment_html_nodate(comment_obj):
    comment_url, author_url, comment_date, parent_url = comment_info(comment_obj)
    return format_html("{0}: {1} commented on {2}", comment_url, author_url, parent_url)


@register.filter
def comment_html(comment_obj):
    comment_url, author_url, comment_date, parent_url = comment_info(comment_obj)
    return format_html(
        "{0}: {1} commented {2} on {3}",
        comment_url,
        author_url,
        comment_date,
        parent_url,
    )


@register.filter
def post_url(slug):
    return reverse("blog_post", args=[slug])


@register.filter
def post(slug, postfix=""):
    url = post_url(slug)
    post_obj = models.BlogPost.objects.get(slug=slug)
    return format_html(
        '<a href="{0}{1}">{2}</a>', mark_safe(url), mark_safe(postfix), post_obj.title
    )


@register.filter
def organization_url(slug):
    return reverse("organization_detail", args=[slug])


@register.filter
def organization(slug, postfix=""):
    url = organization_url(slug)
    organization_obj = models.Organization.objects.get(slug=slug)
    return format_html(
        '<a href="{0}{1}">{2}</a>',
        mark_safe(url),
        mark_safe(postfix),
        organization_obj.name,
    )
