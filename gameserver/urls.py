from django.urls import path, include

from . import views

urlpatterns = [
    path("api", include("gameserver.api.urls")),
    path("", views.Index.as_view(), name="index"),
    path("post/<slug:slug>", views.BlogPost.as_view(), name="blog_post"),
    path("writeup/<slug:slug>", views.Writeup.as_view(), name="writeup"),
    path(
        "accounts/profile",
        views.UserDetailRedirect.as_view(),
        name="user_detail_redirect",
    ),
    path("problems/", views.ProblemList.as_view(), name="problem_list"),
    path(
        "problem/<slug:slug>",
        views.ProblemDetail.as_view(),
        name="problem_detail",
    ),
    path(
        "problem/<slug:slug>/challenge", views.ProblemChallenge.as_view(), name="problem_challenge"
    ),
    path(
        "problem/<slug:slug>/submissions",
        views.ProblemSubmissionList.as_view(),
        name="problem_submission_list",
    ),
    path("users/", views.UserList.as_view(), name="user_list"),
    path("user/<str:slug>", views.UserDetail.as_view(), name="user_detail"),
    path(
        "user/<str:slug>/submissions",
        views.UserSubmissionList.as_view(),
        name="user_submission_list",
    ),
    path(
        "organizations/",
        views.OrganizationList.as_view(),
        name="organization_list",
    ),
    path(
        "organization/<str:slug>",
        views.OrganizationDetail.as_view(),
        name="organization_detail",
    ),
    path(
        "organization/<str:slug>/request",
        views.OrganizationRequest.as_view(),
        name="organization_request",
    ),
    path(
        "organization/<str:slug>/join",
        views.OrganizationJoin.as_view(),
        name="organization_join",
    ),
    path(
        "organization/<str:slug>/leave",
        views.OrganizationLeave.as_view(),
        name="organization_leave",
    ),
    path("teams/", views.TeamList.as_view(), name="team_list"),
    path("teams/create", views.TeamCreate.as_view(), name="team_create"),
    path("team/<int:pk>", views.TeamDetail.as_view(), name="team_detail"),
    path("team/<int:pk>/edit", views.TeamEdit.as_view(), name="team_edit"),
    path("team/<int:pk>/leave", views.TeamLeave.as_view(), name="team_leave"),
    path("contests/", views.ContestList.as_view(), name="contest_list"),
    path(
        "contest/<str:slug>",
        views.ContestDetail.as_view(),
        name="contest_detail",
    ),
    path(
        "contest/<str:slug>/leave",
        views.ContestLeave.as_view(),
        name="contest_leave",
    ),
    path(
        "contest/<str:slug>/problems",
        views.ContestProblemList.as_view(),
        name="contest_problem_list",
    ),
    path(
        "contest/<str:slug>/submissions",
        views.ContestSubmissionList.as_view(),
        name="contest_submission_list",
    ),
    path(
        "contest/<str:slug>/scoreboard",
        views.ContestScoreboard.as_view(),  # cache for 5m
        name="contest_scoreboard",
    ),
    path(
        "contest/<str:contest_slug>/scoreboard/organization/<str:org_slug>",
        views.ContestOrganizationScoreboard.as_view(),
        name="contest_organization_scoreboard",
    ),
    path(
        "participation/<int:pk>",
        views.ContestParticipationDetail.as_view(),
        name="contest_participation_detail",
    ),
    path(
        "participation/<int:pk>/submissions",
        views.ContestParticipationSubmissionList.as_view(),
        name="contest_participation_submission_list",
    ),
    path("accounts/profile/edit", views.UserEdit.as_view(), name="user_edit"),
    path("submissions/", views.SubmissionList.as_view(), name="submission_list"),
    path("comment/<int:pk>", views.Comment.as_view(), name="comment"),
    path(
        "<str:parent_type>/<slug:parent_id>/add_comment",
        views.add_comment,
        name="add_comment",
    ),
]
