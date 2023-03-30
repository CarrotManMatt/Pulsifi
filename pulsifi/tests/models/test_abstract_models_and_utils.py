"""
    Automated test suite for abstract models in pulsifi app.
"""
import itertools
from typing import Iterable, Type

from django.conf import settings
from django.contrib import auth
from django.db import models

from pulsifi.models import utils as pulsifi_models_utils
from pulsifi.tests import utils as pulsifi_tests_utils
from pulsifi.tests.utils import Base_TestCase, Base_Test_Data_Factory, Test_User_Factory

get_user_model = auth.get_user_model  # NOTE: Adding external package functions to the global scope for frequent usage


class Get_Restricted_Admin_Users_Count_Util_Function_Tests(Base_TestCase):
    def test_function_returns_restricted_admin_users_count(self):
        restricted_admin_usernames: Iterable[str] = itertools.islice(settings.RESTRICTED_ADMIN_USERNAMES, settings.PULSIFI_ADMIN_COUNT)
        restricted_admin_usernames_count = 0

        restricted_admin_username: str
        for restricted_admin_username in restricted_admin_usernames:
            Test_User_Factory.create(
                username=restricted_admin_username,
                is_staff=True
            )
            restricted_admin_usernames_count += 1

        for _ in range(3):
            Test_User_Factory.create()

        self.assertEqual(
            restricted_admin_usernames_count,
            pulsifi_models_utils.get_restricted_admin_users_count(exclusion_id=0)
        )

    def test_username_contains_restricted_admin_username(self):
        base_username: str = Test_User_Factory.create_field_value("username")
        base_username_length: int = len(base_username)

        Test_User_Factory.create(
            username=f"{base_username[:base_username_length // 2]}{next(iter(settings.RESTRICTED_ADMIN_USERNAMES))}{base_username[base_username_length // 2:]}",
            is_staff=True
        )

        for _ in range(3):
            Test_User_Factory.create()

        self.assertEqual(
            1,
            pulsifi_models_utils.get_restricted_admin_users_count(exclusion_id=0)
        )

    def test_exclusion_id_is_excluded(self):
        user = Test_User_Factory.create(
            username=next(iter(settings.RESTRICTED_ADMIN_USERNAMES)),
            is_staff=True
        )

        for _ in range(3):
            Test_User_Factory.create()

        self.assertEqual(
            0,
            pulsifi_models_utils.get_restricted_admin_users_count(exclusion_id=user.id)
        )


class Custom_Base_Model_Tests(Base_TestCase):
    def test_refresh_from_database_updates_non_relation_fields(self):
        model_name: str
        for model_name in pulsifi_tests_utils.GENERATABLE_MODEL_NAMES:
            model_factory: Type[Base_Test_Data_Factory] = pulsifi_tests_utils.get_model_factory(model_name)

            obj: pulsifi_models_utils.Custom_Base_Model = model_factory.create()
            old_obj: pulsifi_models_utils.Custom_Base_Model = obj._meta.model.objects.get(id=obj.id)

            self.assertEqual(obj, old_obj)

            field: models.Field
            for field in obj.get_non_relation_fields():
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
