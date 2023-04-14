"""
    Automated test suite for extra template tags & filters in pulsifi app.
"""

from django.template import Template, Context
from django.utils import html as html_utils
from django.utils.safestring import SafeString

from pulsifi.models import utils as pulsifi_models_utils
from pulsifi.templatetags import pulsifi_extras
from pulsifi.tests import utils as pulsifi_tests_utils
from pulsifi.tests.utils import Base_TestCase, Base_Test_User_Generated_Content_Factory, Test_User_Factory


class Extra_Filters_Tests(Base_TestCase):
    def test_format_mentions_filter_user_exists(self):
        user = Test_User_Factory.create()
        message: str = Base_Test_User_Generated_Content_Factory.create_field_value("message")

        formatted_message = pulsifi_extras.format_mentions(
            f"{message[:len(message) // 2]}@{user.username} {message[len(message) // 2:]}"
        )

        self.assertEqual(
            f"{html_utils.escape(message[:len(message) // 2])}<a href=\"/user/@{user.username}/\">@{user.username}</a> {html_utils.escape(message[len(message) // 2:])}",
            formatted_message
        )
        self.assertIsInstance(formatted_message, SafeString)

    def test_format_mentions_filter_user_not_exists(self):
        user = Test_User_Factory.create(save=False)
        message: str = Base_Test_User_Generated_Content_Factory.create_field_value("message")

        formatted_message = pulsifi_extras.format_mentions(
            f"{message[:len(message) // 2]}@{user.username} {message[len(message) // 2:]}"
        )

        self.assertEqual(
            f"{html_utils.escape(message[:len(message) // 2])}@{user.username} {html_utils.escape(message[len(message) // 2:])}",
            formatted_message
        )
        self.assertIsInstance(formatted_message, SafeString)

    def test_format_mentions_filter_invalid_username(self):
        message: str = Base_Test_User_Generated_Content_Factory.create_field_value("message")

        formatted_message = pulsifi_extras.format_mentions(
            f"{message[:len(message) // 6]}@$$hi {message[len(message) // 6:(2 * len(message)) // 6]}@admin {message[(2 * len(message)) // 6:(3 * len(message)) // 6]}@https {message[(3 * len(message)) // 6:(4 * len(message)) // 6]}@abuse {message[(4 * len(message)) // 6:(5 * len(message)) // 6]}@docs {message[(5 * len(message)) // 6:]}"
        )

        self.assertEqual(
            f"{html_utils.escape(message[:len(message) // 6])}@$$hi {html_utils.escape(message[len(message) // 6:(2 * len(message)) // 6])}@admin {html_utils.escape(message[(2 * len(message)) // 6:(3 * len(message)) // 6])}@https {html_utils.escape(message[(3 * len(message)) // 6:(4 * len(message)) // 6])}@abuse {html_utils.escape(message[(4 * len(message)) // 6:(5 * len(message)) // 6])}@docs {html_utils.escape(message[(5 * len(message)) // 6:])}",
            formatted_message
        )
        self.assertIsInstance(formatted_message, SafeString)

    def test_model_meta_tag(self):
        model_name: str
        for model_name in pulsifi_tests_utils.PULSIFI_GENERATABLE_MODELS_NAMES:
            obj: pulsifi_models_utils.Custom_Base_Model = pulsifi_tests_utils.get_model_factory(model_name).create()

            self.assertEqual(obj._meta, pulsifi_extras.model_meta(obj))
            self.assertEqual(
                obj._meta.model_name,
                "".join(
                    [line.strip() for line in Template(
                        "{% load pulsifi_extras %}\n{% model_meta obj as obj_meta %}\n{{ obj_meta.model_name }}"
                    ).render(
                        Context({"obj": obj})
                    ).splitlines()]
                )
            )
            self.assertEqual(
                obj._meta.verbose_name,
                "".join(
                    [line.strip() for line in Template(
                        "{% load pulsifi_extras %}\n{% model_meta obj as obj_meta %}\n{{ obj_meta.verbose_name }}"
                    ).render(
                        Context({"obj": obj})
                    ).splitlines()]
                )
            )
