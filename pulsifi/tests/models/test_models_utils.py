"""
    Automated test suite for models utils in pulsifi app.
"""

import itertools
from typing import Iterable

from django.conf import settings

from pulsifi.models import utils as pulsifi_models_utils
from pulsifi.tests.utils import Base_TestCase, Test_User_Factory


class Get_Restricted_Admin_Users_Count_Util_Function_Tests(Base_TestCase):
    def test_function_returns_restricted_admin_users_count(self):
        restricted_admin_usernames: Iterable[str] = itertools.islice(
            settings.RESTRICTED_ADMIN_USERNAMES,
            settings.PULSIFI_ADMIN_COUNT
        )
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
