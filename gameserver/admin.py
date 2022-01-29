import django.db
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.flatpages.admin import FlatPageAdmin
from django.contrib.flatpages.models import FlatPage
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from . import models

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
        "description",
        "summary",
        "points",
        "flag",
        "problem_group",
        "problem_type",
        "is_public",
        "challenge_spec",
    ]
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

    def has_module_permission(self, request):
        perms = [
            "gameserver.add_problem",
            "gameserver.view_problem",
            "gameserver.change_problem",
            "gameserver.delete_problem",
        ]
        return True in [request.user.has_perm(i) for i in perms]

    def get_queryset(self, request):
        return models.Problem.get_editable_problems(request.user)

    def get_readonly_fields(self, request, obj=None):
        fields = self.readonly_fields
        if not request.user.has_perm("gameserver.change_problem_visibility"):
            fields += ("is_public",)
        return fields

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "author":
            kwargs["queryset"] = models.User.objects.filter(is_staff=True).order_by("username")
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    @admin.display(description="Authors")
    def get_authors(self, obj):
        return ", ".join([u.username for u in obj.author.all()])


class OrganizationAdmin(admin.ModelAdmin):
    list_display = ["__str__", "owner", "member_count", "is_open"]

    def has_view_permission(self, request, obj=None):
        if request.user.has_perm("gameserver.view_organization"):
            if obj is None:
                return True
            else:
                return (
                    request.user in obj.admins.all()
                    or request.user == obj.owner
                    or request.user.is_superuser
                )
        return False

    def has_change_permission(self, request, obj=None):
        if request.user.has_perm("gameserver.change_organization"):
            if obj is None:
                return True
            else:
                return request.user == obj.owner or request.user.is_superuser
        return False

    def has_module_permission(self, request):
        perms = [
            "gameserver.add_organization",
            "gameserver.view_organization",
            "gameserver.change_organization",
            "gameserver.delete_organization",
        ]
        return True in [request.user.has_perm(i) for i in perms]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(Q(admins=request.user) | Q(owner=request.user))


class OrganizationRequestAdmin(admin.ModelAdmin):
    list_display = [
        "__str__",
        "user",
        "organization",
        "date_created",
        "status",
        "reviewed",
    ]
    list_filter = ["organization", "status"]
    readonly_fields = ["user", "organization", "date_created", "reason"]

    def has_given_permission(self, request, obj, permission):
        if request.user.has_perm(permission):
            if obj is None:
                return True
            else:
                return request.user in obj.organization.admins.all()
        return False

    def has_view_permission(self, request, obj=None):
        return self.has_given_permission(request, obj, "gameserver.view_organizationrequest")

    def has_change_permission(self, request, obj=None):
        status = self.has_given_permission(request, obj, "gameserver.change_organizationrequest")
        if obj is not None:
            return status and not obj.reviewed()
        return status

    def has_module_permission(self, request):
        perms = [
            "gameserver.add_organizationrequest",
            "gameserver.view_organizationrequest",
            "gameserver.change_organizationrequest",
            "gameserver.delete_organizationrequest",
        ]
        return True in [request.user.has_perm(i) for i in perms]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(organization__admins=request.user)


class ContestProblemInline(admin.TabularInline):
    model = models.ContestProblem
    extra = 0


class ContestAdmin(admin.ModelAdmin):
    inlines = [
        ContestProblemInline,
    ]
    list_display = [
        "name",
        "get_organizers",
        "start_time",
        "end_time",
    ]

    @admin.display(description="Organizers")
    def get_organizers(self, obj):
        return ", ".join([u.username for u in obj.organizers.all()])


class UserAdmin(admin.ModelAdmin):
    list_display = [
        "username",
        "full_name",
        "is_staff",
        "is_superuser",
    ]
    list_filter = ["is_staff", "is_superuser", "groups"]
    search_fields = [
        "username",
        "full_name",
    ]


admin.site.register(User, UserAdmin)
admin.site.register(models.Problem, ProblemAdmin)
admin.site.register(models.Submission)
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
