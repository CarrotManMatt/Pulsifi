"""
    Automated test suite for avatar provider classes in pulsifi app.
"""

import validators

from pulsifi.avatar_providers import DiscordAvatarProvider, GoogleAvatarProvider, GithubAvatarProvider
from pulsifi.models import User
from pulsifi.tests.utils import Base_TestCase, Test_User_Factory, Test_Social_Account_Factory


class _Base_Avatar_Provider_Tests(Base_TestCase):
    def setUp(self):
        """
            Hook method for setting up the test fixture before exercising it.

            Create User to request avatar from.
        """

        super().setUp()

        self.test_user: User = Test_User_Factory.create()
        for provider in Test_Social_Account_Factory.AVAILABLE_PROVIDERS:
            Test_Social_Account_Factory.create(user=self.test_user, provider=provider)


class Discord_Avatar_Provider_Tests(_Base_Avatar_Provider_Tests):
    def test_no_social_account(self):
        self.assertIsNone(
            DiscordAvatarProvider.get_avatar_url(
                Test_User_Factory.create(),
                100,
                100
            )
        )

    def test_valid_url(self):
        self.assertTrue(
            validators.url(
                DiscordAvatarProvider.get_avatar_url(
                    self.test_user,
                    100,
                    100
                )
            )
        )

    def test_size_calculation(self):
        self.assertEqual(
            DiscordAvatarProvider.calculate_size(100, 100),
            128
        )
        self.assertEqual(
            DiscordAvatarProvider.calculate_size(16, 16),
            16
        )

    def test_max_size(self):
        self.assertEqual(
            DiscordAvatarProvider.calculate_size(9999, 9999),
            4096
        )

    def test_min_size(self):
        self.assertEqual(
            DiscordAvatarProvider.calculate_size(4, 4),
            16
        )

        with self.assertRaisesMessage(ValueError, "Given width & height must be within the valid range so that the calculated size is greater than 0."):
            DiscordAvatarProvider.calculate_size(1, 0)


class Github_Avatar_Provider_Tests(_Base_Avatar_Provider_Tests):
    def test_no_social_account(self):
        self.assertIsNone(
            GithubAvatarProvider.get_avatar_url(
                Test_User_Factory.create(),
                100,
                100
            )
        )

    def test_valid_url(self):
        self.assertTrue(
            validators.url(
                GithubAvatarProvider.get_avatar_url(
                    self.test_user,
                    100,
                    100
                )
            )
        )

    def test_size_calculation(self):
        self.assertEqual(
            GithubAvatarProvider.calculate_size(100, 100),
            100
        )

        self.assertEqual(
            GithubAvatarProvider.calculate_size(16, 16),
            16
        )

    def test_max_size(self):
        self.assertEqual(
            GithubAvatarProvider.calculate_size(999, 999),
            460
        )

    def test_min_size(self):
        with self.assertRaisesMessage(ValueError, "Given width & height must be within the valid range so that the calculated size is greater than 0."):
            GithubAvatarProvider.calculate_size(1, 0)


class Google_Avatar_Provider_Tests(_Base_Avatar_Provider_Tests):
    def test_no_social_account(self):
        self.assertIsNone(
            GoogleAvatarProvider.get_avatar_url(
                Test_User_Factory.create(),
                100,
                100
            )
        )

    def test_valid_url(self):
        self.assertTrue(
            validators.url(
                GoogleAvatarProvider.get_avatar_url(
                    self.test_user,
                    100,
                    100
                )
            )
        )

    def test_min_width_and_min_height(self):
        with self.assertRaisesMessage(ValueError, "Given width & height must be greater than 0."):
            GoogleAvatarProvider.get_avatar_url(self.test_user, 1, 0)

        with self.assertRaisesMessage(ValueError, "Given width & height must be greater than 0."):
            GoogleAvatarProvider.get_avatar_url(self.test_user, 0, 1)
