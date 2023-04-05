"""
    Automated test suite for concrete models in pulsifi app.
"""

from allauth.account import utils as allauth_utils
from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib import auth
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.db import IntegrityError, transaction

from pulsifi import models as pulsifi_models
from pulsifi.models import Follow, Report, User, Pulse, Reply
from pulsifi.tests import utils as pulsifi_tests_utils
from pulsifi.tests.utils import Base_TestCase, Test_Report_Factory, Test_User_Factory
from pulsifi.validators import ReservedUsernameValidator, FreeEmailValidator, ExampleEmailValidator

get_user_model = auth.get_user_model  # NOTE: Adding external package functions to the global scope for frequent usage


# TODO: tests docstrings

class User_Model_Tests(Base_TestCase):  # TODO: test validators & validation errors from clean method, test if username length check is working for in-code user creation
    def test_username_validate_regex(self):
        invalid_char: str
        for invalid_char in {"@", "%", ",", "-", "=", "?", " ", "#", "!", "&", "<", ">", "^", "*", "$", "£", "`", "/", "\\"}:
            with self.assertRaisesMessage(ValidationError, "Enter a valid username. It must contain only letters, digits, '.' and '_'characters."):
                pulsifi_tests_utils.Test_User_Factory.create(
                    username=f"""{pulsifi_tests_utils.Test_User_Factory.create_field_value("username")}{invalid_char}"""
                )

        valid_char: str
        for valid_char in {".", "_"}:
            try:
                pulsifi_tests_utils.Test_User_Factory.create(
                    username=f"""{pulsifi_tests_utils.Test_User_Factory.create_field_value("username")}{valid_char}"""
                )
            except ValidationError:
                self.fail()

    def test_username_validate_not_reserved_username(self):
        with self.assertRaisesMessage(ValidationError, "This username is reserved and cannot be registered. Please choose a different username."):
            pulsifi_tests_utils.Test_User_Factory.create(
                username=next(iter(ReservedUsernameValidator().reserved_usernames))
            )

    def test_username_validate_not_confusable(self):
        with self.assertRaisesMessage(ValidationError, "This username cannot be registered. Please choose a different username."):
            pulsifi_tests_utils.Test_User_Factory.create(
                username=f"""{pulsifi_tests_utils.Test_User_Factory.create_field_value("username")}а"""
            )

    def test_username_validate_min_length(self):
        with self.assertRaisesMessage(ValidationError, "Username must have at least 4 characters."):
            pulsifi_tests_utils.Test_User_Factory.create(
                username=pulsifi_tests_utils.Test_User_Factory.create_field_value("username")[:3]
            )

    def test_username_unique(self):
        user: User = pulsifi_tests_utils.Test_User_Factory.create()

        with self.assertRaisesMessage(ValidationError, "A user with that username already exists."):
            pulsifi_tests_utils.Test_User_Factory.create(username=user.username)

    def test_username_not_empty(self):
        user: User = pulsifi_tests_utils.Test_User_Factory.create()

        with self.assertRaisesMessage(ValidationError, "Username is a required field."):
            user.update(username=None)

        with self.assertRaisesMessage(ValidationError, "Username is a required field."):
            user.update(username="")

    def test_email_validate_html5_email(self):
        with self.assertRaisesMessage(ValidationError, "Enter a valid email address."):
            pulsifi_tests_utils.Test_User_Factory.create(
                email=pulsifi_tests_utils.Test_User_Factory.create_field_value("username")
            )

    def test_email_validate_not_free_email(self):
        with self.assertRaisesMessage(ValidationError, "Registration using free email addresses is prohibited. Please supply a different email address."):
            pulsifi_tests_utils.Test_User_Factory.create(
                email=f"local@{next(iter(FreeEmailValidator().free_email_domains))}"
            )

    def test_email_validate_local_confusable(self):
        with self.assertRaisesMessage(ValidationError, "This email address cannot be registered. Please supply a different email address."):
            pulsifi_tests_utils.Test_User_Factory.create(
                email=f"locаl@yahoo.com"
            )

    def test_email_validate_domain_confusable(self):
        with self.assertRaisesMessage(ValidationError, "This email address cannot be registered. Please supply a different email address."):
            pulsifi_tests_utils.Test_User_Factory.create(
                email=f"local@yаhoo.com"
            )

    def test_email_validate_not_preexisting_with_tld(self):
        tld: str = "yahoo.com"

        pulsifi_tests_utils.Test_User_Factory.create(email=f"local@{tld}")

        with self.assertRaisesMessage(ValidationError, "That Email Address is already in use by another user."):
            pulsifi_tests_utils.Test_User_Factory.create(
                email=f"local@me.test.{tld}"
            )

    def test_email_validate_not_example_email(self):
        with self.assertRaisesMessage(ValidationError, "Registration using unresolvable example email addresses is prohibited. Please supply a different email address."):
            pulsifi_tests_utils.Test_User_Factory.create(
                email=f"local@{next(iter(ExampleEmailValidator().example_email_domains))}"
            )

    def test_email_not_empty(self):
        user: User = pulsifi_tests_utils.Test_User_Factory.create()

        with self.assertRaisesMessage(ValidationError, "Email Address is a required field."):
            user.update(email=None)

        with self.assertRaisesMessage(ValidationError, "Email Address is a required field."):
            user.update(email="")

    def test_valid_email(self):
        user: User = pulsifi_tests_utils.Test_User_Factory.create(
            email="local@me.test.yahoo.com"
        )

        self.assertEqual("local@me.test.yahoo.com", user.email)

    def test_bio_not_null(self):
        user: User = pulsifi_tests_utils.Test_User_Factory.create()

        with self.assertRaisesMessage(IntegrityError, "bio"), transaction.atomic():
            user.update(bio=None)

        try:
            user.update(bio="")
        except (ValidationError, IntegrityError):
            self.fail()

    def test_delete_makes_not_active(self):
        user = Test_User_Factory.create()

        self.assertTrue(user.is_active)

        user.delete()
        user.refresh_from_db()

        self.assertFalse(user.is_active)

    def test_visible_shortcut_in_memory(self):
        user = Test_User_Factory.create()

        self.assertTrue(user.is_visible)
        self.assertTrue(user.is_active)

        user.is_visible = False

        self.assertFalse(user.is_visible)
        self.assertFalse(user.is_active)

    def test_visible_shortcut_in_database(self):
        user = Test_User_Factory.create()

        self.assertTrue(user.is_visible)
        self.assertTrue(user.is_active)

        user.update(is_visible=False)

        self.assertFalse(user.is_visible)
        self.assertFalse(user.is_active)

    def test_stringify_displays_in_correct_format(self):
        user = Test_User_Factory.create()

        self.assertEqual(f"@{user.username}", str(user))

        user.update(is_active=False)

        self.assertEqual(
            "".join(char + "\u0336" for char in f"@{user.username}"),
            str(user)
        )

    def test_user_becomes_superuser_put_in_admin_group(self):
        user = Test_User_Factory.create()
        admin_group = Group.objects.get(name="Admins")

        self.assertNotIn(admin_group, user.groups.all())

        user.update(is_superuser=True)

        self.assertIn(admin_group, user.groups.all())

    def test_superuser_has_groups_changed_kept_in_admin_group(self):
        user = Test_User_Factory.create(is_superuser=True)
        admin_group = Group.objects.get(name="Admins")

        self.assertIn(admin_group, user.groups.all())

        user.groups.remove(admin_group)

        self.assertIn(admin_group, user.groups.all())

        user.groups.set(Group.objects.none())

        self.assertIn(admin_group, user.groups.all())

        user.groups.set([])

        self.assertIn(admin_group, user.groups.all())

        user.groups.clear()

        self.assertIn(admin_group, user.groups.all())

    def test_admin_group_has_users_changed_superusers_kept_in_admin_group(self):
        user = Test_User_Factory.create(is_superuser=True)
        admin_group = Group.objects.get(name="Admins")

        self.assertIn(user, admin_group.user_set.all())

        admin_group.user_set.remove(user)

        self.assertIn(user, admin_group.user_set.all())

        admin_group.user_set.set(get_user_model().objects.none())

        self.assertIn(user, admin_group.user_set.all())

        admin_group.user_set.set([])

        self.assertIn(user, admin_group.user_set.all())

        admin_group.user_set.clear()

        self.assertIn(user, admin_group.user_set.all())

    def test_super_user_made_staff(self):
        user = Test_User_Factory.create()

        self.assertFalse(user.is_staff)

        user.update(is_superuser=True)

        self.assertTrue(user.is_staff)

    def test_user_added_to_staff_group_made_staff(self):
        staff_group_name: str
        for staff_group_name in get_user_model().STAFF_GROUP_NAMES:
            user = Test_User_Factory.create()
            group = Group.objects.get(name=staff_group_name)

            self.assertFalse(user.is_staff)

            user.groups.add(group)

            user.refresh_from_db()

            self.assertTrue(user.is_staff)

    def test_moderator_group_has_user_added_made_staff(self):
        staff_group_name: str
        for staff_group_name in get_user_model().STAFF_GROUP_NAMES:
            user = Test_User_Factory.create()
            group = Group.objects.get(name=staff_group_name)

            self.assertFalse(user.is_staff)

            group.user_set.add(user)

            user.refresh_from_db()

            self.assertTrue(user.is_staff)

    def test_user_cannot_be_in_own_following(self):
        user = Test_User_Factory.create()

        with self.assertRaisesMessage(IntegrityError, "CHECK constraint failed: not_follow_self"), transaction.atomic():
            # noinspection DjangoOrm
            user.following.add(user)

    def test_user_cannot_be_in_own_followers(self):
        user = Test_User_Factory.create()

        with self.assertRaisesMessage(IntegrityError, "CHECK constraint failed: not_follow_self"), transaction.atomic():
            # noinspection DjangoOrm
            user.followers.add(user)

    def test_staff_can_have_restricted_admin_username(self):
        for restricted_admin_username in list(settings.RESTRICTED_ADMIN_USERNAMES)[:settings.PULSIFI_ADMIN_COUNT]:
            try:
                Test_User_Factory.create(
                    username=restricted_admin_username,
                    is_staff=True
                )
            except ValidationError:
                self.fail()

    def test_non_staff_cannot_have_restricted_admin_username(self):
        for restricted_admin_username in list(settings.RESTRICTED_ADMIN_USERNAMES)[:settings.PULSIFI_ADMIN_COUNT]:
            with self.assertRaisesMessage(ValidationError, "That username is not allowed."):
                Test_User_Factory.create(username=restricted_admin_username)

    def test_staff_cannot_have_restricted_admin_username_when_already_max_admin_count(self):
        for restricted_admin_username in list(settings.RESTRICTED_ADMIN_USERNAMES)[:settings.PULSIFI_ADMIN_COUNT]:
            Test_User_Factory.create(
                username=f"{restricted_admin_username}test",
                is_staff=True
            )

            with self.assertRaisesMessage(ValidationError, "That username is not allowed."):
                Test_User_Factory.create(
                    username=restricted_admin_username,
                    is_staff=True
                )

    def test_dots_removed_from_local_part_of_email(self):
        local_email = "test.local.email"
        domain_email = "test.domain.email.com"
        user = Test_User_Factory.create(email=f"{local_email}@{domain_email}")

        self.assertEqual(
            f"""{local_email.replace(".", "")}@{domain_email}""",
            user.email
        )

    def test_plus_alias_removed_from_local_part_of_email(self):
        local_email = "test+local+email"
        domain_email = "test.domain.email.com"
        user = Test_User_Factory.create(email=f"{local_email}@{domain_email}")

        self.assertEqual(
            f"""{local_email.partition("+")[0]}@{domain_email}""",
            user.email
        )

    def test_google_email_alias_replaced(self):
        local_email = "test"
        domain_email = "googlemail.com"
        user = Test_User_Factory.create(email=f"{local_email}@{domain_email}")

        self.assertEqual(f"{local_email}@gmail.com", user.email)

    def test_verified_user_must_have_at_least_one_verified_email(self):
        with self.assertRaisesMessage(ValidationError, "User cannot become verified without at least one verified email address."):
            Test_User_Factory.create(is_verified=True)

        user = Test_User_Factory.create()
        allauth_utils.sync_user_email_addresses(user)
        primary_email: EmailAddress = user.emailaddress_set.get()
        primary_email.primary = True
        primary_email.save()

        with self.assertRaisesMessage(ValidationError, "User cannot become verified without at least one verified email address."):
            user.update(is_verified=True)

        primary_email.verified = True
        primary_email.save()

        try:
            user.update(is_verified=True)
        except ValidationError:
            self.fail()

    def test_email_validate_attribute_unique(self):
        user = Test_User_Factory.create()

        with self.assertRaisesMessage(ValidationError, "That Email Address is already in use by another user."):
            Test_User_Factory.create(email=user.email)

    def test_email_object_not_already_exists(self):
        user = Test_User_Factory.create()
        allauth_utils.sync_user_email_addresses(user)
        old_email = user.email
        user.update(email=Test_User_Factory.create_field_value("email"))

        with self.assertRaisesMessage(ValidationError, "That Email Address is already in use by another user."):
            Test_User_Factory.create(email=old_email)

    def test_reverse_liked_content_becoming_disliked_removes_like(self):
        liked_content_creator: User = Test_User_Factory.create()
        content_liker: User = Test_User_Factory.create()

        model_name: str
        for model_name in {"pulse", "reply"}:
            content: pulsifi_models.User_Generated_Content_Model = pulsifi_tests_utils.get_model_factory(model_name).create(creator=liked_content_creator)

            if model_name == "pulse":
                content_liker.liked_pulse_set.add(content)
            elif model_name == "reply":
                content_liker.liked_reply_set.add(content)

            self.assertTrue(content.liked_by.filter(id=content_liker.id).exists())
            self.assertFalse(content.disliked_by.filter(id=content_liker.id).exists())

            if model_name == "pulse":
                content_liker.disliked_pulse_set.add(content)
            elif model_name == "reply":
                content_liker.disliked_reply_set.add(content)

            self.assertTrue(content.disliked_by.filter(id=content_liker.id).exists())
            self.assertFalse(content.liked_by.filter(id=content_liker.id).exists())

    def test_reverse_disliked_content_becoming_liked_removes_dislike(self):
        liked_content_creator: User = Test_User_Factory.create()
        content_liker: User = Test_User_Factory.create()

        model_name: str
        for model_name in {"pulse", "reply"}:
            content: pulsifi_models.User_Generated_Content_Model = pulsifi_tests_utils.get_model_factory(model_name).create(creator=liked_content_creator)

            if model_name == "pulse":
                content_liker.disliked_pulse_set.add(content)
            elif model_name == "reply":
                content_liker.disliked_reply_set.add(content)

            self.assertTrue(content.disliked_by.filter(id=content_liker.id).exists())
            self.assertFalse(content.liked_by.filter(id=content_liker.id).exists())

            if model_name == "pulse":
                content_liker.liked_pulse_set.add(content)
            elif model_name == "reply":
                content_liker.liked_reply_set.add(content)

            self.assertTrue(content.liked_by.filter(id=content_liker.id).exists())
            self.assertFalse(content.disliked_by.filter(id=content_liker.id).exists())

    def test_obsolete_fields_from_base_user_class_are_none(self):
        user = Test_User_Factory.create()

        self.assertIsNone(user.first_name)
        self.assertIsNone(user.last_name)

        with self.assertRaises(FieldDoesNotExist):
            user.update(first_name="test_value")

        self.assertIsNone(user.first_name)

        with self.assertRaises(FieldDoesNotExist):
            user.update(last_name="test_value")

        self.assertIsNone(user.last_name)


class Pulse_Model_Tests(Base_TestCase):
    def test_stringify_displays_in_correct_format(self):
        pulse: Pulse = pulsifi_tests_utils.Test_Pulse_Factory.create()

        self.assertEqual(
            f"{pulse.creator}, {pulse.message[:settings.MESSAGE_DISPLAY_LENGTH]}",
            str(pulse)
        )

        pulse.update(is_visible=False)

        message: str = "".join(char + "\u0336" for char in pulse.message[:settings.MESSAGE_DISPLAY_LENGTH])
        self.assertEqual(
            f"{pulse.creator}, {message}",
            str(pulse)
        )


class Reply_Model_Tests(Base_TestCase):
    def test_stringify_displays_in_correct_format(self):
        reply: Reply = pulsifi_tests_utils.Test_Reply_Factory.create()

        self.assertEqual(
            f"{reply.creator}, {reply.message[:settings.MESSAGE_DISPLAY_LENGTH]} (For object - {reply._content_type.name} | {reply.replied_content})"[:100],
            str(reply)
        )

        reply.update(is_visible=False)

        message: str = "".join(char + "\u0336" for char in reply.message[:settings.MESSAGE_DISPLAY_LENGTH])
        self.assertEqual(
            f"{reply.creator}, {message} (For object - {reply._content_type.name} | {reply.replied_content})"[:100],
            str(reply)
        )


class Follow_Model_Tests(Base_TestCase):
    def test_cannot_have_same_follower_as_followee(self):
        user = Test_User_Factory.create()

        with self.assertRaisesMessage(ValidationError, "not_follow_self"):
            Follow.objects.create(follower=user, followed=user)


class Report_Model_Tests(Base_TestCase):
    def test_reported_object_is_not_only_available_assigned_moderator(self):
        moderator: User = Test_User_Factory.create()
        moderator.groups.add(Group.objects.get(name="Moderators"))

        with self.assertRaisesMessage(ValidationError, "This reported object refers to the only moderator available to be assigned to this report. Therefore, this moderator cannot be reported."):
            Test_Report_Factory.create(
                reported_object=moderator
            )

    def test_reported_object_is_not_admin(self):
        admin: User = Test_User_Factory.create()
        admin.groups.add(Group.objects.get(name="Admins"))

        with self.assertRaisesMessage(ValidationError, "This reported object refers to an admin. Admins cannot be reported."):
            Test_Report_Factory.create(
                reported_object=admin
            )

    def test_reported_object_is_not_content_of_admin(self):
        admin: User = Test_User_Factory.create()
        admin.groups.add(Group.objects.get(name="Admins"))

        model_name: str
        for model_name in {"pulse", "reply"}:
            content: pulsifi_models.User_Generated_Content_Model = pulsifi_tests_utils.get_model_factory(model_name).create(creator=admin)

            with self.assertRaisesMessage(ValidationError, "This reported object refers to a Pulse or Reply created by an Admin. These Pulses & Replies cannot be reported."):
                Test_Report_Factory.create(
                    reported_object=content
                )

    def test_reporter_is_not_only_available_assigned_moderator(self):
        moderator: User = Test_User_Factory.create()
        moderator.groups.add(Group.objects.get(name="Moderators"))

        with self.assertRaisesMessage(ValidationError, "This user cannot be the reporter because they are the only moderator available to be assigned to this report."):
            Test_Report_Factory.create(reporter=moderator)

    def test_reported_object_is_not_reporter(self):
        reported_user: User = Test_User_Factory.create()

        with self.assertRaisesMessage(ValidationError, "You cannot report yourself. Please choose a different object to report."):
            Test_Report_Factory.create(
                reporter=reported_user,
                reported_object=reported_user
            )

    def test_assigned_moderator_is_consistent(self):
        moderator1: User = Test_User_Factory.create()
        moderator2: User = Test_User_Factory.create()
        moderators_group = Group.objects.get(name="Moderators")
        moderator1.groups.add(moderators_group)
        moderator2.groups.add(moderators_group)

        report = Test_Report_Factory.create()

        original_assigned_moderator: User = report.assigned_moderator

        for _ in range(10):
            report.clean()

            self.assertEqual(
                original_assigned_moderator,
                report.assigned_moderator
            )

    def test_reported_object_is_not_content_of_reporter(self):
        reporter: User = Test_User_Factory.create()

        model_name: str
        for model_name in {"pulse", "reply"}:
            content: pulsifi_models.User_Generated_Content_Model = pulsifi_tests_utils.get_model_factory(model_name).create(creator=reporter)

            with self.assertRaisesMessage(ValidationError, "You cannot report your own content. Please choose a different object to report."):
                Test_Report_Factory.create(
                    reporter=reporter,
                    reported_object=content
                )

    def test_reported_object_is_not_content_of_only_available_assigned_moderator(self):
        moderator: User = Test_User_Factory.create()
        moderator.groups.add(Group.objects.get(name="Moderators"))

        model_name: str
        for model_name in {"pulse", "reply"}:
            content: pulsifi_models.User_Generated_Content_Model = pulsifi_tests_utils.get_model_factory(model_name).create(creator=moderator)

            with self.assertRaisesMessage(ValidationError, "This content cannot be reported because it was created by the only moderator available to be assigned to this report."):
                Test_Report_Factory.create(
                    reported_object=content
                )

    def test_reported_object_is_valid(self):
        for model_name in Report.REPORTABLE_CONTENT_TYPE_NAMES:
            with self.assertRaisesMessage(ValidationError, "Reported object must be valid object."):
                Test_Report_Factory.create(
                    _content_type=ContentType.objects.get(
                        app_label="pulsifi",
                        model=model_name
                    ),
                    _object_id=0
                )

    def test_unique_report_per_reporter_and_reported_object(self):
        reporter: User = Test_User_Factory.create()
        reported_user: User = Test_User_Factory.create()

        Test_Report_Factory.create(
            reporter=reporter,
            reported_object=reported_user
        )

        with self.assertRaisesMessage(ValidationError, "Report with this Reporter, Reported Object ID and Reported Object Type already exists."):
            Test_Report_Factory.create(
                reporter=reporter,
                reported_object=reported_user
            )
