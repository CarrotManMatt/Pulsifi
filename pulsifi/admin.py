"""
    Admin configurations for models in pulsifi app.
"""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db.models import Count

from .admin_filters import GroupListFilter, StaffListFilter, VerifiedListFilter, VisibleListFilter
from .admin_inlines import About_Object_Report_Inline, Avatar_Inline, Created_Pulse_Inline, Created_Reply_Inline, Direct_Reply_Inline, Disliked_Pulse_Inline, Disliked_Reply_Inline, EmailAddress_Inline, Liked_Pulse_Inline, Liked_Reply_Inline, Staff_Assigned_Report_Inline, Submitted_Report_Inline, _Base_Report_Inline_Config
from .models import Pulse, Reply, Report, User

admin.site.site_header = "Pulsifi Administration"
admin.site.site_title = "Pulsifi Admin"
admin.site.index_title = "Whole Site Overview"
admin.site.empty_value_display = "- - - - -"


# TODO: Number of pulses range filter for user, number of replies range filter for user, reported filter for user, number of likes & dislikes range filter & ordering for pulses & replies
# TODO: add better inheritance to remove duplicated code


@admin.register(Pulse)
class Pulse_Admin(admin.ModelAdmin):
    date_hierarchy = "_date_time_created"
    fields = ["creator", "message", ("display_likes", "display_dislikes"), ("liked_by", "disliked_by"), "visible"]
    readonly_fields = ["display_likes", "display_dislikes"]
    autocomplete_fields = ["liked_by", "disliked_by"]
    list_display = ["creator", "message", "display_likes", "display_dislikes", "visible"]
    list_display_links = ["creator", "message"]
    list_editable = ["visible"]
    list_filter = [VisibleListFilter, ("message", admin.EmptyFieldListFilter)]
    search_fields = ["creator", "message"]
    search_help_text = "Search for a creator or message content"
    inlines = [Direct_Reply_Inline, About_Object_Report_Inline]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _likes=Count("liked_by", distinct=True),
            _dislikes=Count("disliked_by", distinct=True),
        )
        return queryset

    @admin.display(description="Number of likes", ordering="_likes")  # TODO: admin range filter on likes & dislikes field
    def display_likes(self, obj: Pulse):
        # noinspection PyUnresolvedReferences, PyProtectedMember
        return obj._likes

    @admin.display(description="Number of dislikes", ordering="_dislikes")
    def display_dislikes(self, obj: Pulse):
        # noinspection PyUnresolvedReferences, PyProtectedMember
        return obj._dislikes

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if not obj and ("display_likes", "display_dislikes") in fields:
            fields.remove(("display_likes", "display_dislikes"))
        return fields

    def get_inlines(self, request, obj):
        inlines = super().get_inlines(request, obj)

        try:
            Report._meta.get_field("assigned_staff_member").default()
        except get_user_model().DoesNotExist:
            inlines = [inline for inline in inlines if not issubclass(inline, _Base_Report_Inline_Config)]

        return inlines


@admin.register(Reply)
class Reply_Admin(admin.ModelAdmin):
    date_hierarchy = "_date_time_created"
    inlines = [Direct_Reply_Inline]
    readonly_fields = ["original_pulse"]

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if not obj:
            fields.remove("original_pulse")
        return fields


@admin.register(Report)
class Report_Admin(admin.ModelAdmin):
    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if not obj:
            fields.remove("assigned_staff_member")
        return fields

    def has_add_permission(self, request):
        try:
            Report._meta.get_field("assigned_staff_member").default()
        except get_user_model().DoesNotExist:
            return False
        return True


@admin.register(get_user_model())
class User_Admin(admin.ModelAdmin):
    date_hierarchy = "date_joined"
    fieldsets = [
        (None, {
            "fields": (("username", "email"), "bio", ("verified", "is_active"), "following")
        }),
        ("Authentication", {
            "fields": ("display_date_joined", "display_last_login", "password"),
            "classes": ("collapse",)
        }),
        ("Permissions", {
            "fields": ("groups", "user_permissions", "is_staff", "is_superuser"),
            "classes": ("collapse",)
        })
    ]
    filter_horizontal = ["user_permissions", ]
    inlines = [
        EmailAddress_Inline,
        Avatar_Inline,
        Created_Pulse_Inline,
        Liked_Pulse_Inline,
        Disliked_Pulse_Inline,
        Created_Reply_Inline,
        Liked_Reply_Inline,
        Disliked_Reply_Inline,
        About_Object_Report_Inline,
        Submitted_Report_Inline,
        Staff_Assigned_Report_Inline
    ]
    list_display = ["display_username", "email", "verified", "is_staff", "is_active"]
    list_display_links = ["display_username"]
    list_editable = ["email", "verified", "is_staff", "is_active"]
    list_filter = [VerifiedListFilter, StaffListFilter, GroupListFilter, VisibleListFilter, ("bio", admin.EmptyFieldListFilter)]
    autocomplete_fields = ["following", "groups"]
    readonly_fields = ["display_username", "password", "display_date_joined", "display_last_login"]
    search_fields = ["username", "email", "bio"]
    search_help_text = "Search for a username, email address or bio"

    @admin.display(description="Username", ordering="username")
    def display_username(self, obj: User):
        return str(obj)

    @admin.display(description="Date joined", ordering="date_joined")
    def display_date_joined(self, obj: User):
        return obj.date_joined.strftime("%d %b %Y %I:%M:%S %p")

    @admin.display(description="Last login", ordering="last_login")
    def display_last_login(self, obj: User):
        return obj.last_login.strftime("%d %b %Y %I:%M:%S %p")

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if not obj:
            fieldsets = [fieldset for fieldset in fieldsets if not fieldset[0] == "Authentication"]
        return fieldsets

    def get_form(self, *args, **kwargs):
        kwargs.update(
            {
                "labels": {"password": "Hashed password string"},
                "help_texts": {"is_active": None}
            }
        )
        return super().get_form(*args, **kwargs)

    def get_inlines(self, request, obj):
        inlines = super().get_inlines(request, obj)

        try:
            Report._meta.get_field("assigned_staff_member").default()
        except get_user_model().DoesNotExist:
            inlines = [inline for inline in inlines if not issubclass(inline, _Base_Report_Inline_Config)]

        return inlines

    def has_add_permission(self, *args, **kwargs):
        return False
