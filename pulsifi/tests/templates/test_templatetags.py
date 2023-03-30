"""
    Automated test suite for extra template tags & filters in pulsifi app.
"""

from django.utils import html as html_utils

from pulsifi.templatetags import pulsifi_extras
from pulsifi.tests.utils import Base_TestCase, Base_Test_User_Generated_Content_Factory, Test_User_Factory


class Extra_Filters_Tests(Base_TestCase):
    def test_format_mentions_filter_user_exists(self):
        user = Test_User_Factory.create()
        message: str = Base_Test_User_Generated_Content_Factory.create_field_value("message")

        self.assertEqual(
            f"{html_utils.escape(message[:len(message) // 2])}<a href=\"/user/@{user.username}/\">@{user.username}</a> {html_utils.escape(message[len(message) // 2:])}",
            pulsifi_extras.format_mentions(f"{message[:len(message) // 2]}@{user.username} {message[len(message) // 2:]}")
        )

    def test_format_mentions_filter_user_not_exists(self):
        user = Test_User_Factory.create(save=False)
        message: str = Base_Test_User_Generated_Content_Factory.create_field_value("message")

        self.assertEqual(
            f"{html_utils.escape(message[:len(message) // 2])}@{user.username} {html_utils.escape(message[len(message) // 2:])}",
            pulsifi_extras.format_mentions(f"{message[:len(message) // 2]}@{user.username} {message[len(message) // 2:]}")
        )

    def test_format_mentions_filter_invalid_username(self):
        message: str = Base_Test_User_Generated_Content_Factory.create_field_value("message")

        self.assertEqual(
            f"{html_utils.escape(message[:len(message) // 6])}@$$hi {html_utils.escape(message[len(message) // 6:(2 * len(message)) // 6])}@admin {html_utils.escape(message[(2 * len(message)) // 6:(3 * len(message)) // 6])}@https {html_utils.escape(message[(3 * len(message)) // 6:(4 * len(message)) // 6])}@abuse {html_utils.escape(message[(4 * len(message)) // 6:(5 * len(message)) // 6])}@docs {html_utils.escape(message[(5 * len(message)) // 6:])}",
            pulsifi_extras.format_mentions(f"{message[:len(message) // 6]}@$$hi {message[len(message) // 6:(2 * len(message)) // 6]}@admin {message[(2 * len(message)) // 6:(3 * len(message)) // 6]}@https {message[(3 * len(message)) // 6:(4 * len(message)) // 6]}@abuse {message[(4 * len(message)) // 6:(5 * len(message)) // 6]}@docs {message[(5 * len(message)) // 6:]}")
        )
