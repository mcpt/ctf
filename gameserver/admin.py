from adminsortable2.admin import SortableAdminBase, SortableInlineAdminMixin
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.flatpages.admin import FlatPageAdmin
from django.contrib.flatpages.models import FlatPage
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from . import models
from .models import Submission, ContestSubmission
from .utils.actions import *

User = get_user_model()


class ProblemFileInline(admin.StackedInline):
    fields = ["artifact"]
    model = models.ProblemFile
    extra = 0


class ProblemAdmin(admin.ModelAdmin):
    fields = [
        "name",
        "slug",
        "author",
        "testers",
        "organizations",
        "description",
        "summary",
        "points",
        "flag",
        "log_submission_content",
        "problem_group",
        "problem_type",
        "challenge_spec",
        "is_public",
        "firstblood",
    ]
    readonly_fields = ["firstblood"]
    inlines = [
        ProblemFileInline,
    ]
    list_display = [
        "name",
        "slug",
        "get_authors",
        "points",
        "is_public",
    ]
    list_filter = [
        "is_public",
        "problem_type",
        "problem_group",
        "author",
    ]
    search_fields = [
        "name",
        "slug",
    ]

    def has_view_permission(self, request, obj=None):
        if request.user.has_perm("gameserver.view_problem"):
            if obj is None:
                return True
            else:
                return obj.is_editable_by(request.user)
        return False

    def has_change_permission(self, request, obj=None):
        if request.user.has_perm("gameserver.change_problem"):
            if obj is None:
                return True
            else:
                return obj.is_editable_by(request.user)
        return False

    def get_queryset(self, request):
        return models.Problem.get_editable_problems(request.user)

    def get_readonly_fields(self, request, obj=None):
        fields = self.readonly_fields
        if request.user.is_superuser:
            return fields
        if request.user.is_superuser or request.user.has_perm(
            "gameserver.change_problem_visibility"
        ):
            return fields
        fields += ("is_public",)
        return fields

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "author":
            kwargs["queryset"] = models.User.objects.filter(is_staff=True).order_by("username")
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    @admin.display(description="Authors")
    def get_authors(self, obj):
        return ", ".join([u.username for u in obj.author.all()])


class SubmissionAdmin(admin.ModelAdmin):
    list_display = [
        "problem",
        "date_created",
        "is_correct",
        "display_firstblooded",
    ]
    list_filter = [
        "problem__points",
        "is_correct",
        "problem",
    ]
    search_fields = [
        "problem__name",
        "user__username",
        "user__full_name",
    ]

    def display_firstblooded(self, obj: models.Submission):
        return obj.is_firstblood

    display_firstblooded.short_description = "Firstblooded"
    display_firstblooded.boolean = True
    # return obj.firstblooded


class OrganizationAdmin(admin.ModelAdmin):
    list_display = ["__str__", "owner", "member_count", "is_open"]

    def has_view_permission(self, request, obj=None):
        if request.user.has_perm("gameserver.view_organization"):
            if obj is None:
                return True
            else:
                return obj.is_editable_by(request.user)
        return False

    def has_change_permission(self, request, obj=None):
        if request.user.has_perm("gameserver.change_organization"):
            if obj is None:
                return True
            else:
                return obj.is_editable_by(request.user)
        return False

    def get_queryset(self, request):
        return models.Organization.get_editable_organizations(request.user)

    def get_readonly_fields(self, request, obj=None):
        fields = self.readonly_fields
        if request.user.is_superuser or request.user.has_perm("gameserver.edit_all_organizations"):
            return fields
        if obj is None or request.user != obj.owner:
            fields += ("owner", "admins")
        return fields

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name in ("owner", "admins"):
            kwargs["queryset"] = models.User.objects.filter(is_staff=True).order_by("username")
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    @admin.display(description="Admins")
    def get_admins(self, obj):
        return ", ".join([u.username for u in obj.admins.all()])


class OrganizationRequestAdmin(admin.ModelAdmin):
    list_display = [
        "__str__",
        "user",
        "organization",
        "date_created",
        "status",
    ]
    list_filter = ["organization", "status"]
    readonly_fields = ["user", "organization", "date_created", "reason"]

    def has_view_permission(self, request, obj=None):
        if request.user.has_perm("gameserver.view_organization"):
            if obj is None:
                return True
            else:
                return obj.organization.is_editable_by(request.user)
        return False

    def has_change_permission(self, request, obj=None):
        if request.user.has_perm("gameserver.change_organization"):
            if obj is None:
                return True
            else:
                return obj.organization.is_editable_by(request.user) and not obj.reviewed
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(
            organization__in=models.Organization.get_editable_organizations(request.user)
        )


class ContestProblemInline(SortableInlineAdminMixin, admin.TabularInline):
    model = models.ContestProblem
    extra = 0


class ContestAdmin(SortableAdminBase, admin.ModelAdmin):
    fields = [
        "name",
        "slug",
        "organizers",
        "curators",
        "organizations",
        "description",
        "summary",
        "start_time",
        "end_time",
        "first_blood_webhook",
        "tags",
        "max_team_size",
        "is_public",
    ]
    inlines = [
        ContestProblemInline,
    ]
    list_display = [
        "name",
        "get_organizers",
        "start_time",
        "end_time",
    ]
    actions = [recalculate_score]

    def has_view_permission(self, request, obj=None):
        if request.user.has_perm("gameserver.view_contest"):
            if obj is None:
                return True
            else:
                return obj.is_editable_by(request.user)
        return False

    def has_change_permission(self, request, obj=None):
        if request.user.has_perm("gameserver.change_contest"):
            if obj is None:
                return True
            else:
                return obj.is_editable_by(request.user)
        return False

    def get_queryset(self, request):
        return models.Contest.get_editable_contests(request.user)

    def get_readonly_fields(self, request, obj=None):
        fields = self.readonly_fields
        if request.user.is_superuser or request.user.has_perm(
            "gameserver.change_contest_visibility"
        ):
            return fields
        fields += ("is_public",)
        return fields

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name in ("organizers", "curators"):
            kwargs["queryset"] = models.User.objects.filter(is_staff=True).order_by("username")
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    @admin.display(description="Organizers")
    def get_organizers(self, obj):
        return ", ".join([u.username for u in obj.organizers.all()])


class UserAdmin(admin.ModelAdmin):
    list_display = [
        "username",
        "full_name",
        "school_name",
        "is_staff",
        "is_superuser",
    ]
    list_filter = ["is_staff", "is_superuser", "groups"]
    search_fields = [
        "username",
        "full_name",
    ]
    actions = [recalculate_user_scores, recalculate_all_user_scores]


class UserScoreAdmin(admin.ModelAdmin):
    fields = (
        "user",
        "points",
        "flag_count",
        "last_correct_submission",
        "last_correct_submission_obj",
    )
    list_display = [
        "user",
        "points",
        "last_correct_submission",
    ]
    ordering = ["-points"]
    search_fields = [
        "user__username",
        "user__full_name",
    ]
    readonly_fields = [
        "user",
        "points",
        "flag_count",
        "last_correct_submission",
        "last_correct_submission_obj",
    ]

    def last_correct_submission_obj(self, obj):
        try:
            obj = Submission.objects.filter(
                user=obj.user, is_correct=True, problem__is_public=True
            ).latest("date_created")
        except Submission.DoesNotExist:
            return "No correct submissions"
        return format_html("<a href='{url}'>{url}</a>", url=obj.get_absolute_admin_url())

    last_correct_submission_obj.allow_tags = True

    last_correct_submission_obj.short_description = "Last correct submission URL"


class ContestScoreAdmin(admin.ModelAdmin):
    fields = (
        "participation",
        "points",
        "flag_count",
        "last_correct_submission",
        "last_correct_submission_obj",
    )
    list_display = [
        "participation",
        "points",
        "last_correct_submission",
    ]
    list_filter = ["participation__contest"]
    ordering = ["-points"]
    search_fields = [
        "participation__team__name",
        "participation__team__members__username",
    ]
    readonly_fields = [
        "participation",
        "points",
        "flag_count",
        "last_correct_submission",
        "last_correct_submission_obj",
    ]

    def last_correct_submission_obj(self, obj):
        try:
            obj = ContestSubmission.objects.filter(
                participation=obj.participation, submission__is_correct=True
            ).latest("submission__date_created")
        except ContestSubmission.DoesNotExist:
            return "No correct submissions"
        return format_html("<a href='{url}'>{url}</a>", url=obj.get_absolute_admin_url())

    last_correct_submission_obj.allow_tags = True
    last_correct_submission_obj.short_description = "Last correct submission URL"


admin.site.register(User, UserAdmin)
admin.site.register(models.ContestScore, ContestScoreAdmin)
admin.site.register(models.UserScore, UserScoreAdmin)
admin.site.register(models.Problem, ProblemAdmin)
admin.site.register(models.Submission, SubmissionAdmin)
admin.site.register(models.ProblemType)
admin.site.register(models.ProblemGroup)
admin.site.register(models.Organization, OrganizationAdmin)
admin.site.register(models.OrganizationRequest, OrganizationRequestAdmin)
admin.site.register(models.Comment)
admin.site.register(models.BlogPost)
admin.site.register(models.Writeup)
admin.site.register(models.Team)
admin.site.register(models.Contest, ContestAdmin)
admin.site.register(models.ContestTag)
admin.site.register(models.ContestParticipation)
admin.site.register(models.ContestSubmission)
admin.site.site_header = "mCTF administration"
admin.site.site_title = "mCTF admin"


class FlatPageAdmin(FlatPageAdmin):
    fieldsets = (
        (None, {"fields": ("url", "title", "content", "sites")}),
        (
            _("Advanced options"),
            {
                "classes": ("collapse",),
                "fields": (
                    "enable_comments",
                    "registration_required",
                    "template_name",
                ),
            },
        ),
    )


# Re-register FlatPageAdmin
admin.site.unregister(FlatPage)
admin.site.register(FlatPage, FlatPageAdmin)
