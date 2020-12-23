from django.urls import path

from . import views

urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    path("post/<slug:slug>", views.BlogPost.as_view(), name="blog_post"),
    path("accounts/profile", views.UserDetailRedirect.as_view(), name="user_detail_redirect"),
    path("problems/", views.ProblemList.as_view(), name="problem_list"),
    path("problem/<slug:slug>", views.ProblemDetail.as_view(), name="problem_detail"),
    path("problem/<slug:slug>/solves", views.ProblemSolves.as_view(), name="problem_solves"),
    path("users/", views.UserList.as_view(), name="user_list"),
    path("user/<str:slug>", views.UserDetail.as_view(), name="user_detail"),
    path("user/<str:slug>/solves", views.UserSolves.as_view(), name="user_solves"),
    path("organizations/", views.OrganizationList.as_view(), name="organization_list"),
    path("organization/<str:slug>", views.OrganizationDetail.as_view(), name="organization_detail"),
    path("organization/<str:slug>/members", views.OrganizationMembers.as_view(), name="organization_members"),
    path("organization/<str:slug>/request", views.OrganizationRequest.as_view(), name="organization_request"),
    path("organization/<str:slug>/join", views.OrganizationJoin.as_view(), name="organization_join"),
    path("organization/<str:slug>/leave", views.OrganizationLeave.as_view(), name="organization_leave"),
    path("teams/", views.TeamList.as_view(), name="team_list"),
    path("teams/create", views.TeamCreate.as_view(), name="team_create"),
    path("team/<int:pk>", views.TeamDetail.as_view(), name="team_detail"),
    path("team/<int:pk>/edit", views.TeamEdit.as_view(), name="team_edit"),
    path("team/<int:pk>/leave", views.TeamLeave.as_view(), name="team_leave"),
    path("accounts/profile/edit", views.UserEdit.as_view(), name="user_edit"),
    path("solves/", views.SolveList.as_view(), name="solve_list"),
    path("comment/<int:pk>", views.Comment.as_view(), name="comment"),
    path("<str:parent_type>/<slug:parent_id>/add_comment", views.add_comment, name="add_comment"),
]
