"""
    Admin filters for models in pulsifi app.
"""

import abc
from typing import Container, Sequence

from django.contrib import admin, auth
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.http import HttpRequest
from rangefilter.filters import NumericRangeFilter

from pulsifi.models import Pulse, Reply, Report, User, Visible_Reportable_Mixin

get_user_model = auth.get_user_model  # NOTE: Adding external package functions to the global scope for frequent usage


class Base_VisibleListFilter(admin.SimpleListFilter, abc.ABC):
    """
        Admin filter to limit any Visible_Reportable_Mixin objects shown on the
        admin list view, by the object's visibility.
    """

    title = "Visibility"
    parameter_name = "is_visible"

    def lookups(self, request: HttpRequest, model_admin: admin.ModelAdmin) -> Sequence[tuple[str, str]]:
        """
            Returns the sequence of pairs of url filter names & verbose filter
            names of the possible lookups.
        """

        return ("1", "Visible"), ("0", "Not Visible")

    @abc.abstractmethod
    def queryset(self, request: HttpRequest, queryset: models.QuerySet[Visible_Reportable_Mixin]) -> models.QuerySet[Visible_Reportable_Mixin]:
        """ Returns the filtered queryset according to the given url lookup. """

        raise NotImplementedError


class UserVerifiedListFilter(admin.SimpleListFilter):
    """
        Admin filter to limit the :model:`pulsifi.user` objects shown on the
        admin list view, by the user's verified status.
    """

    title = "Verified"
    parameter_name = "is_verified"

    def lookups(self, request: HttpRequest, model_admin: admin.ModelAdmin) -> Sequence[tuple[str, str]]:
        """
            Returns the sequence of pairs of url filter names & verbose filter
            names of the possible lookups.
        """

        return ("1", "Verified"), ("0", "Not Verified")

    def queryset(self, request: HttpRequest, queryset: models.QuerySet[User]) -> models.QuerySet[User]:
        """ Returns the filtered queryset according to the given url lookup. """

        if self.value() == "1":
            return queryset.filter(is_verified=True)
        if self.value() == "0":
            return queryset.filter(is_verified=False)


class UserVisibleListFilter(Base_VisibleListFilter):
    """
        Admin filter to limit the :model:`pulsifi.user` objects shown on the
        admin list view, by the user's visibility.
    """

    def queryset(self, request: HttpRequest, queryset: models.QuerySet[User]) -> models.QuerySet[User]:
        """ Returns the filtered queryset according to the given url lookup. """

        if self.value() == "1":
            return queryset.filter(is_active=True)
        if self.value() == "0":
            return queryset.filter(is_active=False)


class GroupListFilter(admin.SimpleListFilter):
    """
        Admin filter to limit the :model:`pulsifi.user` objects shown on the
        admin list view, by the user's group.
    """

    title = "Group"
    parameter_name = "group"

    def lookups(self, request: HttpRequest, model_admin: admin.ModelAdmin) -> Sequence[tuple[str, str]]:
        """
            Returns the sequence of pairs of url filter names & verbose filter
            names of the possible lookups.
        """

        return tuple((str(group.id), str(group.name)) for group in Group.objects.all())

    def queryset(self, request: HttpRequest, queryset: models.QuerySet[User]) -> models.QuerySet[User]:
        """ Returns the filtered queryset according to the given url lookup. """

        group_id: int | None = self.value()
        if group_id is not None:
            return queryset.filter(groups=group_id)
        return queryset


class StaffListFilter(admin.SimpleListFilter):
    """
        Admin filter to limit the :model:`pulsifi.user` objects shown on the
        admin list view, by whether the user is a staff member.
    """

    title = "Staff Member Status"
    parameter_name = "is_staff"

    def lookups(self, request: HttpRequest, model_admin: admin.ModelAdmin) -> Sequence[tuple[str, str]]:
        """
            Returns the sequence of pairs of url filter names & verbose filter
            names of the possible lookups.
        """

        return ("1", "Staff Member"), ("0", "Not a Staff Member")

    def queryset(self, request: HttpRequest, queryset: models.QuerySet[User]) -> models.QuerySet[User]:
        """ Returns the filtered queryset according to the given url lookup. """

        if self.value() == "1":
            return queryset.filter(is_staff=True)
        if self.value() == "0":
            return queryset.filter(is_staff=False)


# noinspection PyAbstractClass
class CreatedPulsesListFilter(admin.ListFilter):
    """
        Admin filter to limit the :model:`pulsifi.user` objects shown on the
        admin list view, by the number of :model:`pulsifi.pulse` objects they
        have created.
    """

    def __new__(cls, request: HttpRequest, params: Container, model: models.Model, model_admin: admin.ModelAdmin) -> admin.ListFilter:
        return NumericRangeFilter(
            models.PositiveIntegerField(verbose_name="Number of Created Pulses"),
            request,
            params,
            model,
            model_admin,
            field_path="_pulses",
        )


# noinspection PyAbstractClass
class CreatedRepliesListFilter(admin.ListFilter):
    """
        Admin filter to limit the :model:`pulsifi.user` objects shown on the
        admin list view, by the number of :model:`pulsifi.reply` objects they
        have created.
    """

    def __new__(cls, request: HttpRequest, params: Container, model: models.Model, model_admin: admin.ModelAdmin) -> admin.ListFilter:
        return NumericRangeFilter(
            models.PositiveIntegerField(verbose_name="Number of Created Replies"),
            request,
            params,
            model,
            model_admin,
            field_path="_replies",
        )


class ReportedObjectTypeListFilter(admin.SimpleListFilter):
    """
        Admin filter to limit the :model:`pulsifi.report` objects shown on the
        admin list view, by the type of object reported.
    """

    title = "Reported Object Type"
    parameter_name = "reported_object_type"

    def lookups(self, request: HttpRequest, model_admin: admin.ModelAdmin) -> Sequence[tuple[str, str]]:
        """
            Returns the sequence of pairs of url filter names & verbose filter
            names of the possible lookups.
        """

        # noinspection PyProtectedMember
        return [(content_type.model, content_type.name) for content_type in ContentType.objects.filter(**Report._meta.get_field("_content_type")._limit_choices_to)]

    def queryset(self, request: HttpRequest, queryset: models.QuerySet[Report]) -> models.QuerySet[Report]:
        """ Returns the filtered queryset according to the given url lookup. """

        content_type_name: str | None = self.value()
        if content_type_name is not None:
            # noinspection PyProtectedMember
            return queryset.filter(
                _content_type=ContentType.objects.filter(
                    **Report._meta.get_field("_content_type")._limit_choices_to
                ).filter(model=content_type_name).first()
            )
        return queryset


class AssignedModeratorListFilter(admin.SimpleListFilter):
    """
        Admin filter to limit the :model:`pulsifi.report` objects shown on the
        admin list view, by the assigned moderator.
    """

    title = "Assigned Moderator"
    parameter_name = "assigned_moderator"

    def lookups(self, request: HttpRequest, model_admin: admin.ModelAdmin) -> Sequence[tuple[str, str]]:
        """
            Returns the sequence of pairs of url filter names & verbose filter
            names of the possible lookups.
        """

        # noinspection PyProtectedMember
        return [(user.id, str(user)) for user in get_user_model().objects.filter(**Report._meta.get_field("assigned_moderator")._limit_choices_to)]

    def queryset(self, request: HttpRequest, queryset: models.QuerySet[Report]) -> models.QuerySet[Report]:
        """ Returns the filtered queryset according to the given url lookup. """

        user_id: int | None = self.value()
        if user_id is not None:
            return queryset.filter(assigned_moderator_id=user_id)
        return queryset


class CategoryListFilter(admin.SimpleListFilter):
    """
        Admin filter to limit the :model:`pulsifi.report` objects shown on the
        admin list view, by the category the report is within.
    """

    title = "Category"
    parameter_name = "category"

    def lookups(self, request: HttpRequest, model_admin: admin.ModelAdmin) -> Sequence[tuple[str, str]]:
        """
            Returns the sequence of pairs of url filter names & verbose filter
            names of the possible lookups.
        """

        return Report.Categories.choices

    def queryset(self, request: HttpRequest, queryset: models.QuerySet[Report]) -> models.QuerySet[Report]:
        """ Returns the filtered queryset according to the given url lookup. """

        category_choice: str | None = self.value()
        if category_choice is not None:
            return queryset.filter(category=category_choice)
        return queryset


class StatusListFilter(admin.SimpleListFilter):
    """
        Admin filter to limit the :model:`pulsifi.report` objects shown on the
        admin list view, by the status of the report.
    """

    title = "Status"
    parameter_name = "status"

    def lookups(self, request: HttpRequest, model_admin: admin.ModelAdmin) -> Sequence[tuple[str, str]]:
        """
            Returns the sequence of pairs of url filter names & verbose filter
            names of the possible lookups.
        """

        return Report.Statuses.choices

    def queryset(self, request: HttpRequest, queryset: models.QuerySet[Report]) -> models.QuerySet[Report]:
        """ Returns the filtered queryset according to the given url lookup. """

        status_choice: str | None = self.value()
        if status_choice is not None:
            return queryset.filter(status=status_choice)
        return queryset


# noinspection PyAbstractClass
class LikesListFilter(admin.ListFilter):
    """
        Admin filter to limit the :model:`pulsifi.pulse` &
        :model:`pulsifi.reply` objects shown on the admin list view, by the
        number of likes they have.
    """

    def __new__(cls, request: HttpRequest, params: Container, model: models.Model, model_admin: admin.ModelAdmin) -> admin.ListFilter:
        return NumericRangeFilter(
            models.PositiveIntegerField(verbose_name="Number of Likes"),
            request,
            params,
            model,
            model_admin,
            field_path="_likes",
        )


# noinspection PyAbstractClass
class DislikesListFilter(admin.ListFilter):
    """
        Admin filter to limit the :model:`pulsifi.pulse` &
        :model:`pulsifi.reply` objects shown on the admin list view, by the
        number of dislikes they have.
    """

    def __new__(cls, request: HttpRequest, params: Container, model: models.Model, model_admin: admin.ModelAdmin) -> admin.ListFilter:
        return NumericRangeFilter(
            models.PositiveIntegerField(verbose_name="Number of Dislikes"),
            request,
            params,
            model,
            model_admin,
            field_path="_dislikes",
        )


class HasReportAboutObjectListFilter(admin.SimpleListFilter):
    """
        Admin filter to limit the :model:`pulsifi.pulse`,
        :model:`pulsifi.reply` & :model:`pulsifi.user` objects shown on the
        admin list view, by whether they have been reported or not.
    """

    title = "Number of Reports"
    parameter_name = "has_reports"

    def lookups(self, request: HttpRequest, model_admin: admin.ModelAdmin) -> Sequence[tuple[str, str]]:
        """
            Returns the sequence of pairs of url filter names & verbose filter
            names of the possible lookups.
        """

        return ("1", "Has Been Reported"), ("0", "Has Not Been Reported")

    def queryset(self, request: HttpRequest, queryset: models.QuerySet[User | Pulse | Reply]) -> models.QuerySet[User | Pulse | Reply]:
        """ Returns the filtered queryset according to the given url lookup. """

        queryset = queryset.annotate(_reports=models.Count("about_object_report_set", distinct=True))
        if self.value() == "1":
            return queryset.filter(_reports__gt=0)
        if self.value() == "0":
            return queryset.filter(_reports=0)


class UserContentVisibleListFilter(Base_VisibleListFilter):
    """
        Admin filter to limit the :model:`pulsifi.pulse`,
        :model:`pulsifi.reply` objects shown on the admin list view, by whether
        they are visible or not.
    """

    def queryset(self, request: HttpRequest, queryset: models.QuerySet[Pulse | Reply]) -> models.QuerySet[Pulse | Reply]:
        """ Returns the filtered queryset according to the given url lookup. """

        if self.value() == "1":
            return queryset.filter(visible=True)
        if self.value() == "0":
            return queryset.filter(visible=False)


class RepliedObjectTypeListFilter(admin.SimpleListFilter):
    """
        Admin filter to limit the :model:`pulsifi.reply` objects shown on the
        admin list view, by the type of content that this is a reply for.
    """

    title = "Replied Object Type"
    parameter_name = "replied_object_type"

    def lookups(self, request: HttpRequest, model_admin: admin.ModelAdmin) -> Sequence[tuple[str, str]]:
        """
            Returns the sequence of pairs of url filter names & verbose filter
            names of the possible lookups.
        """

        # noinspection PyProtectedMember
        return [(content_type.model, content_type.name) for content_type in ContentType.objects.filter(**Reply._meta.get_field("_content_type")._limit_choices_to)]

    def queryset(self, request: HttpRequest, queryset: models.QuerySet[Reply]) -> models.QuerySet[Reply]:
        """ Returns the filtered queryset according to the given url lookup. """

        content_type_name: str | None = self.value()
        if content_type_name is not None:
            # noinspection PyProtectedMember
            return queryset.filter(
                _content_type=ContentType.objects.filter(
                    **Report._meta.get_field("_content_type")._limit_choices_to
                ).filter(model=content_type_name).first()
            )
        return queryset


# noinspection PyAbstractClass
class DirectRepliesListFilter(admin.ListFilter):
    """
        Admin filter to limit the :model:`pulsifi.pulse`,
        :model:`pulsifi.reply` objects shown on the admin list view, by the
        type of content that this is a reply for.
    """

    def __new__(cls, request: HttpRequest, params: Container, model: models.Model, model_admin: admin.ModelAdmin) -> admin.ListFilter:
        return NumericRangeFilter(
            models.PositiveIntegerField(verbose_name="Number of Direct Replies"),
            request,
            params,
            model,
            model_admin,
            field_path="_direct_replies",
        )
