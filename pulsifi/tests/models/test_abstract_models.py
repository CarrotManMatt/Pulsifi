"""
    Automated test suite for abstract models in pulsifi app.
"""
from typing import Type

from django.contrib import auth
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import ValidationError
from django.db import models

from pulsifi import models as pulsifi_models
from pulsifi.models import utils as pulsifi_models_utils, User
from pulsifi.tests import utils as pulsifi_tests_utils
from pulsifi.tests.utils import Base_TestCase, Base_Test_Data_Factory, Test_User_Factory

get_user_model = auth.get_user_model  # NOTE: Adding external package functions to the global scope for frequent usage


class Custom_Base_Model_Tests(Base_TestCase):
    def test_refresh_from_database_updates_non_relation_fields(self):
        model_name: str
        for model_name in pulsifi_tests_utils.GENERATABLE_MODELS_NAMES:
            model_factory: Type[Base_Test_Data_Factory] = pulsifi_tests_utils.get_model_factory(model_name)

            obj: pulsifi_models_utils.Custom_Base_Model = model_factory.create()
            old_obj: pulsifi_models_utils.Custom_Base_Model = obj._meta.model.objects.get(id=obj.id)

            field: models.Field
            for field in obj.get_non_relation_fields():
                self.assertEqual(
                    getattr(old_obj, field.name),
                    getattr(obj, field.name)
                )

                if field.name in pulsifi_tests_utils.get_model_factory(model_name).GENERATABLE_FIELDS:
                    setattr(
                        obj,
                        field.name,
                        model_factory.create_field_value(field.name)
                    )

                elif isinstance(field, models.BooleanField):
                    setattr(obj, field.name, not getattr(obj, field.name))

                else:
                    continue

                self.assertNotEqual(
                    getattr(obj, field.name),
                    getattr(old_obj, field.name)
                )

                obj.refresh_from_db()

                self.assertEqual(
                    getattr(old_obj, field.name),
                    getattr(obj, field.name)
                )

    def test_refresh_from_database_updates_single_relation_fields(self):
        model_name: str
        for model_name in pulsifi_tests_utils.GENERATABLE_MODELS_NAMES:
            obj: pulsifi_models_utils.Custom_Base_Model = pulsifi_tests_utils.get_model_factory(model_name).create()
            old_obj: pulsifi_models_utils.Custom_Base_Model = obj._meta.model.objects.get(id=obj.id)

            self.assertEqual(old_obj, obj)

            field: models.Field
            for field in obj.get_single_relation_fields():
                if field.name.startswith("_"):
                    continue

                if isinstance(field, GenericForeignKey):
                    setattr(
                        obj,
                        field.name,
                        pulsifi_tests_utils.get_model_factory(
                            next(iter(obj._meta.get_field(field.ct_field)._limit_choices_to["model__in"]))
                        ).create()
                    )

                elif isinstance(field, models.ForeignKey):
                    setattr(
                        obj,
                        field.name,
                        pulsifi_tests_utils.get_model_factory(field.related_model._meta.model_name).create()
                    )

                else:
                    continue

                self.assertNotEqual(
                    getattr(obj, field.name),
                    getattr(old_obj, field.name)
                )

                obj.refresh_from_db()

                self.assertEqual(
                    getattr(old_obj, field.name),
                    getattr(obj, field.name)
                )

    def test_update(self):
        model_name: str
        for model_name in pulsifi_tests_utils.GENERATABLE_MODELS_NAMES:
            model_factory: Type[Base_Test_Data_Factory] = pulsifi_tests_utils.get_model_factory(model_name)
            obj: pulsifi_models_utils.Custom_Base_Model = model_factory.create()

            field: models.Field
            for field in obj.get_non_relation_fields():
                old_value = getattr(obj, field.name)

                if field.name in pulsifi_tests_utils.get_model_factory(model_name).GENERATABLE_FIELDS:
                    try:
                        obj.update(**{field.name: model_factory.create_field_value(field.name)})
                    except ValidationError:
                        continue

                elif isinstance(field, models.BooleanField):
                    try:
                        obj.update(**{field.name: not getattr(obj, field.name)})
                    except ValidationError:
                        continue

                else:
                    continue

                self.assertNotEqual(
                    getattr(obj, field.name),
                    old_value
                )
                self.assertNotEqual(
                    getattr(obj._meta.model.objects.get(id=obj.id), field.name),
                    old_value
                )

    def test_update_without_commit(self):
        model_name: str
        for model_name in pulsifi_tests_utils.GENERATABLE_MODELS_NAMES:
            model_factory: Type[Base_Test_Data_Factory] = pulsifi_tests_utils.get_model_factory(model_name)
            obj: pulsifi_models_utils.Custom_Base_Model = model_factory.create()

            field: models.Field
            for field in obj.get_non_relation_fields():
                old_value = getattr(obj, field.name)

                if field.name in pulsifi_tests_utils.get_model_factory(model_name).GENERATABLE_FIELDS:
                    try:
                        obj.update(commit=False, **{field.name: model_factory.create_field_value(field.name)})
                    except ValidationError:
                        continue

                elif isinstance(field, models.BooleanField):
                    try:
                        obj.update(commit=False, **{field.name: not getattr(obj, field.name)})
                    except ValidationError:
                        continue

                else:
                    continue

                self.assertNotEqual(
                    getattr(obj, field.name),
                    old_value
                )
                self.assertEqual(
                    old_value,
                    getattr(obj._meta.model.objects.get(id=obj.id), field.name)
                )


class Visible_Reportable_Mixin_Tests(Base_TestCase):
    def test_delete_makes_not_visible(self):
        model_name: str
        for model_name in {"user", "pulse", "reply"}:
            obj: pulsifi_models.Visible_Reportable_Mixin = pulsifi_tests_utils.get_model_factory(model_name).create()

            self.assertTrue(obj.is_visible)

            obj.delete()
            obj.refresh_from_db()

            self.assertFalse(obj.is_visible)

    def test_string_when_visible(self):
        model_name: str
        for model_name in {"user", "pulse", "reply"}:
            model_factory: Type[Base_Test_Data_Factory] = pulsifi_tests_utils.get_model_factory(model_name)

            obj: pulsifi_models.Visible_Reportable_Mixin = model_factory.create()

            # noinspection PyTypeChecker
            string: str = model_factory.create_field_value(next(iter(model_factory.GENERATABLE_FIELDS)))

            self.assertEqual(
                string,
                obj.string_when_visible(string)
            )

            obj.update(is_visible=False)

            self.assertEqual(
                "".join(f"{char}\u0336" for char in string),
                obj.string_when_visible(string)
            )

    def test_get_absolute_url(self):
        model_name: str
        for model_name in {"user", "pulse", "reply"}:
            obj: pulsifi_models.User_Generated_Content_Model = pulsifi_tests_utils.get_model_factory(model_name).create()

            absolute_url: str = obj.get_absolute_url()

            self.assertTrue(absolute_url.startswith("/"))

            login_user_password: str = pulsifi_tests_utils.Test_User_Factory.create_field_value("password")
            self.client.login(
                username=pulsifi_tests_utils.Test_User_Factory.create(
                    password=login_user_password
                ).username,
                password=login_user_password
            )
            absolute_url_response = self.client.get(absolute_url)

            self.assertEqual(200, absolute_url_response.status_code)
            self.assertIn(obj, absolute_url_response.context.dicts[3].values())


class User_Generated_Content_Model_Tests(Base_TestCase):
    def test_liked_content_becoming_disliked_removes_like(self):
        liked_content_creator: User = Test_User_Factory.create()
        content_liker: User = Test_User_Factory.create()

        model_name: str
        for model_name in {"pulse", "reply"}:
            content: pulsifi_models.User_Generated_Content_Model = pulsifi_tests_utils.get_model_factory(model_name).create(creator=liked_content_creator)

            content.liked_by.add(content_liker)

            self.assertTrue(content.liked_by.filter(id=content_liker.id).exists())
            self.assertFalse(content.disliked_by.filter(id=content_liker.id).exists())

            content.disliked_by.add(content_liker)

            self.assertTrue(content.disliked_by.filter(id=content_liker.id).exists())
            self.assertFalse(content.liked_by.filter(id=content_liker.id).exists())

    def test_disliked_content_becoming_liked_removes_dislike(self):
        liked_content_creator: User = Test_User_Factory.create()
        content_liker: User = Test_User_Factory.create()

        model_name: str
        for model_name in {"pulse", "reply"}:
            content: pulsifi_models.User_Generated_Content_Model = pulsifi_tests_utils.get_model_factory(model_name).create(creator=liked_content_creator)

            content.disliked_by.add(content_liker)

            self.assertTrue(content.disliked_by.filter(id=content_liker.id).exists())
            self.assertFalse(content.liked_by.filter(id=content_liker.id).exists())

            content.liked_by.add(content_liker)

            self.assertTrue(content.liked_by.filter(id=content_liker.id).exists())
            self.assertFalse(content.disliked_by.filter(id=content_liker.id).exists())
