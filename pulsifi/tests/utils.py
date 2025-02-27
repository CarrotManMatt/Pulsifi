"""
    Utility classes for pulsifi app test suite.
"""

import abc
import datetime
import json
import random
import string
from typing import Iterator, Type

from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from pulsifi.exceptions import NotEnoughTestDataError
from pulsifi.models import Pulse, Reply, Report, User

PULSIFI_GENERATABLE_MODELS_NAMES: set[str] = {"user", "pulse", "reply", "report"}

TEST_DATA = {}
if settings.TEST_DATA_JSON_FILE_PATH:
    with open(settings.TEST_DATA_JSON_FILE_PATH, "r") as test_data_json_file:
        TEST_DATA = json.load(test_data_json_file)


def get_field_test_data(model_name: str, field_name: str) -> set[str]:
    """
        Returns the set of test data values for the given model_name and
        field_name, from the test data JSON file.
    """

    if not TEST_DATA:
        raise ImproperlyConfigured(f"TEST_DATA_JSON_FILE_PATH cannot be empty when running tests.")

    return set(TEST_DATA[model_name][field_name])


class Base_TestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        """
            Hook method for setting up the test data more efficiently.

            All staff Group instances must be created before tests are run.
        """

        staff_groups: dict[str, Group] = {}

        staff_group_name: str
        for staff_group_name in get_user_model().STAFF_GROUP_NAMES:
            staff_groups[staff_group_name] = Group.objects.create(name=staff_group_name)

        cls.staff_groups: dict[str, Group] = staff_groups

    def setUp(self):
        """
            Hook method for setting up the test fixture before exercising it.
        """

        Test_User_Factory.restart_iterators()
        Base_Test_User_Generated_Content_Factory.restart_iterators()
        Test_Report_Factory.restart_iterators()


def get_model_factory(model_name: str) -> Type["Base_Test_Data_Factory"]:
    """
        Returns the Factory class that can create an instance of the model
        provided in the parameter model_name.
    """

    if model_name == "user":
        return Test_User_Factory
    elif model_name == "pulse":
        return Test_Pulse_Factory
    elif model_name == "reply":
        return Test_Reply_Factory
    elif model_name == "report":
        return Test_Report_Factory
    elif model_name == "social_account":
        return Test_Social_Account_Factory


class Base_Test_Data_Factory(abc.ABC):
    """
        Helper class to provide functions that create test object instances of
        any model within the pulsifi app.
    """

    # noinspection PyPropertyDefinition,PyPep8Naming
    @classmethod
    @property
    @abc.abstractmethod
    def GENERATABLE_FIELDS(cls) -> set[str]:
        """
            The names of the fields of the model that this factory creates,
            that can be autogenerated from example data.
        """

        raise NotImplementedError

    @classmethod
    def restart_iterators(cls) -> None:
        """
            Restarts all iterators that generate test data values to the
            beginning of their iterable again.
        """

        pass

    @classmethod
    @abc.abstractmethod
    def create(cls, *, save=True, **kwargs):
        """
            Helper function that creates & returns a test object instance, with
            additional options for its attributes provided in kwargs. The save
            argument declares whether the object instance should be saved to
            the database or not.
        """

        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def _create_field_value(cls, field_name: str) -> str:
        raise NotImplementedError

    @classmethod
    def create_field_value(cls, field_name: str) -> str:
        """
            Helper function to return a new arbitrary value for the given field
            name.
        """

        if field_name not in cls.GENERATABLE_FIELDS:
            raise ValueError(f"Given field_name ({field_name}) is not one that can have test values created for it.")

        return cls._create_field_value(field_name)


class Test_User_Factory(Base_Test_Data_Factory):
    """
        Helper class to provide functions that create test data for
        :model:`pulsifi.user` object instances.
    """

    GENERATABLE_FIELDS: set[str] = {
        "username",
        "password",
        "email",
        "bio"
    }
    test_usernames_iterator: Iterator[str] = iter(get_field_test_data("user", "username"))
    test_passwords_iterator: Iterator[str] = iter(get_field_test_data("user", "password"))
    test_emails_iterator: Iterator[str] = iter(get_field_test_data("user", "email"))
    test_bios_iterator: Iterator[str] = iter(get_field_test_data("user", "bio"))

    @classmethod
    def restart_iterators(cls) -> None:
        """
            Restarts all iterators that generate test user details values to
            the beginning of their iterable again.
        """

        cls.test_usernames_iterator = iter(get_field_test_data("user", "username"))
        cls.test_passwords_iterator = iter(get_field_test_data("user", "password"))
        cls.test_emails_iterator = iter(get_field_test_data("user", "email"))
        cls.test_bios_iterator = iter(get_field_test_data("user", "bio"))

    @classmethod
    def create(cls, *, save=True, **kwargs) -> User:
        """
            Helper function that creates & returns a test :model:`pulsifi.user`
            object instance, with additional options for its attributes
            provided in kwargs. The save argument declares whether the
            :model:`pulsifi.user` instance should be saved to the database or
            not.
        """

        username: str = kwargs.pop("username", None) or cls.create_field_value("username")
        password: str = kwargs.pop("password", None) or cls.create_field_value("password")
        email: str = kwargs.pop("email", None) or cls.create_field_value("email")
        bio: str = kwargs.pop("bio", None) or cls.create_field_value("bio")

        is_active: bool | None = kwargs.get("is_active", None)
        is_visible: bool | None = kwargs.pop("is_visible", None)

        if is_active != is_visible and is_active is not None and is_visible is not None:
            raise ValueError("User attribute <is_active> cannot be set to a different value from the User attribute <is_visible>.")

        if save:
            return get_user_model().objects.create_user(
                username=username,
                password=password,
                email=email,
                bio=bio,
                **kwargs
            )
        else:
            return get_user_model()(
                username=username,
                password=password,
                email=email,
                bio=bio,
                **kwargs
            )

    @classmethod
    def _create_field_value(cls, field_name: str) -> str:
        if field_name == "username":
            try:
                return next(cls.test_usernames_iterator)
            except StopIteration as e:
                raise NotEnoughTestDataError(field_name=field_name) from e
        elif field_name == "password":
            try:
                return next(cls.test_passwords_iterator)
            except StopIteration as e:
                raise NotEnoughTestDataError(field_name=field_name) from e
        elif field_name == "email":
            try:
                return next(cls.test_emails_iterator)
            except StopIteration as e:
                raise NotEnoughTestDataError(field_name=field_name) from e
        elif field_name == "bio":
            try:
                return next(cls.test_bios_iterator)
            except StopIteration as e:
                raise NotEnoughTestDataError(field_name=field_name) from e


class Base_Test_User_Generated_Content_Factory(Base_Test_Data_Factory, abc.ABC):
    """
        Helper class to provide functions that create test data for
        User_Generated_Content objects.
    """

    GENERATABLE_FIELDS: set[str] = {"message"}
    test_messages_iterator: Iterator[str] = iter(get_field_test_data("user_generated_content", "message"))

    @classmethod
    def restart_iterators(cls) -> None:
        """
            Restarts the iterator that generates test message values to the
            beginning of its iterable again.
        """

        cls.test_messages_iterator = iter(get_field_test_data("user_generated_content", "message"))

    @classmethod
    def _create_field_value(cls, field_name: str) -> str:
        if field_name == "message":
            try:
                return next(cls.test_messages_iterator)
            except StopIteration as e:
                raise NotEnoughTestDataError(field_name=field_name) from e


class Test_Pulse_Factory(Base_Test_User_Generated_Content_Factory):
    """
        Helper class to provide functions that create test data for
        :model:`pulsifi.pulse` objects.
    """

    @classmethod
    def create(cls, *, save=True, **kwargs) -> Pulse:
        """
            Helper function that creates & returns a test
            :model:`pulsifi.pulse` object instance, with additional options for
            its attributes provided in kwargs. The save argument declares
            whether the :model:`pulsifi.pulse` object instance should be saved
            to the database or not.

            (Additional keyword arguments not used to construct this
            :model:`pulsifi.pulse` object, will be used to construct its
            creator :model:`pulsifi.user` object).
        """

        message: str = kwargs.pop("message", None) or cls.create_field_value("message")

        pulse_kwargs: dict[str, ...] = {}
        if (is_visible := kwargs.pop("is_visible", None)) is not None:
            pulse_kwargs["is_visible"] = is_visible

        creator_kwargs: dict[str, ...] = kwargs.copy()
        if (creator__is_visible := kwargs.pop("creator__is_visible", None)) is not None:
            creator_kwargs["is_visible"] = creator__is_visible

        creator: User = kwargs.pop("creator", None) or Test_User_Factory.create(**creator_kwargs)

        if save:
            return Pulse.objects.create(
                message=message,
                creator=creator,
                **pulse_kwargs
            )
        else:
            return Pulse(
                message=message,
                creator=creator,
                **pulse_kwargs
            )


class Test_Reply_Factory(Base_Test_User_Generated_Content_Factory):
    """
        Helper class to provide functions that create test data for
        :model:`pulsifi.reply` objects.
    """

    @classmethod
    def create(cls, *, save=True, **kwargs) -> Reply:
        """
            Helper function that creates & returns a test
            :model:`pulsifi.reply` object instance, with additional options for
            its attributes provided in kwargs. The save argument declares
            whether the :model:`pulsifi.reply` object instance should be saved
            to the database or not.

            (Additional keyword arguments not used to construct this
            :model:`pulsifi.reply` object, or its creator :model:`pulsifi.user`
            object will be used to construct its replied_content object).
        """

        message: str = kwargs.pop("message", None) or cls.create_field_value("message")

        reply_kwargs: dict[str, ...] = {}
        if (is_visible := kwargs.pop("is_visible", None)) is not None:
            reply_kwargs["is_visible"] = is_visible
        if (replied_content := kwargs.pop("replied_content", None)) is not None:
            reply_kwargs["replied_content"] = replied_content
        if (_content_type := kwargs.pop("_content_type", None)) is not None:
            reply_kwargs["_content_type"] = _content_type
        if (_content_type_id := kwargs.pop("_content_type_id", None)) is not None:
            reply_kwargs["_content_type_id"] = _content_type_id
        if (_object_id := kwargs.pop("_object_id", None)) is not None:
            reply_kwargs["_object_id"] = _object_id

        creator_kwargs: dict[str, ...] = {}
        field_name: str
        for field_name in get_user_model().get_non_relation_fields(names=True) - (Pulse.get_non_relation_fields(names=True) | Reply.get_non_relation_fields(names=True)):
            if (field_value := kwargs.pop(f"creator__{field_name}", None)) is not None:
                creator_kwargs[field_name] = field_value
        if (creator__is_visible := kwargs.pop("creator__is_visible", None)) is not None:
            creator_kwargs["is_visible"] = creator__is_visible

        creator: User = kwargs.pop("creator", None) or Test_User_Factory.create(**creator_kwargs)

        replied_content_kwargs: dict[str, ...] = kwargs.copy()
        if (replied_content__message := kwargs.pop("replied_content__message", None)) is not None:
            replied_content_kwargs["message"] = replied_content__message
        if (replied_content__is_visible := kwargs.pop("replied_content__is_visible", None)) is not None:
            replied_content_kwargs["is_visible"] = replied_content__is_visible

        if (replied_content is None and _content_type is None and _content_type_id is None) or (replied_content is None and _object_id is None):
            reply_kwargs["replied_content"] = Test_Pulse_Factory.create(**replied_content_kwargs)

        if save:
            return Reply.objects.create(
                message=message,
                creator=creator,
                **reply_kwargs
            )
        else:
            return Reply(
                message=message,
                creator=creator,
                **reply_kwargs
            )


class Test_Report_Factory(Base_Test_Data_Factory):
    """
        Helper class to provide functions that create test data for
        :model:`pulsifi.report` objects.
    """

    GENERATABLE_FIELDS: set[str] = {"reason"}
    test_reasons_iterator: Iterator[str] = iter(get_field_test_data("report", "reason"))

    @classmethod
    def restart_iterators(cls) -> None:
        """
            Restarts the iterator that generates test reason values to the
            beginning of its iterable again.
        """

        cls.test_reasons_iterator = iter(get_field_test_data("report", "reason"))

    @classmethod
    def create(cls, *, save=True, **kwargs) -> Report:
        """
            Helper function that creates & returns a test
            :model:`pulsifi.report` object instance, with additional options
            for its attributes provided in kwargs. The save argument declares
            whether the :model:`pulsifi.report` object instance should be saved
            to the database or not.

            (Additional keyword arguments not used to construct this
            :model:`pulsifi.report` object, or its reporter
            :model:`pulsifi.user` object will be used to construct its
            :model:`pulsifi.pulse` reported_object).
        """

        reason: str = kwargs.pop("reason", None) or cls.create_field_value("reason")

        report_kwargs: dict[str, ...] = {}
        if (reported_object := kwargs.pop("reported_object", None)) is not None:
            report_kwargs["reported_object"] = reported_object
        if (_content_type := kwargs.pop("_content_type", None)) is not None:
            report_kwargs["_content_type"] = _content_type
        if (_content_type_id := kwargs.pop("_content_type_id", None)) is not None:
            report_kwargs["_content_type_id"] = _content_type_id
        if (_object_id := kwargs.pop("_object_id", None)) is not None:
            report_kwargs["_object_id"] = _object_id

        reporter_kwargs: dict[str, ...] = {}
        field_name: str
        for field_name in get_user_model().get_non_relation_fields(names=True) - (Pulse.get_non_relation_fields(names=True) | Reply.get_non_relation_fields(names=True)):
            if (field_value := kwargs.pop(field_name, None)) is not None:
                reporter_kwargs[field_name] = field_value
        if (reporter__is_visible := kwargs.pop("reporter__is_visible", None)) is not None:
            reporter_kwargs["is_visible"] = reporter__is_visible

        reporter: User = kwargs.pop("reporter", None) or Test_User_Factory.create(**reporter_kwargs)

        reported_object_kwargs: dict[str, ...] = kwargs.copy()
        if (reported_object_visible := kwargs.pop("reported_object_visible", None)) is not None:
            reported_object_kwargs["visible"] = reported_object_visible

        if (reported_object is None and _content_type is None and _content_type_id is None) or (reported_object is None and _object_id is None):
            report_kwargs["reported_object"] = Test_Pulse_Factory.create(**reported_object_kwargs)

        if not get_user_model().objects.filter(groups__name="Moderators").exists():
            moderator = Test_User_Factory.create()
            moderator.groups.add(Group.objects.get(name="Moderators"))

        if save:
            return Report.objects.create(
                reporter=reporter,
                reason=reason,
                category=next(iter(Report.Categories.values)),
                **report_kwargs
            )
        else:
            report = Report(
                reporter=reporter,
                reason=reason,
                category=next(iter(Report.Categories.values)),
                **report_kwargs
            )
            report.full_clean()
            return report

    @classmethod
    def _create_field_value(cls, field_name: str) -> str:
        if field_name == "reason":
            try:
                return next(cls.test_reasons_iterator)
            except StopIteration as e:
                raise NotEnoughTestDataError(field_name=field_name) from e


class Test_Social_Account_Factory(Base_Test_Data_Factory):
    # noinspection SpellCheckingInspection
    """
        Helper class to provide functions that create test data for
        :model:`socialaccount.socialaccount` object instances.
    """

    GENERATABLE_FIELDS: set[str] = {"discord_uid", "github_uid", "google_uid"}
    AVAILABLE_PROVIDERS: set[str] = {"discord", "google", "github"}

    @classmethod
    def create(cls, *, save=True, **kwargs) -> SocialAccount:
        # noinspection SpellCheckingInspection
        """
            Helper function that creates & returns a test
            :model:`socialaccount.socialaccount` object instance, with
            additional options for its attributes provided in kwargs. The save
            argument declares whether the :model:`socialaccount.socialaccount`
            instance should be saved to the database or not.
        """

        user_kwargs: dict[str, ...] = {}

        field_name: str
        for field_name in get_user_model().get_non_relation_fields(names=True) - {"id", "last_login", "date_joined"}:
            if (field_value := kwargs.pop(f"user__{field_name}", None)) is not None:
                user_kwargs[field_name] = field_value

        if (user__is_visible := kwargs.pop("user__is_visible", None)) is not None:
            user_kwargs["is_visible"] = user__is_visible

        user: User = kwargs.pop("user", None) or Test_User_Factory.create(**user_kwargs)

        try:
            provider: str = kwargs.pop("provider")
        except KeyError as e:
            raise TypeError("create() missing 1 required argument: \"provider\"") from e

        uid: int | None = None

        extra_data: dict[str, str | int | None] = {}

        if provider not in cls.AVAILABLE_PROVIDERS:
            raise ValueError(f"Argument <provider> must be one of " + ", ".join(f"\"{available_provider}\"" for available_provider in cls.AVAILABLE_PROVIDERS))

        elif provider == "discord":
            uid: int = int(cls.create_field_value("discord_uid"))

            extra_data = {
                "id": uid,
                "username": user.username,
                "global_name": user.username,
                "display_name": user.username,
                "avatar": f"{random.randint(0, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF):032x}",
                "discriminator": f"{random.randint(0, 9999):04}",
                "public_flags": 0,
                "flags": 0,
                "banner": None,
                "banner_color": f"#{random.randint(0x00, 0xFF):02x}{random.randint(0x00, 0xFF):02x}{random.randint(0x00, 0xFF):02x}",
                "accent_color": random.randint(0x000000, 0xFFFFFF),
                "locale": "en-GB",
                "mfa_enabled": False,
                "premium_type": 0,
                "avatar_decoration": True,
                "email": user.email,
                "verified": True
            }

        elif provider == "google":
            uid: int = int(cls.create_field_value("google_uid"))
            google_content_link: str = f"""{random.randint(100000000000, 999999999999):012}-{"".join(random.choices(string.ascii_lowercase + string.digits, k=32))}.apps.googleusercontent.com"""

            extra_data = {
                "iss": "https://accounts.google.com",
                "azp": google_content_link,
                "aud": google_content_link,
                "sub": f"{random.randint(100000000000000000000, 999999999999999999999):021}",
                "email": user.email,
                "email_verified": True,
                "at_hash": "".join(random.choices(string.ascii_letters + string.digits, k=22)),
                "name": user.username,
                "picture": f"""https://lh3.googleusercontent.com/a/{"".join(random.choices(string.ascii_letters + string.digits, k=44))}=s96-c""",
                "given_name": user.username[:int(len(user.username) / 2)],
                "family_name": user.username[int(len(user.username) / 2):],
                "locale": "en-GB",
                "iat": random.randint(1000000000, 9999999999),
                "exp": random.randint(1000000000, 9999999999)
            }

        elif provider == "github":
            uid: int = int(cls.create_field_value("github_uid"))

            extra_data = {
                "login": "Pulsifi-app",
                "id": uid,
                "avatar_url": f"https://avatars.githubusercontent.com/u/{uid}?v=4",
                "gravatar_id": "",
                "url": f"https://api.github.com/users/{user.username}",
                "html_url": f"https://github.com/{user.username}",
                "followers_url": f"https://api.github.com/users/{user.username}/followers",
                "following_url": f"https://api.github.com/users/{user.username}/following{{/other_user}}",
                "gists_url": f"https://api.github.com/users/{user.username}/gists{{/gist_id}}",
                "starred_url": f"https://api.github.com/users/{user.username}/starred{{/owner}}{{/repo}}",
                "subscriptions_url": f"https://api.github.com/users/{user.username}/subscriptions",
                "organizations_url": f"https://api.github.com/users/{user.username}/orgs",
                "repos_url": f"https://api.github.com/users/{user.username}/repos",
                "events_url": f"https://api.github.com/users/{user.username}/events{{/privacy}}",
                "received_events_url": f"https://api.github.com/users/{user.username}/received_events",
                "type": "User",
                "site_admin": False,
                "name": user.username,
                "company": None,
                "blog": None,
                "location": None,
                "email": user.email,
                "hireable": None,
                "bio": user.bio,
                "twitter_username": None,
                "public_repos": 0,
                "public_gists": 0,
                "followers": 0,
                "following": 0,
                "created_at": datetime.datetime.now().strftime("%FT%TZ"),
                "updated_at": datetime.datetime.now().strftime("%FT%TZ")
            }

        if save:
            return SocialAccount.objects.create(
                user=user,
                provider=provider,
                uid=uid,
                extra_data=extra_data
            )
        else:
            return SocialAccount(
                user=user,
                provider=provider,
                uid=uid,
                extra_data=extra_data
            )

    @classmethod
    def _create_field_value(cls, field_name: str) -> str:
        if field_name == "discord_uid":
            return f"{random.randint(10000000, 999999999999999999):018}"

        elif field_name == "github_uid":
            return f"{random.randint(100101000, 130658469):09}"

        elif field_name == "google_uid":
            return f"{random.randint(10000000, 999999999999999999999):021}"
