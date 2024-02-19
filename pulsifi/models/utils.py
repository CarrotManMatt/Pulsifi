"""
    Utility classes & functions provided for all models within this app.
"""

import functools
import operator
from typing import Collection

from django.conf import settings
from django.contrib import auth
from django.contrib.contenttypes.fields import GenericRel, GenericRelation
from django.db import models
from django.db.models import ManyToManyField, ManyToManyRel, ManyToOneRel

get_user_model = auth.get_user_model  # NOTE: Adding external package functions to the global scope for frequent usage


def get_restricted_admin_users_count(*, exclusion_id: int) -> int:
    """
        Returns the number of :model:`pulsifi.user` objects that already exist
        with their username one of the restricted usernames (declared in
        settings.py).
    """

    return get_user_model().objects.exclude(id=exclusion_id).filter(
        functools.reduce(
            operator.or_,
            (models.Q(username__icontains=username) for username in settings.RESTRICTED_ADMIN_USERNAMES)
        )
    ).count()


class Custom_Base_Model(models.Model):
    """
        Base model that provides extra utility methods for all other models to
        use.

        This class is abstract so should not be instantiated or have a table
        made for it in the database (see
        https://docs.djangoproject.com/en/4.1/topics/db/models/#abstract-base-classes).
    """

    class Meta:
        abstract = True

    def base_save(self, clean=True, *args, **kwargs) -> None:
        """
            The lowest level saving function that can bypass model cleaning
            (which will usually occur if save() is called), when recursive
            saving is required (E.g. within the update() method).
        """

        if clean:
            self.full_clean()

        models.Model.save(self, *args, **kwargs)

    def refresh_from_db(self, using: str = None, fields: Collection[str] = None, deep=True) -> None:
        """
            Custom implementation of refreshing in-memory objects from the
            database, which also updates any related fields on this object. The
            fields to update can be limited with the "fields" argument, and
            whether to update related objects or not can be specified with the
            "deep" argument.

            Uses django's argument structure so cannot be changed (see
            https://docs.djangoproject.com/en/4.1/ref/models/instances/#django.db.models.Model.refresh_from_db).
        """

        if fields is not None and not isinstance(fields, set):  # NOTE: Remove duplicate field names from fields parameter
            fields = set(fields)

        super().refresh_from_db(using=using, fields=fields)

        if fields is None:
            fields = set()

        if deep:  # NOTE: Refresh any related fields/objects if requested
            updated_model: models.Model = self._meta.model.objects.get(id=self.id)

            field: models.Field
            for field in self.get_single_relation_fields():
                if not fields or field.name in fields:  # NOTE: Limit the fields to update by the provided list of field names
                    setattr(self, field.name, getattr(updated_model, field.name))

            for field in self.get_multi_relation_fields():  # BUG: Relation fields not of acceptable type are not refreshed
                if not fields or field.name in fields:  # NOTE: Limit the fields to update by the provided list of field names
                    pass

    def save(self, *args, **kwargs) -> None:
        """
            Saves the current instance to the database, only after the model
            has been cleaned. This ensures any data in the database is valid,
            even if the data was not added via a ModelForm (E.g. data is added
            using the ORM API).

            Uses django's argument structure so cannot be changed (see
            https://docs.djangoproject.com/en/4.1/ref/models/instances/#django.db.models.Model.save).
        """

        self.full_clean()

        super().save(*args, **kwargs)

    def update(self, using: str = None, *, commit=True, base_save=False, clean=True, **kwargs) -> None:
        """
            Changes an in-memory object's values & save that object to the
            database all in one operation (based on Django's
            Queryset.bulk_update method).
        """

        key: str
        for key, value in kwargs.items():
            if key not in self.get_proxy_field_names():  # NOTE: Given field name must be a proxy field name or an actual field name
                self._meta.get_field(key)  # NOTE: Attempt to get the field by its name (will raise FieldDoesNotExist if no field exists with that name for this model)
            setattr(self, key, value)

        if commit:
            if base_save:  # NOTE: Use the base_save method of the object (to skip additional save functionality) and only clean the object if specified
                if using is not None:
                    self.base_save(clean, using)
                else:
                    self.base_save(clean)

            else:  # NOTE: Otherwise use the normal full save method of the object
                if using is not None:
                    self.save(using)
                else:
                    self.save()

    @classmethod
    def get_proxy_field_names(cls) -> set[str]:
        """
            Returns a set of names of extra properties of this model that can
            be saved to the database, even though those fields don't actually
            exist. They are just proxy fields.
        """

        return set()

    @classmethod
    def get_non_relation_fields(cls, *, names=False) -> set[models.Field] | set[str]:
        """
            Helper function to return an iterable of all the standard
            non-relation fields or field names of this model.
        """

        non_relation_fields: set[models.Field] = {field for field in cls._meta.get_fields() if field.name != "+" and not field.is_relation}

        if names:
            return {field.name for field in non_relation_fields}
        else:
            return non_relation_fields

    @classmethod
    def get_single_relation_fields(cls, *, names=False) -> set[models.Field] | set[str]:
        """
            Helper function to return an iterable of all the forward single
            relation fields or field names of this model.
        """

        single_relation_fields: set[models.Field] = {field for field in cls._meta.get_fields() if field.name != "+" and field.is_relation and not isinstance(field, ManyToManyField) and not isinstance(field, ManyToManyRel) and not isinstance(field, ManyToOneRel) and not isinstance(field, GenericRelation) and not isinstance(field, GenericRel)}

        if names:
            return {field.name for field in single_relation_fields}
        else:
            return single_relation_fields

    @classmethod
    def get_multi_relation_fields(cls, *, names=False) -> set[models.Field] | set[str]:
        """
            Helper function to return an iterable of all the forward
            many-to-many relation fields or field names of this model.
        """

        multi_relation_fields: set[models.Field] = {field for field in cls._meta.get_fields() if field.name != "+" and field.is_relation and (isinstance(field, ManyToManyField) or isinstance(field, ManyToManyRel) or isinstance(field, ManyToOneRel) or isinstance(field, GenericRelation) or isinstance(field, GenericRel))}

        if names:
            return {field.name for field in multi_relation_fields}
        else:
            return multi_relation_fields


class Date_Time_Created_Mixin(models.Model):
    """
        Model mixin that provides the field date_time_created, which is used by
        some other models in pulsifi app.

        This class is abstract so should not be instantiated or have a table
        made for it in the database (see
        https://docs.djangoproject.com/en/4.1/topics/db/models/#abstract-base-classes).
    """

    _date_time_created = models.DateTimeField(
        "Creation Date & Time",
        auto_now=True,
        help_text="Datetime object representing the date & time that this object instance was created."
    )

    @property
    def date_time_created(self):
        """
            Datetime object representing the date & time that this object
            instance was created.
        """

        return self._date_time_created

    class Meta:
        abstract = True
