"""
    Utility classes for pulsifi app test suite.
"""
import abc
import json
from typing import Iterator, Type

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from pulsifi.models import Pulse, Reply, Report, User

GENERATABLE_MODELS_NAMES: set[str] = {"user", "pulse", "reply", "report"}

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
    def setUp(self):
        """
            Hook method for setting up the test fixture before exercising it.

            All staff Group instances must be created before tests are run.
        """

        staff_group_name: str
        for staff_group_name in get_user_model().STAFF_GROUP_NAMES:
            Group.objects.create(name=staff_group_name)

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
    def _create_field_value(cls, field_name: str):
        raise NotImplementedError

    @classmethod
    def create_field_value(cls, field_name: str):
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
        visible: bool | None = kwargs.pop("visible", None)

        if is_active != visible and is_active is not None and visible is not None:
            raise ValueError("User attribute <is_active> cannot be set to a different value from the User attribute <visible>.")

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
            return next(cls.test_usernames_iterator)
        elif field_name == "password":
            return next(cls.test_passwords_iterator)
        elif field_name == "email":
            return next(cls.test_emails_iterator)
        elif field_name == "bio":
            return next(cls.test_bios_iterator)


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
            return next(cls.test_messages_iterator)


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
        if (visible := kwargs.pop("visible", None)) is not None:
            pulse_kwargs["visible"] = visible

        creator_kwargs: dict[str, ...] = kwargs.copy()
        if (creator_visible := kwargs.pop("creator_visible", None)) is not None:
            creator_kwargs["visible"] = creator_visible

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
        if (visible := kwargs.pop("visible", None)) is not None:
            reply_kwargs["visible"] = visible

        creator_kwargs: dict[str, ...] = {}
        field_name: str
        for field_name in get_user_model().get_non_relation_fields(names=True) - (Pulse.get_non_relation_fields(names=True) | Reply.get_non_relation_fields(names=True)):
            if (field_value := kwargs.pop(field_name, None)) is not None:
                creator_kwargs[field_name] = field_value
        if (creator_visible := kwargs.pop("creator_visible", None)) is not None:
            creator_kwargs["visible"] = creator_visible

        creator: User = kwargs.pop("creator", None) or Test_User_Factory.create(**creator_kwargs)

        replied_content_kwargs: dict[str, ...] = kwargs.copy()
        if (replied_content_message := kwargs.pop("replied_content_message", None)) is not None:
            replied_content_kwargs["message"] = replied_content_message
        if (replied_content_visible := kwargs.pop("replied_content_visible", None)) is not None:
            replied_content_kwargs["visible"] = replied_content_visible

        replied_content: Pulse | Reply = kwargs.pop("replied_content", None) or Test_Pulse_Factory.create(**replied_content_kwargs)

        if save:
            return Reply.objects.create(
                message=message,
                creator=creator,
                replied_content=replied_content,
                **reply_kwargs
            )
        else:
            return Reply(
                message=message,
                creator=creator,
                replied_content=replied_content,
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
        if (_object_id := kwargs.pop("_object_id", None)) is not None:
            report_kwargs["_object_id"] = _object_id

        reporter_kwargs: dict[str, ...] = {}
        field_name: str
        for field_name in get_user_model().get_non_relation_fields(names=True) - (Pulse.get_non_relation_fields(names=True) | Reply.get_non_relation_fields(names=True)):
            if (field_value := kwargs.pop(field_name, None)) is not None:
                reporter_kwargs[field_name] = field_value
        if (reporter_visible := kwargs.pop("reporter_visible", None)) is not None:
            reporter_kwargs["visible"] = reporter_visible

        reporter: User = kwargs.pop("reporter", None) or Test_User_Factory.create(**reporter_kwargs)

        reported_object_kwargs: dict[str, ...] = kwargs.copy()
        if (reported_object_visible := kwargs.pop("reported_object_visible", None)) is not None:
            reported_object_kwargs["visible"] = reported_object_visible

        if reported_object is None and _content_type is None and _object_id is None:
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
            return next(cls.test_reasons_iterator)
