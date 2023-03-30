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
from django.db import IntegrityError, models, transaction

from pulsifi.models import Follow, Report, User
from pulsifi.tests.utils import Base_TestCase, CreateTestUserGeneratedContentHelper, CreateTestUserHelper, GetFieldsHelper

get_user_model = auth.get_user_model  # NOTE: Adding external package functions to the global scope for frequent usage


# TODO: change assertRaises to assertRaisesMessage
# TODO: tests docstrings

class User_Model_Tests(Base_TestCase):
    def test_refresh_from_database_updates_non_relation_fields(self):  # TODO: test validators & validation errors from clean method
        user = CreateTestUserHelper.create_test_user()
        old_user: User = get_user_model().objects.get(id=user.id)

        self.assertEqual(user, old_user)

        for field in GetFieldsHelper.get_non_relation_fields(user, exclude=["id", "last_login", "date_joined"]):
            if field.name in CreateTestUserHelper.TEST_USERS[0]:
                setattr(
                    user,
                    field.name,
                    CreateTestUserHelper.get_test_field_value(field.name)
                )
            elif isinstance(field, models.BooleanField):
                setattr(user, field.name, not getattr(user, field.name))

            self.assertNotEqual(
                getattr(user, field.name),
                getattr(old_user, field.name)
            )
            user.refresh_from_db()
            self.assertEqual(
                getattr(old_user, field.name),
                getattr(user, field.name)
            )

    def test_delete_makes_not_active(self):
        user = CreateTestUserHelper.create_test_user()

        self.assertTrue(user.is_active)

        user.delete()
        user.refresh_from_db()

        self.assertFalse(user.is_active)

    def test_visible_shortcut_in_memory(self):
        user = CreateTestUserHelper.create_test_user()

        self.assertTrue(user.visible)
        self.assertTrue(user.is_active)

        user.visible = False

        self.assertFalse(user.visible)
        self.assertFalse(user.is_active)

    def test_visible_shortcut_in_database(self):
        user = CreateTestUserHelper.create_test_user()

        self.assertTrue(user.visible)
        self.assertTrue(user.is_active)

        user.update(visible=False)

        self.assertFalse(user.visible)
        self.assertFalse(user.is_active)

    def test_stringify_displays_in_correct_format(self):
        user = CreateTestUserHelper.create_test_user()

        self.assertEqual(f"@{user.username}", str(user))

        user.update(is_active=False)

        self.assertEqual(
            "".join(letter + "\u0336" for letter in f"@{user.username}"),
            str(user)
        )

    def test_user_becomes_superuser_put_in_admin_group(self):
        user = CreateTestUserHelper.create_test_user()
        admin_group = Group.objects.get(name="Admins")

        self.assertNotIn(admin_group, user.groups.all())

        user.update(is_superuser=True)

        self.assertIn(admin_group, user.groups.all())

    def test_superuser_has_groups_changed_kept_in_admin_group(self):
        user = CreateTestUserHelper.create_test_user(is_superuser=True)
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
        user = CreateTestUserHelper.create_test_user(is_superuser=True)
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
        user = CreateTestUserHelper.create_test_user()

        self.assertFalse(user.is_staff)

        user.update(is_superuser=True)

        self.assertTrue(user.is_staff)

    def test_user_added_to_staff_group_made_staff(self):
        staff_group_name: str
        for staff_group_name in get_user_model().STAFF_GROUP_NAMES:
            user = CreateTestUserHelper.create_test_user()
            group = Group.objects.get(name=staff_group_name)

            self.assertFalse(user.is_staff)

            user.groups.add(group)

            user.refresh_from_db()

            self.assertTrue(user.is_staff)

    def test_moderator_group_has_user_added_made_staff(self):
        staff_group_name: str
        for staff_group_name in get_user_model().STAFF_GROUP_NAMES:
            user = CreateTestUserHelper.create_test_user()
            group = Group.objects.get(name=staff_group_name)

            self.assertFalse(user.is_staff)

            group.user_set.add(user)

            user.refresh_from_db()

            self.assertTrue(user.is_staff)

    def test_user_cannot_be_in_own_following(self):
        user = CreateTestUserHelper.create_test_user()

        with self.assertRaisesMessage(IntegrityError, "CHECK constraint failed: not_follow_self"), transaction.atomic():
            user.add_following(user)

    def test_user_cannot_be_in_own_followers(self):
        user = CreateTestUserHelper.create_test_user()

        with self.assertRaisesMessage(IntegrityError, "CHECK constraint failed: not_follow_self"), transaction.atomic():
            user.add_followers(user)

    def test_non_staff_cannot_have_restricted_admin_username(self):
        for restricted_admin_username in settings.RESTRICTED_ADMIN_USERNAMES:
            with self.assertRaises(ValidationError) as e:
                CreateTestUserHelper.create_test_user(username=restricted_admin_username)
            self.assertEqual(1, len(e.exception.error_dict))
            self.assertEqual("username", e.exception.error_dict.popitem()[0])

    def test_staff_cannot_have_restricted_admin_username_when_already_max_admin_count(self):
        for restricted_admin_username in settings.RESTRICTED_ADMIN_USERNAMES:
            CreateTestUserHelper.create_test_user(
                username=f"{restricted_admin_username}test",
                is_staff=True
            )

            with self.assertRaises(ValidationError) as e:
                CreateTestUserHelper.create_test_user(
                    username=restricted_admin_username,
                    is_staff=True
                )
            self.assertEqual(1, len(e.exception.error_dict))
            self.assertEqual("username", e.exception.error_dict.popitem()[0])

    def test_dots_removed_from_local_part_of_email(self):
        local_email = "test.local.email"
        domain_email = "test.domain.email.com"
        user = CreateTestUserHelper.create_test_user(email="@".join([local_email, domain_email]))

        self.assertEqual("@".join([local_email.replace(".", ""), domain_email]), user.email)

    def test_plus_alias_removed_from_local_part_of_email(self):
        local_email = "test+local+email"
        domain_email = "test.domain.email.com"
        user = CreateTestUserHelper.create_test_user(email="@".join([local_email, domain_email]))

        self.assertEqual("@".join([local_email.split("+", maxsplit=1)[0], domain_email]), user.email)

    def test_google_email_alias_replaced(self):
        local_email = "test"
        domain_email = "googlemail.com"
        user = CreateTestUserHelper.create_test_user(email="@".join([local_email, domain_email]))

        self.assertEqual("@".join([local_email, "gmail.com"]), user.email)

    def test_verified_user_must_have_at_least_one_verified_email(self):
        with self.assertRaisesMessage(ValidationError, "User cannot become verified without at least one verified email address."):
            CreateTestUserHelper.create_test_user(verified=True)

        user = CreateTestUserHelper.create_test_user()
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

    def test_verify_not_duplicate_email_attribute(self):
        user = CreateTestUserHelper.create_test_user()

        with self.assertRaisesMessage(ValidationError, "That Email Address is already in use by another user."):
            CreateTestUserHelper.create_test_user(email=user.email)

    def test_verify_not_duplicate_email_object(self):
        user = CreateTestUserHelper.create_test_user()
        allauth_utils.sync_user_email_addresses(user)
        old_email = user.email
        user.update(email=CreateTestUserHelper.get_test_field_value("email"))

        with self.assertRaisesMessage(ValidationError, "That Email Address is already in use by another user."):
            CreateTestUserHelper.create_test_user(email=old_email)

    def test_reverse_liked_content_becoming_disliked_removes_like(self):
        user1 = CreateTestUserHelper.create_test_user()
        user2 = CreateTestUserHelper.create_test_user()
        for model in ["pulse", "reply"]:
            content = CreateTestUserGeneratedContentHelper.create_test_user_generated_content(model, creator=user1)

            if model == "pulse":
                user2.liked_pulse_set.add(content)
            elif model == "reply":
                user2.liked_reply_set.add(content)

            self.assertTrue(content.liked_by.filter(id=user2.id).exists())
            self.assertFalse(content.disliked_by.filter(id=user2.id).exists())

            if model == "pulse":
                user2.disliked_pulse_set.add(content)
            elif model == "reply":
                user2.disliked_reply_set.add(content)

            self.assertTrue(content.disliked_by.filter(id=user2.id).exists())
            self.assertFalse(content.liked_by.filter(id=user2.id).exists())

    def test_reverse_disliked_content_becoming_liked_removes_dislike(self):
        user1 = CreateTestUserHelper.create_test_user()
        user2 = CreateTestUserHelper.create_test_user()
        for model in ["pulse", "reply"]:
            content = CreateTestUserGeneratedContentHelper.create_test_user_generated_content(model, creator=user1)

            if model == "pulse":
                user2.disliked_pulse_set.add(content)
            elif model == "reply":
                user2.disliked_reply_set.add(content)

            self.assertTrue(content.disliked_by.filter(id=user2.id).exists())
            self.assertFalse(content.liked_by.filter(id=user2.id).exists())

            if model == "pulse":
                user2.liked_pulse_set.add(content)
            elif model == "reply":
                user2.liked_reply_set.add(content)

            self.assertTrue(content.liked_by.filter(id=user2.id).exists())
            self.assertFalse(content.disliked_by.filter(id=user2.id).exists())

    def test_obsolete_fields_from_base_user_class_are_none(self):
        user = CreateTestUserHelper.create_test_user()

        self.assertIsNone(user.first_name)
        self.assertIsNone(user.last_name)

        with self.assertRaises(FieldDoesNotExist):
            user.update(first_name="test_value")

        self.assertIsNone(user.first_name)

        with self.assertRaises(FieldDoesNotExist):
            user.update(last_name="test_value")

        self.assertIsNone(user.last_name)


class Follow_Model_Tests(Base_TestCase):
    def test_cannot_have_same_follower_as_followee(self):
        user = CreateTestUserHelper.create_test_user()

        with self.assertRaisesMessage(ValidationError, "not_follow_self"):
            Follow.objects.create(follower=user, followed=user)


class _User_Generated_Content_Model_Tests(Base_TestCase):  # TODO: test validation errors from clean method
    def test_liked_content_becoming_disliked_removes_like(self):
        user1 = CreateTestUserHelper.create_test_user()
        user2 = CreateTestUserHelper.create_test_user()

        for model in ["pulse", "reply"]:
            content = CreateTestUserGeneratedContentHelper.create_test_user_generated_content(model, creator=user1)

            content.liked_by.add(user2)

            self.assertTrue(content.liked_by.filter(id=user2.id).exists())
            self.assertFalse(content.disliked_by.filter(id=user2.id).exists())

            content.disliked_by.add(user2)

            self.assertTrue(content.disliked_by.filter(id=user2.id).exists())
            self.assertFalse(content.liked_by.filter(id=user2.id).exists())

    def test_disliked_content_becoming_liked_removes_dislike(self):
        user1 = CreateTestUserHelper.create_test_user()
        user2 = CreateTestUserHelper.create_test_user()
        for model in ["pulse", "reply"]:
            content = CreateTestUserGeneratedContentHelper.create_test_user_generated_content(model, creator=user1)

            content.disliked_by.add(user2)

            self.assertTrue(content.disliked_by.filter(id=user2.id).exists())
            self.assertFalse(content.liked_by.filter(id=user2.id).exists())

            content.liked_by.add(user2)

            self.assertTrue(content.liked_by.filter(id=user2.id).exists())
            self.assertFalse(content.disliked_by.filter(id=user2.id).exists())

    def test_stringify_displays_in_correct_format(self):
        for model in ["pulse", "reply"]:
            content = CreateTestUserGeneratedContentHelper.create_test_user_generated_content(model)

            if model == "pulse":
                self.assertEqual(
                    f"{content.creator}, {content.message[:settings.MESSAGE_DISPLAY_LENGTH]}",
                    str(content)
                )
            if model == "reply":
                self.assertEqual(
                    f"{content.creator}, {content.message[:settings.MESSAGE_DISPLAY_LENGTH]} (For object - {content._content_type.name} | {content.replied_content})"[:100],
                    str(content)
                )

            content.update(is_visible=False)

            if model == "pulse":
                self.assertEqual(
                    f"{content.creator}, " + "".join(letter + "\u0336" for letter in content.message[:settings.MESSAGE_DISPLAY_LENGTH]),
                    str(content)
                )
            if model == "reply":
                self.assertEqual(
                    (f"{content.creator}, " + "".join(letter + "\u0336" for letter in content.message[:settings.MESSAGE_DISPLAY_LENGTH]) + f" (For object - {content._content_type.name} | {content.replied_content})")[:100],
                    str(content)
                )


class Report_Model_Tests(Base_TestCase):
    def test_assigned_staff_is_not_reported_object(self):
        user1 = CreateTestUserHelper.create_test_user()
        user2 = CreateTestUserHelper.create_test_user()
        user2.groups.add(Group.objects.get(name="Moderators"))

        with self.assertRaises(ValidationError) as e:
            Report.objects.create(
                reporter=user1,
                _content_type=ContentType.objects.get_for_model(user2),
                _object_id=user2.id,
                reason="test reason message",
                category=Report.Categories.SPAM
            )
        self.assertEqual(1, len(e.exception.error_dict))
        self.assertEqual("_object_id", e.exception.error_dict.popitem()[0])

    def test_content_created_by_admin_cannot_be_reported(self):
        user1 = CreateTestUserHelper.create_test_user()
        user2 = CreateTestUserHelper.create_test_user()
        user3 = CreateTestUserHelper.create_test_user()
        user2.groups.add(Group.objects.get(name="Admins"))
        user3.groups.add(Group.objects.get(name="Moderators"))
        for model in ["pulse", "reply"]:
            content = CreateTestUserGeneratedContentHelper.create_test_user_generated_content(model, creator=user2)

            with self.assertRaises(ValidationError) as e:
                Report.objects.create(
                    reporter=user1,
                    _content_type=ContentType.objects.get_for_model(content),
                    _object_id=content.id,
                    reason="test reason message",
                    category=Report.Categories.SPAM
                )
            self.assertEqual(1, len(e.exception.error_dict))
            self.assertEqual("_object_id", e.exception.error_dict.popitem()[0])

    def test_reported_user_is_not_the_only_moderator(self):
        user1 = CreateTestUserHelper.create_test_user()
        user2 = CreateTestUserHelper.create_test_user()
        user2.groups.add(Group.objects.get(name="Moderators"))

        with self.assertRaises(ValidationError) as e:
            Report.objects.create(
                reporter=user1,
                _content_type=ContentType.objects.get_for_model(user2),
                _object_id=user2.id,
                reason="test reason message",
                category=Report.Categories.SPAM
            )
        self.assertEqual(1, len(e.exception.error_dict))
        self.assertEqual("_object_id", e.exception.error_dict.popitem()[0])

    def test_reporter_is_not_the_only_moderator(self):
        user1 = CreateTestUserHelper.create_test_user()
        user2 = CreateTestUserHelper.create_test_user()
        user2.groups.add(Group.objects.get(name="Moderators"))
        for model in ["pulse", "reply"]:
            content = CreateTestUserGeneratedContentHelper.create_test_user_generated_content(model, creator=user1)

            with self.assertRaises(ValidationError) as e:
                Report.objects.create(
                    reporter=user2,
                    _content_type=ContentType.objects.get_for_model(content),
                    _object_id=content.id,
                    reason="test reason message",
                    category=Report.Categories.SPAM
                )
            self.assertEqual(1, len(e.exception.error_dict))
            self.assertEqual("reporter", e.exception.error_dict.popitem()[0])
