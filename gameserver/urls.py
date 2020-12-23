from django.urls import path

from . import views

urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    path("post/<slug:slug>", views.BlogPost.as_view(), name="blog_post"),
    path("accounts/profile", views.UserDetailRedirect.as_view(), name="user_detail_redirect"),
    path("problems/", views.ProblemList.as_view(), name="problem_list"),
    path("problem/<slug:slug>", views.ProblemDetail.as_view(), name="problem_detail"),
    path("problem/<slug:slug>/submissions", views.ProblemAllSubmissions.as_view(), name="problem_all_submissions"),
    path("problem/<slug:slug>/rank", views.ProblemBestSubmissions.as_view(), name="problem_best_submissions"),
    path("users/", views.UserList.as_view(), name="user_list"),
    path("user/<str:slug>", views.UserDetail.as_view(), name="user_detail"),
    path("user/<str:slug>/submissions", views.UserSubmissions.as_view(), name="user_submissions"),
    path("organizations/", views.OrganizationList.as_view(), name="organization_list"),
    path("organization/<str:slug>", views.OrganizationDetail.as_view(), name="organization_detail"),
    path("organization/<str:slug>/members", views.OrganizationMembers.as_view(), name="organization_members"),
    path("organization/<str:slug>/request", views.OrganizationRequest.as_view(), name="organization_request"),
    path("organization/<str:slug>/join", views.OrganizationJoin.as_view(), name="organization_join"),
    path("organization/<str:slug>/leave", views.OrganizationLeave.as_view(), name="organization_leave"),
    path("accounts/profile/edit", views.UserEdit.as_view(), name="user_edit"),
    path("submissions/", views.SubmissionList.as_view(), name="submission_list"),
    path("submission/<int:pk>", views.SubmissionDetail.as_view(), name="submission_detail"),
    path("comment/<int:pk>", views.Comment.as_view(), name="comment"),
    path("<str:parent_type>/<slug:parent_id>/add_comment", views.add_comment, name="add_comment"),
]
