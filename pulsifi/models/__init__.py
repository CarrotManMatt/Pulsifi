"""
    Models in pulsifi app.
"""

import abc
import logging
import random

import tldextract
from allauth import utils as allauth_core_utils
from allauth.account import utils as allauth_utils
from allauth.account.models import EmailAddress
from django import urls as django_urls_utils
from django.conf import settings
from django.contrib import auth
from django.contrib.auth.models import AbstractUser, Group
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from thefuzz import fuzz as thefuzz
from tldextract.tldextract import ExtractResult as TLD_ExtractResult

from pulsifi.models import utils as pulsifi_models_utils
from pulsifi.validators import ConfusableEmailValidator, ConfusableStringValidator, ExampleEmailValidator, FreeEmailValidator, HTML5EmailValidator, PreexistingEmailTLDValidator, ReservedNameValidator

get_user_model = auth.get_user_model  # NOTE: Adding external package functions to the global scope for frequent usage
abstractmethod = abc.abstractmethod


class _Visible_Reportable_Mixin(pulsifi_models_utils.Custom_Base_Model):
    """
        Model mixin that prevents objects from actually being deleted (making
        them invisible instead), as well as allowing all objects of this type
        to have reports made about them.

        This class is abstract so should not be instantiated or have a table
        made for it in the database (see
        https://docs.djangoproject.com/en/4.1/topics/db/models/#abstract-base-classes).
    """

    about_object_report_set = GenericRelation(
        "Report",
        content_type_field="_content_type",
        object_id_field="_object_id",
        related_query_name="reverse_parent_object",
        verbose_name="Reports About This Object",
        help_text="Provides a link to the set of all :model:`pulsifi.report` objects that are reporting this object."
    )
    """
        Provides a link to the set of all :model:`pulsifi.report` objects that
        are reporting this object.
    """

    # noinspection PyMissingOrEmptyDocstring
    class Meta:
        abstract = True

    @property
    @abstractmethod
    def is_visible(self) -> bool:
        """
            Boolean flag to determine whether this object should be accessible
            to the website. Use this flag instead of deleting objects.
        """

        raise NotImplementedError

    @is_visible.setter
    @abstractmethod
    def is_visible(self, value: bool) -> None:
        raise NotImplementedError

    def delete(self, *_args, **_kwargs) -> tuple[int, dict[str, int]]:
        """
            Sets this instance's is_visible field to False instead of deleting this
            instance's data from the database.

            Uses django's argument structure so cannot be changed (see
            https://docs.djangoproject.com/en/4.1/ref/models/instances/#django.db.models.Model.delete).
        """

        self.is_visible = False
        self.save()

        return 0, {}

    @abstractmethod
    def get_absolute_url(self):
        """
            Returns the canonical URL for this object instance.

            Uses django's argument structure so cannot be changed (see
            https://docs.djangoproject.com/en/4.1/ref/models/instances/#django.db.models.Model.get_absolute_url).
        """

        raise NotImplementedError

    def string_when_visible(self, string: str):
        """
            Returns the given string, or the given string but crossed out if
            this object is not visible.

            (string gets crossed out by adding the unicode strikethrough
            character between every character in the string).
        """

        if self.is_visible:
            return string
        return "".join(f"{char}\u0336" for char in string)


class User_Generated_Content_Model(_Visible_Reportable_Mixin, pulsifi_models_utils.Date_Time_Created_Mixin):  # TODO: calculate time remaining based on engagement (decide {just likes}, {likes & {likes of replies}} or {likes, {likes of replies} & replies}) & creator follower count
    """
        Base model that defines fields for all types of user generated content,
        as well as extra instance methods for retrieving commonly computed
        properties.

        This class is abstract so should not be instantiated or have a table
        made for it in the database (see
        https://docs.djangoproject.com/en/4.1/topics/db/models/#abstract-base-classes).
    """

    message = models.TextField("Message")
    creator: "User" = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Creator",
        related_name="created_%(class)s_set",
        null=False,
        blank=False
    )
    liked_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="liked_%(class)s_set",
        blank=True,
        help_text="The set of :model:`pulsifi.user` instances that have liked this content object instance."
    )
    """
        The set of :model:`pulsifi.user` instances that have liked this content
        object instance.
    """

    disliked_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="disliked_%(class)s_set",
        blank=True,
        help_text="The set of :model:`pulsifi.user` instances that have disliked this content object instance."
    )
    """
        The set of :model:`pulsifi.user` instances that have disliked this
        content object instance.
    """

    reply_set = GenericRelation(
        "Reply",
        content_type_field="_content_type",
        object_id_field="_object_id",
        verbose_name="Replies",
        help_text="The set of :model:`pulsifi.reply` objects for this content object instance."
    )
    """
        The set of :model:`pulsifi.reply` objects for this content object
        instance.
    """

    is_visible = models.BooleanField(
        "Is visible?",
        default=True,
        help_text="Boolean flag to determine whether this object should be accessible to the website. Use this flag instead of deleting objects."
    )
    """
        Boolean flag to determine whether this object should be accessible
        to the website. Use this flag instead of deleting objects.
    """

    @property
    @abstractmethod
    def original_pulse(self) -> "Pulse":
        """
            The single :model:`pulsifi.pulse` object instance that is the
            highest parent object in the tree of :model:`pulsifi.pulse` &
            :model:`pulsifi.reply` objects that this instance is within.
        """

        raise NotImplementedError

    @property
    @abstractmethod
    def full_depth_replies(self) -> set["Reply"]:
        """
            The set of all :model:`pulsifi.reply` objects that are within the
            tree of this instance's children/children's children etc.
        """

        raise NotImplementedError

    # noinspection PyMissingOrEmptyDocstring
    class Meta:
        abstract = True

    def __repr__(self) -> str:
        return f"<{self._meta.verbose_name}: {self.creator}, \"{self.message}\">"

    def __str__(self) -> str:
        """
            Returns the stringified version of this content's creator and the
            message within this content if it is still visible, otherwise
            returns the crossed out message within this content.
        """

        return f"{self.creator}, {self.string_when_visible(self.message[:settings.MESSAGE_DISPLAY_LENGTH])}"

    def get_absolute_url(self) -> str:
        """
            Returns the canonical URL for this object instance.

            Uses django's argument structure so cannot be changed (see
            https://docs.djangoproject.com/en/4.1/ref/models/instances/#django.db.models.Model.get_absolute_url).
        """

        return f"""{django_urls_utils.reverse("pulsifi:feed")}?{self._meta.model_name}={self.id}"""


class User(_Visible_Reportable_Mixin, AbstractUser):  # TODO: show verified tick or staff badge next to username
    """
        Model to define changes to existing fields/extra fields & processing
        for users, beyond that/those given by Django's base :model:`auth.user`
        model.
    """

    STAFF_GROUP_NAMES = {"Moderators", "Admins"}

    first_name = None  # make blank in save method
    last_name = None
    get_full_name = None
    get_short_name = None

    moderator_assigned_report_set: models.Manager
    """
        The set of :model:`pulsifi.report` objects that this user (if they are
        a moderator) has been assigned to moderate.
    """

    avatar_set: models.Manager
    """
        The set of :model:`avatar.avatar` image objects that this user has
        uploaded.
    """

    disliked_pulse_set: models.Manager
    """ The set of :model:`pulsifi.pulse` objects that this user has disliked. """

    disliked_reply_set: models.Manager
    """ The set of :model:`pulsifi.reply` objects that this user has disliked. """

    # noinspection SpellCheckingInspection
    emailaddress_set: models.Manager
    # noinspection SpellCheckingInspection
    """
        The set of :model:`account.emailaddress` objects that have been
        assigned to this user.
    """

    liked_pulse_set: models.Manager
    """ The set of :model:`pulsifi.pulse` objects that this user has liked. """

    liked_reply_set: models.Manager
    """ The set of :model:`pulsifi.reply` objects that this user has liked. """

    created_pulse_set: models.Manager
    """ The set of :model:`pulsifi.pulse` objects that this user has created. """

    created_reply_set: models.Manager
    """ The set of :model:`pulsifi.reply` objects that this user has created. """

    submitted_report_set: models.Manager
    """
        The set of :model:`pulsifi.report` objects that this user has
        submitted.
    """

    # noinspection SpellCheckingInspection
    socialaccount_set: models.Manager
    # noinspection SpellCheckingInspection
    """
        The set of :model:`socialaccount:socialaccount` objects that can be
        used to log in this user.
    """

    username = models.CharField(
        "Username",
        max_length=30,
        unique=True,
        validators=[
            RegexValidator(
                r"^[\w.-]+\Z",
                "Enter a valid username. This value may contain only letters, digits and ./_ characters."
            ),
            ReservedNameValidator(),
            ConfusableStringValidator()
        ],
        error_messages={
            "unique": "A user with that username already exists."
        },
        null=False,
        blank=False
    )
    email = models.EmailField(
        "Email Address",
        unique=True,
        validators=[
            HTML5EmailValidator(),
            FreeEmailValidator(),
            ConfusableEmailValidator(),
            PreexistingEmailTLDValidator(),
            ExampleEmailValidator()
        ],
        error_messages={
            "unique": f"That Email Address is already in use by another user."
        },
        null=False,
        blank=False
    )
    bio = models.TextField(
        "Bio",
        max_length=200,
        blank=True,
        help_text="Longer textfield containing an autobiographical description of this user."
    )
    """
        Longer textfield containing an autobiographical description of this
        user.
    """

    is_verified = models.BooleanField(
        "Is verified?",
        default=False,
        help_text="Boolean flag to indicate whether this user is a noteable person/organisation."
    )
    """
        Boolean flag to indicate whether this user is a noteable
        person/organisation.
    """

    following = models.ManyToManyField(
        "self",
        symmetrical=False,
        related_name="followers",
        through="Follow",
        through_fields=("follower", "followed"),
        blank=True,
        help_text="Set of other :model:`pulsifi.user` objects that this user is following."
    )
    """ Set of other :model:`pulsifi.user` objects that this user is following. """

    is_staff = models.BooleanField(
        "Is a staff member?",
        default=False,
        help_text="Boolean flag to indicate whether this user is a staff member, and thus can log into the admin site."
    )
    """
        Boolean flag to indicate whether this user is a staff member, and thus
        can log into the admin site.
    """

    is_superuser = models.BooleanField(
        "Is a superuser?",
        default=False,
        help_text="Boolean flag to provide a quick way to designate that this user has all permissions without explicitly assigning them."
    )
    """
        Boolean flag to provide a quick way to designate that this user has all
        permissions without explicitly assigning them.
    """

    is_active = models.BooleanField(
        "Is visible?",
        default=True,
        help_text="Boolean flag to determine whether this object should be accessible to the website. Use this flag instead of deleting objects."
    )
    """
        Boolean flag to determine whether this object should be accessible
        to the website. Use this flag instead of deleting objects.
    """

    date_joined = models.DateTimeField(
        "Date Joined",
        default=timezone.now,
        editable=False
    )
    last_login = models.DateTimeField(
        "Last Login",
        blank=True,
        null=True,
        editable=False
    )

    @property
    def is_visible(self) -> bool:
        """
            Shortcut variable for the is_active property, to provide a
            consistent way to access the visibility of all objects in pulsifi
            app.
        """

        return self.is_active

    @is_visible.setter
    def is_visible(self, value: bool):
        self.is_active = value

    class Meta:
        verbose_name = "User"

    def __str__(self) -> str:
        """
            Returns this user's username, if they are still visible; otherwise
            returns the crossed out username.
        """

        return self.string_when_visible(f"@{self.username}")

    def clean(self) -> None:
        """
            Performs extra model-wide validation after clean() has been called
            on every field by self.clean_fields().

            Uses django's argument structure so cannot be changed (see
            https://docs.djangoproject.com/en/4.1/ref/models/instances/#django.db.models.Model.clean).
        """

        if self.is_superuser:  # NOTE: is_staff should be True if is_superuser is True
            self.is_staff = self.is_superuser

        if self.username:  # NOTE: Only compare the username similarity if the value is valid for all other conditions
            restricted_admin_username_in_username = any(restricted_admin_username in self.username.lower() for restricted_admin_username in settings.RESTRICTED_ADMIN_USERNAMES)
            if (pulsifi_models_utils.get_restricted_admin_users_count(exclusion_id=self.id) >= settings.PULSIFI_ADMIN_COUNT or not self.is_staff) and restricted_admin_username_in_username:  # NOTE: The username can only contain a restricted_admin_username if the user is a staff member & the maximum admin count has not been reached
                raise ValidationError({"username": "That username is not allowed."}, code="invalid")

        username: str
        for username in get_user_model().objects.exclude(id=self.id).values_list("username", flat=True):  # NOTE: Check this username is not too similar to any other username (apart from this user's existing email)
            if thefuzz.token_sort_ratio(self.username, username) >= settings.USERNAME_SIMILARITY_PERCENTAGE:
                raise ValidationError({"username": "That username is too similar to a username belonging to an existing user."}, code="unique")

        if self.email.count("@") == 1:
            local: str
            seperator: str
            whole_domain: str
            local, seperator, whole_domain = self.email.rpartition("@")

            extracted_domain: TLD_ExtractResult = tldextract.extract(whole_domain)

            local = local.replace(".", "")  # NOTE: Format the local part of the email address to remove dots

            if "+" in local:
                local = local.partition("+")[0]  # NOTE: Format the local part of the email address to remove any part after a plus symbol

            if extracted_domain.domain == "googlemail":  # NOTE: Rename alias email domains (E.g. googlemail == gmail)
                extracted_domain = TLD_ExtractResult(subdomain=extracted_domain.subdomain, domain="gmail", suffix=extracted_domain.suffix)

            else:
                restricted_admin_username_in_username = any(restricted_admin_username in extracted_domain.domain for restricted_admin_username in settings.RESTRICTED_ADMIN_USERNAMES)
                if (pulsifi_models_utils.get_restricted_admin_users_count(exclusion_id=self.id) >= settings.PULSIFI_ADMIN_COUNT or not self.is_staff) and restricted_admin_username_in_username:  # NOTE: The email domain can only contain a restricted_admin_username if the user is a staff member & the maximum admin count has not been reached
                    raise ValidationError({"email": f"That Email Address cannot be used."}, code="invalid")

            self.email = seperator.join((local, extracted_domain.fqdn))  # NOTE: Replace the cleaned email address

        if allauth_core_utils.email_address_exists(self.email, self):
            raise ValidationError({"email": f"That Email Address is already in use by another user."}, code="unique")

        if self.is_verified and not allauth_utils.has_verified_email(self):
            raise ValidationError({"is_verified": "User cannot become verified without at least one verified email address."})

        super().clean()

    def save(self, *args, **kwargs) -> None:
        # noinspection SpellCheckingInspection
        """
            Saves the current instance to the database then performs extra
            cleanup of relations (E.g. removing self from followers or ensuring
            an :model:`account.emailaddress` object exists for the user's
            primary email).

            Uses django's argument structure so cannot be changed (see
            https://docs.djangoproject.com/en/4.1/ref/models/instances/#django.db.models.Model.save).
        """

        super().save(*args, **kwargs)

        self.ensure_superuser_in_admin_group()
        self.ensure_user_in_any_staff_group_is_staff()

        # TODO: run sync_user_email_addresses as cron job instead
        # TODO: run sync staff members with being verified (as long as have one verified email)
        # TODO: run create Admins & Moderators groups as cron job

    def ensure_user_in_any_staff_group_is_staff(self) -> None:
        """
            Ensures that if the current user instance has been added to any of
            the staff :model:`auth.group` objects, then they should have the
            is_staff property set to True.
        """

        if not self.is_staff and self.STAFF_GROUP_NAMES & set(self.groups.all().values_list("name", flat=True)):
            self.update(is_staff=True)

    def ensure_superuser_in_admin_group(self) -> None:
        """
            Ensures that if the current user instance has the is_superuser
            property set to True then they should be added to the Admins
            :model:`auth.group`.
        """

        if self.is_superuser and "Admins" not in self.groups.all().values_list("name", flat=True):
            try:
                self.groups.add(Group.objects.get(name="Admins"))
            except Group.DoesNotExist:
                logging.error(f"User: {self} is superuser but could not be added to \"Admins\" group because it does not exist.")

    def get_absolute_url(self) -> str:
        """
            Returns the canonical URL for this object instance.

            Uses django's argument structure so cannot be changed (see
            https://docs.djangoproject.com/en/4.1/ref/models/instances/#django.db.models.Model.get_absolute_url).
        """

        return django_urls_utils.reverse("pulsifi:specific_account", kwargs={"username": self.username})

    def get_feed_pulses(self) -> models.QuerySet["Pulse"]:
        """
            Returns the set of :model:`pulsifi.pulse` objects that should be
            displayed on the :view:`pulsifi.views.Feed_View` for this user.
        """  # ISSUE: Admindocs does not generate link to view correctly

        return Pulse.objects.filter(
            creator__in=self.following.exclude(is_active=False)
        ).order_by("_date_time_created")

    def add_following(self, *objs, bulk=True) -> None:
        """
            Adds the provided User objects to the set of other
            :model:`pulsifi.user` objects that this user is following.
        """

        self.following.add(*objs, bulk, through_defaults=dict())

    def add_followers(self, *objs, bulk=True) -> None:
        """
            Adds the provided User objects to the set of other
            :model:`pulsifi.user` objects that are following this user.
        """

        self.followers.add(*objs, bulk, through_defaults=dict())

    @classmethod
    def get_proxy_field_names(cls) -> set[str]:
        """
            Returns a set of names of extra properties of this model that can
            be saved to the database, even though those fields don't actually
            exist. They are just proxy fields.
        """

        extra_property_fields: set[str] = super().get_proxy_field_names()

        extra_property_fields.add("is_visible")

        return extra_property_fields


class Follow(pulsifi_models_utils.Custom_Base_Model):
    """
        Intermediate through model that represents the link between the
        many-to-many relationship of one user following another.
    """

    follower = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="followers_set"
    )
    followed = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="following_set"
    )

    def __repr__(self) -> str:
        return f"<{self._meta.verbose_name}: {self.follower}, {self.followed}>"

    def __str__(self) -> str:
        """
            Returns the stringified version of this :model:`pulsifi.follow`
            object with the follower and followed.
        """

        return f"{self.id}: {self.follower} -> {self.followed}"

    class Meta:
        verbose_name = "Following Link"
        constraints = [
            models.UniqueConstraint(
                fields=["follower", "followed"],
                name="follow_once"
            ),
            models.CheckConstraint(
                check=~models.Q(follower=models.F("followed")),
                name="not_follow_self"
            )
        ]


class Pulse(User_Generated_Content_Model):
    """
        Model to define pulses (posts) that are made by users and are visible
        on the main website.
    """

    # noinspection PyMissingOrEmptyDocstring
    class Meta:
        verbose_name = "Pulse"

    def save(self, *args, **kwargs) -> None:
        """
            Saves the current instance to the database, after making any
            :model:`pulsifi.reply` objects, of this instance, the matching
            visibility, to this pulse's visibility.

            Uses django's argument structure so cannot be changed (see
            https://docs.djangoproject.com/en/4.1/ref/models/instances/#django.db.models.Model.save).
        """

        self.full_clean()

        try:
            old_is_visible: bool = Pulse.objects.get(id=self.id).is_visible
        except Pulse.DoesNotExist:
            pass
        else:
            if not self.is_visible and old_is_visible:
                for reply in self.full_depth_replies:
                    reply.update(base_save=True, is_visible=False)

            elif self.is_visible and not old_visibility:
                for reply in self.full_depth_replies:
                    reply.update(base_save=True, is_visible=True)

        super().save(*args, **kwargs)

    @property
    def original_pulse(self) -> "Pulse":
        """
            Returns the :model:`pulsifi.pulse` object that is the highest
            parent object in the tree of :model:`pulsifi.pulse` &
            :model:`pulsifi.reply` objects that this instance is within.

            The highest User_Generated_Content object within the current
            replies-tree is always a :model:`pulsifi.pulse` object.
        """

        return self

    @property
    def full_depth_replies(self) -> set["Reply"]:
        """
            The set of all :model:`pulsifi.reply` objects that are within the
            tree of this instance's children/children's children etc.
        """

        return {reply for reply in Reply.objects.all() if reply.original_pulse is self}


class Reply(User_Generated_Content_Model):
    """
        Model to define replies (posts assigned to a parent
        :model:`pulsifi.pulse` object) that are made by a :model:`pulsifi.user`
        and visible on the main website (underneath the corresponding
        :model:`pulsifi.pulse`).
    """

    _content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to={"app_label": "pulsifi", "model__in": {"pulse", "reply"}},
        verbose_name="Replied Content Type",
        help_text="Link to the content type of the replied_content instance (either :model:`pulsifi.pulse` or :model:`pulsifi.reply`).",
        null=False,
        blank=False
    )
    """
        Link to the content type of the replied_content instance (either
        :model:`pulsifi.pulse` or :model:`pulsifi.reply`).
    """

    _object_id = models.PositiveIntegerField(
        verbose_name="Replied Content ID",
        help_text="ID number of the specific instance of the replied_content instance."
    )
    """ ID number of the specific instance of the replied_content instance. """

    replied_content = GenericForeignKey(ct_field="_content_type", fk_field="_object_id")
    """
        Shortcut variable for the instance of replied_content, determined from
        the _content_type and _object_id.
    """

    @property
    def original_pulse(self) -> Pulse:
        """
            The single :model:`pulsifi.pulse` object instance that is the
            highest parent object in the tree of :model:`pulsifi.pulse` &
            :model:`pulsifi.reply` objects that this instance is within.
        """

        return self.replied_content.original_pulse

    @property
    def full_depth_replies(self) -> set["Reply"]:
        """
            The set of all :model:`pulsifi.reply` objects that are within the
            tree of this instance's children/children's children etc.
        """

        replies = set()
        reply: "Reply"
        for reply in self.reply_set.all():
            replies.add(reply)  # NOTE: Add the current level :model:`pulsifi.reply` objects to the set
            replies.update(reply.full_depth_replies)  # NOTE: Add the child :model:`pulsifi.reply` objects recursively to the set
        return replies

    # noinspection PyMissingOrEmptyDocstring
    class Meta:
        verbose_name = "Reply"
        verbose_name_plural = "Replies"
        indexes = [
            models.Index(fields=["_content_type", "_object_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.creator}, {self.string_when_visible(self.message[:settings.MESSAGE_DISPLAY_LENGTH])} (For object - {self._content_type.name} | {self.replied_content})"[:100]

    def clean(self) -> None:
        """
            Performs extra model-wide validation after clean() has been called
            on every field by self.clean_fields().

            Uses django's argument structure so cannot be changed (see
            https://docs.djangoproject.com/en/4.1/ref/models/instances/#django.db.models.Model.clean).
        """

        if self._content_type and self._object_id is not None:  # HACK: Don't clean the generic content relation if the values are not set (prevents error in AdminInlines where dummy objects are cleaned without values in _content_type and _object_id)
            if self._content_type.model not in {"pulse", "reply"}:
                raise ValidationError({"_content_type": f"The Content Type: {self._content_type} is not one of the allowed options: Pulse, Reply."}, code="invalid")

            if self._content_type.model == "reply" and self._object_id == self.id:
                raise ValidationError({"_object_id": "Replied content cannot be this Reply."}, code="invalid")

            if (self._content_type.model == "pulse" and not Pulse.objects.filter(id=self._object_id).exists()) or (self._content_type.model == "reply" and not Reply.objects.filter(id=self._object_id).exists()):
                raise ValidationError("Replied content must be valid object.")

        else:
            logging.warning(f"Replied object of {repr(self)} could not be correctly verified because _content_type and _object_id fields were not set, when cleaning. It is likely that this happened within an AdminInline, so it can be assumed that the input data is valid anyway.")

        super().clean()

    def save(self, *args, **kwargs) -> None:
        """
            Saves the current instance to the database, after ensuring the
            current instance is not visible if the original_pulse is not
            visible.

            Uses django's argument structure so cannot be changed (see
            https://docs.djangoproject.com/en/4.1/ref/models/instances/#django.db.models.Model.save).
        """

        self.full_clean()

        if self.original_pulse:  # HACK: Don't try to retrieve the original_pulse for visibility updates (prevents error in AdminInlines where dummy objects are created without values in _content_type and _object_id)
            if not self.original_pulse.is_visible:
                self.is_visible = False
        else:
            logging.warning(f"Visibility of original_pulse could not be correctly retrieved because _content_type and _object_id fields were not set, when updating reply visibility to match original_pulse's visibility. It is likely that this happened within an AdminInline.")

        self.base_save(clean=False, *args, **kwargs)

    def get_latest_reply_of_same_original_pulse(self) -> "Reply":
        """
            Returns the most recently created :model:`pulsifi.reply` object by
            this :model:`pulsifi.reply` object's creator, to the same
            original_pulse as this :model:`pulsifi.reply` object's
            original_pulse.
        """

        for reply in Reply.objects.exclude(id=self.id).filter(creator=self.creator).order_by("-_date_time_created"):
            if reply.original_pulse == self.original_pulse:
                return reply
        else:
            raise Reply.DoesNotExist("No other Replies from this creator exist, to this Reply's original Pulse")


class Report(pulsifi_models_utils.Custom_Base_Model, pulsifi_models_utils.Date_Time_Created_Mixin):
    """
        Model to define reports, which flags inappropriate content/users to
        moderators.
    """

    REPORTABLE_CONTENT_TYPE_NAMES = {"user", "pulse", "reply"}

    class Categories(models.TextChoices):
        """ Enum of category code & display values of each category. """

        SPAM = "SPM", "Spam"
        SEXUAL = "SEX", "Nudity or sexual activity"
        HATE = "HAT", "Hate speech or symbols"
        VIOLENCE = "VIO", "Violence or dangerous organisations"
        ILLEGAL_GOODS = "ILG", "Sale of illegal or regulated goods"
        BULLYING = "BUL", "Bullying or harassment"
        INTELLECTUAL_PROPERTY = "INP", "Intellectual property violation or impersonation"
        SELF_INJURY = "INJ", "Suicide or self-injury"
        SCAM = "SCM", "Scam or fraud"
        FALSE_INFO = "FLS", "False or misleading information"

    class Statuses(models.TextChoices):
        """ Enum of status code & display values of each status. """

        IN_PROGRESS = "PR", "In Progress"
        REJECTED = "RE", "Rejected"
        COMPLETED = "CM", "Completed"

    _content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to={
            "app_label": "pulsifi",
            "model__in": REPORTABLE_CONTENT_TYPE_NAMES
        },
        verbose_name="Reported Object Type",
        help_text="Link to the content type of the reported_object instance (either :model:`pulsifi.user`, :model:`pulsifi.pulse` or :model:`pulsifi.reply`).",
        null=False,
        blank=False
    )
    """
        Link to the content type of the reported_object instance (either
        :model:`pulsifi.user`, :model:`pulsifi.pulse` or
        :model:`pulsifi.reply`).
    """

    _object_id = models.PositiveIntegerField(
        verbose_name="Reported Object ID",
        help_text="ID number of the specific instance of the reported_object instance."
    )
    """ ID number of the specific instance of the reported_object instance. """

    reported_object = GenericForeignKey(ct_field="_content_type", fk_field="_object_id")
    """
        Shortcut variable for the instance of reported_object, determined from
        the _content_type and _object_id.
    """

    reporter: User = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Reporter",
        related_name="submitted_report_set",
        help_text="Link to the :model:`pulsifi.user` object instance that created this report.",
        null=False,
        blank=False
    )
    """
        Link to the :model:`pulsifi.user` object instance that created this
        report.
    """

    assigned_moderator: User = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Assigned Moderator",
        related_name="moderator_assigned_report_set",
        limit_choices_to={"groups__name": "Moderators", "is_active": True},
        help_text="Link to the :model:`pulsifi.user` object instance (from the set of moderators) that has been assigned to moderate this report.",
        null=False,
        blank=True
    )
    """
        Link to the :model:`pulsifi.user` object instance (from the set of
        moderators) that has been assigned to moderate this report.
    """

    reason = models.TextField(
        "Reason",
        help_text="Longer textfield containing an detailed description of the reason for this report's existence."
    )
    """
        Longer textfield containing an detailed description of the reason for
        this report's existence.
    """

    category = models.CharField(
        "Category",
        max_length=3,
        choices=Categories.choices,
        help_text="The category code that gives an overview as to the reason for the report."
    )
    """
        The category code that gives an overview as to the reason for the
        report.
    """

    status = models.CharField(
        "Status",
        max_length=2,
        choices=Statuses.choices,
        default=Statuses.IN_PROGRESS,
        help_text="The status code that outlines the current position within the moderation cycle that this report is within."
    )
    """
        The status code that outlines the current position within the
        moderation cycle that this report is within.
    """

    # noinspection PyMissingOrEmptyDocstring
    class Meta:
        verbose_name = "Report"
        indexes = [
            models.Index(fields=["_content_type", "_object_id"]),
        ]

    def __repr__(self) -> str:
        return f"<{self._meta.verbose_name}: {self.reporter}, {self.category}, {self.get_status_display()} (Assigned Moderator - {self.assigned_moderator})>"

    def __str__(self) -> str:
        return f"{self.reporter}, {self.category}, {self.get_status_display()} (For object - {self._content_type.name} | {self.reported_object})(Assigned Moderator - {self.assigned_moderator})"

    def clean(self) -> None:
        """
            Performs extra model-wide validation after clean() has been called
            on every field by self.clean_fields().

            Uses django's argument structure so cannot be changed (see
            https://docs.djangoproject.com/en/4.1/ref/models/instances/#django.db.models.Model.clean).
        """

        if self._content_type and self._object_id is not None:  # HACK: Don't clean the generic content relation if the values are not set (prevents error in AdminInlines where dummy objects are cleaned without values in _content_type and _object_id)
            if self._content_type.model not in self.REPORTABLE_CONTENT_TYPE_NAMES:
                raise ValidationError({"_content_type": f"The Content Type: {self._content_type} is not one of the allowed options: User, Pulse, Reply."}, code="invalid")

            if (self._content_type.model == "user" and not get_user_model().objects.filter(id=self._object_id).exists()) or (self._content_type.model == "pulse" and not Pulse.objects.filter(id=self._object_id).exists()) or (self._content_type.model == "reply" and not Reply.objects.filter(id=self._object_id).exists()):  # TODO: Check if this validation is needed or just inbuilt
                raise ValidationError("Reported object must be valid object.")

            if self._content_type.model in {"pulse", "reply"}:
                if self.reported_object.creator.is_superuser or self.reported_object.creator.groups.filter(name="Admins").exists():
                    raise ValidationError({"_object_id": "This reported object refers to a Pulse or Reply created by an Admin. These Pulses & Replies cannot be reported."}, code="invalid")

                if self.reported_object.creator == self.reporter:
                    raise ValidationError({"_object_id": "You cannot report your own content. Please choose a different object to report."}, code="invalid")

            if self._content_type.model == "user" and (self.reported_object.is_superuser or self.reported_object.groups.filter(name="Admins").exists()):
                raise ValidationError({"_object_id": "This reported object refers to an admin. Admins cannot be reported."}, code="invalid")

            if self.reported_object == self.reporter:
                raise ValidationError({"_object_id": f"You cannot report yourself. Please choose a different object to report."}, code="invalid")

        else:
            logging.warning(f"Reported object of {repr(self)} could not be correctly verified because _content_type and _object_id fields were not set, when cleaning. It is likely that this happened within an AdminInline, so it can be assumed that the input data is valid anyway.")

        moderator_qs: models.QuerySet[User] = self.get_moderator_qs()

        if moderator_qs.count() == 1 and moderator_qs.first() == self.reported_object:
            raise ValidationError({"_object_id": "This reported object refers to the only moderator available to be assigned to this report. Therefore, this moderator cannot be reported."}, code="invalid")

        elif moderator_qs.count() == 1 and moderator_qs.first() == self.reporter:
            raise ValidationError({"reporter": "This user cannot be the reporter because they are the only moderator available to be assigned to this report."}, code="invalid")

        elif moderator_qs.count() == 1 and self._content_type.model in {"pulse", "reply"} and moderator_qs.first() == self.reported_object.creator:
            raise ValidationError({"_object_id": "This content cannot be reported because it was created by the only moderator available to be assigned to this report."}, code="invalid")

        elif self.assigned_moderator_id is None:
            self.assigned_moderator_id = random.choice(moderator_qs.values_list("id", flat=True))

        super().clean()

    @classmethod
    def get_moderator_qs(cls) -> models.QuerySet[User]:
        """
            Returns the set of moderator :model:`pulsifi.user` objects that can
            be picked to be the assigned_assigned moderator to any given
            Report.
        """

        # noinspection PyProtectedMember
        moderator_qs: models.QuerySet[User] = get_user_model().objects.filter(**cls._meta.get_field("assigned_moderator")._limit_choices_to)

        if not moderator_qs.exists():
            raise get_user_model().DoesNotExist("Random moderator cannot be chosen, because none exist.")

        return moderator_qs
