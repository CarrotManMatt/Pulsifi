"""
    Automated test suite for abstract models in pulsifi app.
"""

from django.contrib.contenttypes.models import ContentType

from pulsifi.forms import Bio_Form, Login_Form, Pulse_Form, Reply_Form, Signup_Form
from pulsifi.tests.utils import Base_TestCase, Test_Reply_Factory, Test_User_Factory


class Login_Form_Tests(Base_TestCase):
    def test_has_prefix(self):
        self.assertTrue(Login_Form().prefix)


class Signup_Form_Tests(Base_TestCase):
    def test_has_prefix(self):
        self.assertTrue(Signup_Form().prefix)

    def test_field_values_cleaned_against_model(self):
        password: str = Test_User_Factory.create_field_value("password")
        signup_form = Signup_Form(
            {
                "signup-username": f"""{Test_User_Factory.create_field_value("username")}pulsifi""",
                "signup-password1": password,
                "signup-password2": password,
                "signup-email": Test_User_Factory.create_field_value("email")
            }
        )

        self.assertTrue(
            any("username is not allowed" in error for error in signup_form.errors["username"])
        )

    def test_password_too_common_error_does_not_show_when_length_error_shows(self):
        password: str = "vh5150"
        signup_form = Signup_Form(
            {
                "signup-username": Test_User_Factory.create_field_value("username"),
                "signup-password1": password,
                "signup-password2": password,
                "signup-email": Test_User_Factory.create_field_value("email")
            }
        )

        self.assertFalse(
            any("common" in error for error in signup_form.errors["password1"]) and any("short" in error for error in signup_form.errors["password1"])
        )


class Pulse_Form_Tests(Base_TestCase):
    def test_has_prefix(self):
        self.assertTrue(Pulse_Form().prefix)


class Reply_Form_Tests(Base_TestCase):
    def test_has_prefix(self):
        self.assertTrue(Reply_Form().prefix)

    def test_creator_content_type_and_object_id_fields_are_hidden(self):
        self.assertTrue(Reply_Form().fields["_content_type"].widget.is_hidden)
        self.assertTrue(Reply_Form().fields["_object_id"].widget.is_hidden)

    def test_cannot_create_reply_soon_after_already_creating_a_reply_under_the_same_original_pulse(self):
        reply = Test_Reply_Factory.create()

        reply_form = Reply_Form(
            {
                "create_reply-message": Test_Reply_Factory.create_field_value("message"),
                "create_reply-_content_type": ContentType.objects.get_for_model(reply.original_pulse),
                "create_reply-_object_id": reply.original_pulse.id
            }
        )
        reply_form.instance.creator = reply.creator

        self.assertIn(
            "Cannot create Reply so soon after already creating a Reply under this original Pulse.",
            reply_form.errors["__all__"]
        )


class Bio_Form_Tests(Base_TestCase):
    def test_has_prefix(self):
        self.assertTrue(Bio_Form().prefix)
