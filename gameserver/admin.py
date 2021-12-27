import django.db
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.flatpages.admin import FlatPageAdmin
from django.contrib.flatpages.models import FlatPage
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from martor.widgets import AdminMartorWidget

from . import models

User = get_user_model()


class ProblemFileInline(admin.TabularInline):
    fields = ["artifact"]
    model = models.ProblemFile
    extra = 0


class ProblemAdmin(admin.ModelAdmin):
    fields = [
        "name",
        "slug",
        "author",
        "description",
        "summary",
        "points",
        "flag",
        "problem_group",
        "problem_type",
        "is_private",
    ]
    inlines = [
        ProblemFileInline,
    ]
    formfield_overrides = {
        django.db.models.TextField: {"widget": AdminMartorWidget},
    }

    def has_view_permission(self, request, obj=None):
        if request.user.has_perm("gameserver.view_problem"):
            if obj is None:
                return True
            else:
                return request.user in obj.author.all() or request.user.has_perm("gameserver.edit_all_problems")
        return False

    def has_change_permission(self, request, obj=None):
        if request.user.has_perm("gameserver.change_problem"):
            if obj is None:
                return True
            else:
                return request.user in obj.author.all() or request.user.has_perm("gameserver.edit_all_problems")
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
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.has_perm('gameserver.edit_all_problems'):
            return qs
        return qs.filter(author=request.user)

    def get_readonly_fields(self, request, obj=None):
        fields = self.readonly_fields
        if not request.user.has_perm('gameserver.change_problem_visibility'):
            fields += ('is_private',)
        return fields

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
        return self.has_given_permission(
            request, obj, "gameserver.view_organizationrequest"
        )

    def has_change_permission(self, request, obj=None):
        status = self.has_given_permission(
            request, obj, "gameserver.change_organizationrequest"
        )
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


admin.site.register(User)
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
